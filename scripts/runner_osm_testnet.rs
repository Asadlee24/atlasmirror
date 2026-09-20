#![allow(unused_imports)]
use borsh::{BorshDeserialize, BorshSerialize};
use serde::{Deserialize, Serialize};
use lee::{AccountId, program::Program};
use wallet::WalletCore;

#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq)]
pub enum RegionLevel {
    Country,
    Subregion,
}

#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct RegionRecord {
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

#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, Default, PartialEq, Eq)]
pub struct RegistryState {
    pub total_regions: u64,
    pub last_updated: u64,
    pub records: Vec<RegionRecord>,
}

#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
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

#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub enum RegistryInstruction {
    Initialize,
    RegisterRegion(RegisterRegionArgs),
}

#[tokio::main]
async fn main() {
    let wallet_core = WalletCore::from_env().await.unwrap();

    let args: Vec<String> = std::env::args().collect();
    if args.len() < 4 {
        eprintln!(
            "Usage: run_osm_registry PROGRAM_PATH ACCOUNT_ID ACTION [ARGS...]"
        );
        std::process::exit(1);
    }

    let program_path = &args[1];
    let account_id: AccountId = args[2].parse().expect("Invalid account ID");
    let action = &args[3];

    let bytecode: Vec<u8> = std::fs::read(program_path).expect("Failed to read program binary");
    let program = Program::new(bytecode.into()).expect("Failed to parse program");
    println!("Program ID: {:?}", program.id());

    if action == "query" {
        println!("Querying account state for {}", account_id);
        let account = wallet_core
            .get_account(wallet::account::AccountIdWithPrivacy::Public(account_id))
            .await
            .expect("Failed to get account");
        println!("Account view: {:?}", account);
        let raw_data = account.data.as_ref();
        println!("Raw data len: {}", raw_data.len());
        if !raw_data.is_empty() {
            let state: RegistryState =
                borsh::from_slice(raw_data).expect("Failed to decode RegistryState");
            println!("Registry State: total_regions={}, last_updated={}", state.total_regions, state.last_updated);
            for r in state.records {
                println!(
                    "REGION_RECORD: region={}, parent={:?}, level={:?}, cid={}, source_url={}, checksum={}, version={}, hosted={}, timestamp={}",
                    r.region, r.parent, r.level, r.cid, r.source_url, r.checksum, r.version, r.hosted, r.timestamp
                );
            }
        } else {
            println!("Account data is empty.");
        }
        return;
    }

    let instruction = match action.as_str() {
        "init" => {
            println!("Building Initialize instruction...");
            RegistryInstruction::Initialize
        }
        "register" => {
            let region = args.get(4).cloned().unwrap_or_else(|| "china/henan".to_string());
            let cid = args.get(5).cloned().unwrap_or_else(|| "zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny".to_string());
            let checksum = args.get(6).cloned().unwrap_or_else(|| "0055ebfc7f14585c56d53a88062d5814".to_string());
            let source_url = args.get(7).cloned().unwrap_or_else(|| "https://download.geofabrik.de/asia/china/henan-latest.osm.pbf".to_string());
            let version = args.get(8).cloned().unwrap_or_else(|| "2026-09-20".to_string());
            let timestamp: u64 = args.get(9).and_then(|s| s.parse().ok()).unwrap_or(1789905600);

            let (parent, level) = if region.contains('/') {
                let parts: Vec<&str> = region.split('/').collect();
                (Some(parts[0].to_string()), RegionLevel::Subregion)
            } else {
                (None, RegionLevel::Country)
            };

            let reg_args = RegisterRegionArgs {
                region,
                parent,
                level,
                cid,
                source_url,
                checksum,
                version,
                hosted: true,
                timestamp,
            };
            println!("Building RegisterRegion instruction: {:?}", reg_args);
            RegistryInstruction::RegisterRegion(reg_args)
        }
        other => panic!("Unknown action: {}", other),
    };

    let instruction_data = Program::serialize_instruction(instruction).expect("Failed to serialize instruction");

    let tx_hash = wallet_core
        .send_pub_tx(
            vec![wallet::AccountIdentity::Public(account_id)],
            instruction_data,
            program.id(),
        )
        .await
        .expect("Failed to send transaction");

    println!("Transaction submitted! Hash: {:?}", tx_hash);

    println!("Polling for transaction finalization...");
    let final_res = wallet_core
        .poll_and_finalize_public_transaction(tx_hash)
        .await
        .expect("Failed to finalize transaction");
    println!("Transaction finalized successfully! Result: {:?}", final_res);
}
