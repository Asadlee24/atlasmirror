use borsh::{BorshDeserialize, BorshSerialize};
use osm_registry_core::{
    BatchRegisterArgs, GlobalRegistryState, RegionRecord, RegisterRegionArgs, RegistryError,
};

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug)]
pub enum RegistryInstruction {
    Initialize,
    RegisterRegion(RegisterRegionArgs),
    BatchRegister(BatchRegisterArgs),
}

/// Entry point for the SPEL OSM Registry on the Logos Execution Zone.
pub fn process_instruction(
    instruction_data: &[u8],
    state: &mut GlobalRegistryState,
    records: &mut Vec<RegionRecord>,
) -> Result<(), RegistryError> {
    let instruction = RegistryInstruction::try_from_slice(instruction_data)
        .map_err(|_| RegistryError::InvalidRegionPath)?;

    match instruction {
        RegistryInstruction::Initialize => {
            state.total_regions = 0;
            state.last_updated = 0;
            Ok(())
        }
        RegistryInstruction::RegisterRegion(args) => {
            args.validate()?;
            let ts = args.timestamp;

            // Check if region already exists for timestamp monotonicity
            if let Some(existing) = records.iter_mut().find(|r| r.region == args.region) {
                if ts <= existing.timestamp {
                    return Err(RegistryError::TimestampRegression {
                        existing_ts: existing.timestamp,
                        new_ts: ts,
                    });
                }
                *existing = args.into_record();
            } else {
                records.push(args.into_record());
                state.total_regions += 1;
            }

            state.last_updated = ts;
            Ok(())
        }
        RegistryInstruction::BatchRegister(batch) => {
            batch.validate()?;

            for args in batch.records {
                let ts = args.timestamp;
                if let Some(existing) = records.iter_mut().find(|r| r.region == args.region) {
                    if ts <= existing.timestamp {
                        return Err(RegistryError::TimestampRegression {
                            existing_ts: existing.timestamp,
                            new_ts: ts,
                        });
                    }
                    *existing = args.into_record();
                } else {
                    records.push(args.into_record());
                    state.total_regions += 1;
                }
                if ts > state.last_updated {
                    state.last_updated = ts;
                }
            }

            Ok(())
        }
    }
}
