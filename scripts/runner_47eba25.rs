#![allow(unused_imports, clippy::all)]
use borsh::{BorshDeserialize, BorshSerialize};
use lee::{AccountId, program::Program};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use wallet::{AccountIdentity, WalletCore};

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
pub struct BatchRegisterArgs {
    pub records: Vec<RegisterRegionArgs>,
}

#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub enum RegistryInstruction {
    Initialize,
    RegisterRegion(RegisterRegionArgs),
    BatchRegister(BatchRegisterArgs),
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let wallet_core = WalletCore::from_env()
        .await
        .expect("Failed to initialize WalletCore from environment");

    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("Usage: run_osm_registry ACCOUNT_ID ACTION [ARGS...]");
        std::process::exit(1);
    }

    let account_id: AccountId = args[1].parse().expect("Invalid account ID");
    let action = &args[2];

    let program_id: [u32; 8] = [
        1108401340, 224902513, 3719279011, 2256696779, 2279479750, 2288278838, 1677050569, 1334542228,
    ];

    let instruction = match action.as_str() {
        "init" => RegistryInstruction::Initialize,
        "register" => {
            let region = args.get(3).cloned().unwrap();
            let cid = args.get(4).cloned().unwrap();
            let checksum = args.get(5).cloned().unwrap();
            let source_url = args.get(6).cloned().unwrap();
            let version = args.get(7).cloned().unwrap();
            let timestamp: u64 = args.get(8).and_then(|s| s.parse().ok()).unwrap();

            let (parent, level) = {
                let p = region.to_lowercase();
                if p.starts_with("us/") || p.starts_with("india/") || p.starts_with("china/") || p.starts_with("russia/") {
                    let parts: Vec<&str> = p.split('/').collect();
                    (Some(parts[0].to_string()), RegionLevel::Subregion)
                } else {
                    (None, RegionLevel::Country)
                }
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
            println!("Building RegisterRegion: {:?}", reg_args);
            RegistryInstruction::RegisterRegion(reg_args)
        }
        "batch_register" => {
            let json_path = args.get(3).expect("Missing batch json file path");
            let json_str = std::fs::read_to_string(json_path).expect("Failed to read batch json file");
            let records: Vec<RegisterRegionArgs> = serde_json::from_str(&json_str).expect("Failed to parse batch records JSON");
            println!("Building BatchRegister instruction with {} records...", records.len());
            RegistryInstruction::BatchRegister(BatchRegisterArgs { records })
        }
        other => panic!("Unknown action: {}", other),
    };

    let instruction_data = Program::serialize_instruction(instruction)
        .expect("Failed to serialize instruction");

    println!("Submitting transaction for account {} (program {:?})...", account_id, program_id);
    let accounts = vec![AccountIdentity::Public(account_id)];
    let tx_result = wallet_core
        .send_pub_tx(accounts, instruction_data, program_id)
        .await;

    match tx_result {
        Ok(tx_hash) => {
            println!("Transaction submitted! Hash: {:?}", tx_hash);
            println!("Waiting for inclusion...");
            tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
            println!("Done!");
        }
        Err(e) => {
            eprintln!("send_pub_tx error: {:?}", e);
            return Err(format!("{:?}", e).into());
        }
    }

    Ok(())
}
