import os
import subprocess

CARGO_TOML_PATH = "/tmp/lez/examples/program_deployment/Cargo.toml"
RUNNER_RS_PATH = "/tmp/lez/examples/program_deployment/src/bin/run_osm_registry.rs"

RUNNER_CODE = r'''use common::transaction::LeeTransaction;
use lee::{
    AccountId, ProgramShardSelector, PublicTransaction,
    program::Program,
    public_transaction::{Message, WitnessSet},
};
use borsh::{BorshDeserialize, BorshSerialize};
use sequencer_service_rpc::RpcClient as _;
use wallet::WalletCore;

#[derive(BorshSerialize, BorshDeserialize, Clone, Copy, Debug, PartialEq, Eq)]
pub enum RegionLevel {
    Country,
    Subregion,
}

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq, Eq)]
pub struct RegisterRegionArgs {
    pub region: String,
    pub parent: Option<String>,
    pub level: RegionLevel,
    pub cid: String,
    pub source_url: String,
    pub checksum: String,
    pub version: String,
    pub hosted: bool,
    pub timestamp: u64,
}

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq, Eq)]
pub enum RegistryInstruction {
    Initialize,
    RegisterRegion(RegisterRegionArgs),
    BatchRegister(Vec<RegisterRegionArgs>),
}

#[tokio::main]
async fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 4 {
        eprintln!(
            "Usage: run_osm_registry <program_path> <account_id> <initialize|register> [args...]"
        );
        std::process::exit(1);
    }

    let program_path = &args[1];
    let account_id: AccountId = args[2].parse().expect("Invalid account ID");
    let action = &args[3];

    // Initialize wallet
    let wallet_core = WalletCore::from_env().await.unwrap();

    // Load the program
    let bytecode: Vec<u8> = std::fs::read(program_path).unwrap();
    let program = Program::new(bytecode.into()).unwrap();
    let program_id = program.id();
    println!("Program ID: {}", program_id);

    // Build instruction
    let instruction: RegistryInstruction = match action.as_str() {
        "initialize" => {
            println!("Building Initialize instruction...");
            RegistryInstruction::Initialize
        }
        "register" => {
            if args.len() < 10 {
                eprintln!("Usage for register: run_osm_registry <prog> <account> register <region> <cid> <checksum> <source_url> <version> <timestamp>");
                std::process::exit(1);
            }
            let region = args[4].clone();
            let cid = args[5].clone();
            let checksum = args[6].clone();
            let source_url = args[7].clone();
            let version = args[8].clone();
            let timestamp: u64 = args[9].parse().expect("Invalid timestamp");

            let reg_args = RegisterRegionArgs {
                region,
                parent: None,
                level: RegionLevel::Country,
                cid,
                source_url,
                checksum,
                version,
                hosted: true,
                timestamp,
            };
            println!("Building RegisterRegion instruction for region: {}", reg_args.region);
            RegistryInstruction::RegisterRegion(reg_args)
        }
        other => panic!("Unknown action: {}", other),
    };

    let instruction_bytes = borsh::to_vec(&instruction).expect("Failed to serialize instruction");

    // Load signing keys if available
    let signing_key_opt = wallet_core
        .storage()
        .key_chain()
        .pub_account_signing_key(account_id);

    // Query current nonce
    let nonces = wallet_core
        .get_accounts_nonces(&[account_id])
        .await
        .expect("Failed to get account nonces from node");

    let message = Message::try_new(
        program_id.into(),
        vec![ProgramShardSelector::new(account_id, program_id.into())],
        nonces,
        instruction_bytes,
    )
    .expect("Failed to create message");

    let witness_set = if let Ok(key) = signing_key_opt {
        WitnessSet::for_message(&message, &[&key])
    } else {
        WitnessSet::for_message(&message, &[])
    };

    let tx = PublicTransaction::new(message, witness_set);

    println!("Submitting transaction to LEZ sequencer...");
    let response = wallet_core
        .helm_owned()
        .send_transaction(LeeTransaction::Public(tx))
        .await
        .expect("Failed to send transaction");

    println!("Transaction confirmed! Response: {:?}", response);
}
'''

def main():
    # Update Cargo.toml
    cmd = [
        "wsl", "-u", "root", "bash", "-c",
        f"""
        if ! grep -q 'borsh.workspace' {CARGO_TOML_PATH}; then
            echo 'borsh.workspace = true' >> {CARGO_TOML_PATH}
        fi
        cat << 'EOF' > {RUNNER_RS_PATH}
{RUNNER_CODE}
EOF
        echo "Runner created at {RUNNER_RS_PATH}"
        """
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    print(res.stderr)

if __name__ == "__main__":
    main()
