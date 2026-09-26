use borsh::{BorshDeserialize, BorshSerialize};
use lee_core::program::{AccountPostState, Claim, ProgramInput, ProgramOutput, read_lee_inputs};
use osm_registry_core::{
    BatchRegisterArgs, RegionRecord, RegisterRegionArgs, RegistryError, RegistryInstruction,
    RegistryState,
};

fn process_instruction(
    instruction: RegistryInstruction,
    state: &mut RegistryState,
) -> Result<(), RegistryError> {
    match instruction {
        RegistryInstruction::Initialize => {
            state.total_regions = 0;
            state.last_updated = 0;
            state.records.clear();
            Ok(())
        }
        RegistryInstruction::RegisterRegion(args) => {
            args.validate()?;
            let ts = args.timestamp;

            if let Some(existing) = state.records.iter_mut().find(|r| r.region == args.region) {
                if ts <= existing.timestamp {
                    return Err(RegistryError::TimestampRegression {
                        existing_ts: existing.timestamp,
                        new_ts: ts,
                    });
                }
                *existing = args.into_record();
            } else {
                state.records.push(args.into_record());
                state.total_regions += 1;
            }

            // Ensure deterministic timestamp ordering in the on-chain shard state
            state.records.sort_by(|a, b| {
                a.timestamp
                    .cmp(&b.timestamp)
                    .then_with(|| a.region.cmp(&b.region))
            });

            state.last_updated = ts;
            Ok(())
        }
        RegistryInstruction::BatchRegister(batch) => {
            batch.validate()?;

            for args in batch.records {
                let ts = args.timestamp;
                if let Some(existing) = state.records.iter_mut().find(|r| r.region == args.region) {
                    if ts <= existing.timestamp {
                        return Err(RegistryError::TimestampRegression {
                            existing_ts: existing.timestamp,
                            new_ts: ts,
                        });
                    }
                    *existing = args.into_record();
                } else {
                    state.records.push(args.into_record());
                    state.total_regions += 1;
                }
                if ts > state.last_updated {
                    state.last_updated = ts;
                }
            }

            // Ensure deterministic timestamp ordering across all batch insertions
            state.records.sort_by(|a, b| {
                a.timestamp
                    .cmp(&b.timestamp)
                    .then_with(|| a.region.cmp(&b.region))
            });

            Ok(())
        }
    }
}

fn main() {
    let (
        ProgramInput {
            self_program_id,
            caller_program_id,
            pre_states,
            instruction,
        },
        instruction_words,
    ) = read_lee_inputs::<RegistryInstruction>();

    let Ok([pre]) = <[_; 1]>::try_from(pre_states) else {
        panic!("Input pre states should consist of a single account");
    };

    let account_pre = &pre.account;
    let mut account_post = account_pre.clone();

    let raw_data: &[u8] = account_pre.data.as_ref();
    let mut state: RegistryState = if raw_data.is_empty() {
        RegistryState::default()
    } else {
        borsh::from_slice(raw_data).expect("failed to decode RegistryState")
    };

    process_instruction(instruction, &mut state).expect("failed to process instruction");

    let new_bytes = borsh::to_vec(&state).expect("failed to serialize state");
    account_post.data = new_bytes
        .try_into()
        .expect("ShardData should fit within allowed limits");

    ProgramOutput::new(
        self_program_id,
        caller_program_id,
        instruction_words,
        vec![pre],
        vec![AccountPostState::new_claimed_if_default(
            account_post,
            Claim::Authorized,
        )],
    )
    .write();
}
