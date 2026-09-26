use borsh::BorshDeserialize;
use osm_registry_core::RegistryState;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::process::Command;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct OnChainRecord {
    pub region: String,
    pub parent: Option<String>,
    pub level: String,
    pub cid: String,
    pub source_url: String,
    pub checksum: String,
    pub version: String,
    pub hosted: bool,
    pub timestamp: u64,
}

/// Queries the genuine on-chain LEZ registry using a pure async RPC client.
/// Uses direct RPC call to the sequencer first, falling back to LEZ_RUNNER_BIN if configured.
pub async fn query_on_chain_registry() -> Result<Vec<OnChainRecord>, Box<dyn std::error::Error>> {
    let rpc_url = std::env::var("LEZ_RPC_URL")
        .unwrap_or_else(|_| "https://testnet.lez.logos.co/".to_string());
    let account_id = std::env::var("LEZ_ACCOUNT_ID")
        .unwrap_or_else(|_| "T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci".to_string());

    // 1. Attempt direct async RPC query
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build();

    if let Ok(cli) = client {
        let payload = json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccount",
            "params": [account_id]
        });

        if let Ok(resp) = cli.post(&rpc_url).json(&payload).send().await {
            if resp.status().is_success() {
                if let Ok(body) = resp.json::<serde_json::Value>().await {
                    if let Some(data_arr) = body["result"]["data"].as_array() {
                        let raw_bytes: Vec<u8> = data_arr
                            .iter()
                            .filter_map(|v| v.as_u64().map(|n| n as u8))
                            .collect();

                        if !raw_bytes.is_empty() {
                            if let Ok(state) = RegistryState::try_from_slice(&raw_bytes) {
                                let records: Vec<OnChainRecord> = state
                                    .records
                                    .into_iter()
                                    .map(|r| OnChainRecord {
                                        region: r.region,
                                        parent: r.parent,
                                        level: format!("{:?}", r.level).to_lowercase(),
                                        cid: r.cid,
                                        source_url: r.source_url,
                                        checksum: r.checksum,
                                        version: r.version,
                                        hosted: r.hosted,
                                        timestamp: r.timestamp,
                                    })
                                    .collect();
                                return Ok(records);
                            }
                        }
                    }
                }
            }
        }
    }

    // 2. Fallback to LEZ_RUNNER_BIN if direct RPC is unavailable
    let runner_bin = std::env::var("LEZ_RUNNER_BIN").unwrap_or_else(|_| {
        "/root/lez-testnet-compatible/target/release/run_osm_registry".to_string()
    });
    let program_bin =
        std::env::var("OSM_REGISTRY_BIN").unwrap_or_else(|_| "/root/osm_registry.bin".to_string());

    let output = Command::new(&runner_bin)
        .arg(&program_bin)
        .arg(&account_id)
        .arg("query")
        .output();

    match output {
        Ok(out) if out.status.success() => {
            let stdout = String::from_utf8_lossy(&out.stdout);
            let mut records = Vec::new();
            for line in stdout.lines() {
                if let Some(rest) = line.strip_prefix("REGION_RECORD:") {
                    let mut region = String::new();
                    let mut parent = None;
                    let mut level = String::new();
                    let mut cid = String::new();
                    let mut source_url = String::new();
                    let mut checksum = String::new();
                    let mut version = String::new();
                    let mut hosted = true;
                    let mut timestamp = 0u64;

                    for part in rest.split(", ") {
                        let mut kv = part.splitn(2, '=');
                        if let (Some(k), Some(v)) = (kv.next(), kv.next()) {
                            let k = k.trim();
                            let v = v.trim();
                            match k {
                                "region" => region = v.to_string(),
                                "parent" => {
                                    if v != "None" && !v.is_empty() {
                                        let cleaned = v
                                            .trim_start_matches("Some(")
                                            .trim_end_matches(')')
                                            .trim_matches('"');
                                        parent = Some(cleaned.to_string());
                                    }
                                }
                                "level" => level = v.to_string(),
                                "cid" => cid = v.to_string(),
                                "source_url" => source_url = v.to_string(),
                                "checksum" => checksum = v.to_string(),
                                "version" => version = v.to_string(),
                                "hosted" => hosted = v.parse().unwrap_or(true),
                                "timestamp" => timestamp = v.parse().unwrap_or(0),
                                _ => {}
                            }
                        }
                    }
                    if !region.is_empty() {
                        records.push(OnChainRecord {
                            region,
                            parent,
                            level,
                            cid,
                            source_url,
                            checksum,
                            version,
                            hosted,
                            timestamp,
                        });
                    }
                }
            }
            Ok(records)
        }
        Ok(out) => {
            let err = String::from_utf8_lossy(&out.stderr);
            Err(format!("On-chain query failed: {}", err).into())
        }
        Err(e) => Err(format!(
            "LEZ RPC unreachable and runner binary unavailable at '{}': {}",
            runner_bin, e
        )
        .into()),
    }
}
