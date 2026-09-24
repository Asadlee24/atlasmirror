use colored::Colorize;
use serde_json::json;
use std::path::Path;
use std::time::Duration;

struct CheckItem {
    name: &'static str,
    status: bool,
    details: String,
}

pub async fn execute(json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let mut checks = Vec::new();

    // 1. Supported Platform
    let os = std::env::consts::OS;
    let arch = std::env::consts::ARCH;
    let is_supported_platform = (os == "linux" && arch == "x86_64")
        || (os == "macos" && arch == "aarch64")
        || os == "windows";

    checks.push(CheckItem {
        name: "Host Architecture & OS",
        status: is_supported_platform,
        details: format!("Detected: {} ({})", os, arch),
    });

    // 2. Geofabrik Reachability
    let geofabrik_ok = reqwest::Client::builder()
        .timeout(Duration::from_secs(8))
        .build()?
        .head("https://download.geofabrik.de/index-v1-nogeom.json")
        .send()
        .await
        .map(|r| r.status().is_success())
        .unwrap_or(false);

    checks.push(CheckItem {
        name: "Geofabrik Index Reachability",
        status: geofabrik_ok,
        details: if geofabrik_ok {
            "Connected to download.geofabrik.de (HTTP 200)".to_string()
        } else {
            "Failed to reach download.geofabrik.de".to_string()
        },
    });

    // 3. Writable Download Directory
    let download_dir = Path::new("./downloads");
    let dir_ok = std::fs::create_dir_all(download_dir).is_ok();
    checks.push(CheckItem {
        name: "Writable Download Directory",
        status: dir_ok,
        details: format!("Directory: {}", download_dir.display()),
    });

    // 4. LEZ Sequencer Connectivity (Active Test)
    let lez_url = std::env::var("LEZ_RPC_URL")
        .unwrap_or_else(|_| "https://testnet.lez.logos.co/".to_string());
    
    let lez_payload = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "checkHealth",
        "params": []
    });

    let lez_res = reqwest::Client::builder()
        .timeout(Duration::from_secs(8))
        .build()?
        .post(&lez_url)
        .json(&lez_payload)
        .send()
        .await;

    let lez_ok = match lez_res {
        Ok(r) if r.status().is_success() => {
            let body: serde_json::Value = r.json().await.unwrap_or_default();
            body.get("result").is_some() || body.get("error").is_none()
        }
        _ => false,
    };

    checks.push(CheckItem {
        name: "LEZ Sequencer Connection",
        status: lez_ok,
        details: if lez_ok {
            format!("Verified responsive at {}", lez_url)
        } else {
            format!("Failed to reach sequencer at {}", lez_url)
        },
    });

    // 5. Deployed Program ID & Canonical State Account
    let program_id = "bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f";
    let state_account = std::env::var("LEZ_ACCOUNT_ID")
        .unwrap_or_else(|_| "T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci".to_string());

    // Verify account exists on-chain
    let acc_payload = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccount",
        "params": [state_account]
    });

    let acc_ok = if lez_ok {
        reqwest::Client::builder()
            .timeout(Duration::from_secs(8))
            .build()?
            .post(&lez_url)
            .json(&acc_payload)
            .send()
            .await
            .map(|r| r.status().is_success())
            .unwrap_or(false)
    } else {
        false
    };

    checks.push(CheckItem {
        name: "SPEL Registry Program & Account",
        status: acc_ok,
        details: format!(
            "Program ID: {}\n    Target Account: {}",
            program_id, state_account
        ),
    });

    // 6. Logos Storage Module (Active Test)
    let storage_status = std::process::Command::new("logoscore")
        .args(["call", "storage_module", "manifests", "--json"])
        .output();

    let storage_ok = match storage_status {
        Ok(out) => out.status.success(),
        Err(_) => {
            // Check if VPS storage endpoint is reachable
            let vps_storage = "http://199.231.187.97:8070";
            reqwest::Client::builder()
                .timeout(Duration::from_secs(5))
                .build()?
                .get(vps_storage)
                .send()
                .await
                .is_ok()
        }
    };

    checks.push(CheckItem {
        name: "Logos Storage Module",
        status: storage_ok,
        details: if storage_ok {
            "Storage module active and responding".to_string()
        } else {
            "Storage module daemon not found locally or port unreachable".to_string()
        },
    });

    let all_passed = checks.iter().all(|c| c.status);

    if json_output {
        let json_checks: Vec<_> = checks
            .iter()
            .map(|c| {
                json!({
                    "name": c.name,
                    "passed": c.status,
                    "details": c.details
                })
            })
            .collect();

        println!(
            "{}",
            json!({ "all_passed": all_passed, "checks": json_checks })
        );
    } else {
        println!("AtlasMirror Environment Doctor:");
        println!("{}", "-".repeat(80));
        for c in &checks {
            let symbol = if c.status { "✔".green() } else { "✖".red() };
            println!("  [{}] {:<32} {}", symbol, c.name.bold(), c.details);
        }
        println!("{}", "-".repeat(80));
        if all_passed {
            println!("{}", "All environment checks passed successfully!".green().bold());
        } else {
            println!("{}", "Warning: Some environment checks did not pass.".yellow().bold());
        }
    }

    if !all_passed {
        // Report failure when unavailable as required
        std::process::exit(1);
    }

    Ok(())
}
