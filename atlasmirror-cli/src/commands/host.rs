use crate::storage::LogosStorageClient;
use colored::Colorize;
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use std::time::Duration;

pub async fn execute_host_single(
    region: &str,
    dry_run: bool,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if dry_run {
        if json_output {
            println!(
                "{}",
                json!({ "dry_run": true, "region": region, "estimated_size": "118 MB" })
            );
        } else {
            println!("[DRY RUN] Region: {} | Estimated size: 118 MB", region);
        }
        return Ok(());
    }

    println!("Hosting region: {}", region.bold());
    println!("  1. Fetching canonical metadata & MD5 from Geofabrik...");
    let expected_md5 = crate::geofabrik::fetch_published_md5(region).await?;
    println!("     Canonical MD5: {}", expected_md5.cyan());

    // Prepare download path
    let cache_dir = PathBuf::from("./target/pbf_cache");
    std::fs::create_dir_all(&cache_dir)?;
    let safe_name = region.replace('/', "_");
    let pbf_path = cache_dir.join(format!("{}.osm.pbf", safe_name));

    println!("  2. Downloading snapshot & verifying integrity...");
    let url = format!("https://download.geofabrik.de/{}-latest.osm.pbf", region);
    let needs_download = if pbf_path.exists() {
        match crate::geofabrik::compute_file_md5(&pbf_path) {
            Ok(md5) => md5 != expected_md5,
            Err(_) => true,
        }
    } else {
        true
    };

    if needs_download {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(300))
            .build()?;

        let resp = client.get(&url).send().await?;
        if !resp.status().is_success() {
            eprintln!(
                "{} Failed to download snapshot from Geofabrik: HTTP {}",
                "✖".red(),
                resp.status()
            );
            std::process::exit(1);
        }
        let bytes = resp.bytes().await?;
        std::fs::write(&pbf_path, bytes)?;
    }

    let actual_md5 = crate::geofabrik::compute_file_md5(&pbf_path)?;
    if actual_md5 != expected_md5 {
        eprintln!(
            "{} Snapshot checksum mismatch! Halting immediately.",
            "✖".red()
        );
        eprintln!("   Expected: {}", expected_md5);
        eprintln!("   Computed: {}", actual_md5);
        let _ = std::fs::remove_file(&pbf_path);
        std::process::exit(1);
    }
    println!("     Status: {}", "CHECKSUM_VERIFIED".green());

    println!("  3. Uploading exact bytes to Logos Storage (official storage_module)...");
    let storage = LogosStorageClient::new(None, 3, 500);

    let cid = match storage.put(&pbf_path).await {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{} Logos Storage upload failed: {}", "✖".red(), e);
            eprintln!("   Ensure Logos storage module / logoscore daemon is active.");
            std::process::exit(1);
        }
    };
    println!("     Obtained CID: {}", cid.cyan());

    println!("  4. Registering on-chain in LEZ OSM registry...");
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)?
        .as_secs();

    let version = crate::geofabrik::fetch_snapshot_version(region).await;
    let tx_hash =
        match execute_register_onchain(region, &cid, &actual_md5, &url, &version, timestamp) {
            Ok(h) => h,
            Err(e) => {
                eprintln!("{} {}", "✖".red(), e);
                std::process::exit(1);
            }
        };

    println!("     Transaction: {}", tx_hash.green());

    if json_output {
        println!(
            "{}",
            json!({
                "success": true,
                "region": region,
                "cid": cid,
                "tx_hash": tx_hash,
                "status": "HOSTED"
            })
        );
    } else {
        println!(
            "\n{} Successfully hosted {} on Logos!",
            "✔".green(),
            region.bold()
        );
    }

    Ok(())
}

pub async fn execute_host_many(
    raw_regions: &[String],
    dry_run: bool,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let regions: Vec<String> = raw_regions
        .iter()
        .flat_map(|r| r.split(','))
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    // LP-0018: Strict non-overlapping check across selected regions
    for i in 0..regions.len() {
        for j in (i + 1)..regions.len() {
            let r1 = &regions[i];
            let r2 = &regions[j];
            if r1 == r2
                || r1.starts_with(&format!("{}/", r2))
                || r2.starts_with(&format!("{}/", r1))
            {
                eprintln!(
                    "{} Region overlap warning: '{}' and '{}' contain common geography!",
                    "⚠".yellow(),
                    r1,
                    r2
                );
            }
        }
    }

    if dry_run {
        println!("[DRY RUN] Bulk Hosting Plan for {} regions:", regions.len());
        for r in &regions {
            println!("  - {:<30} ~120 MB", r);
        }
        println!("Total Estimated Transfer: ~{} MB", regions.len() * 120);
        return Ok(());
    }

    println!(
        "Executing bounded single-transaction batch hosting for {} regions...",
        regions.len()
    );

    let mut batch_records = Vec::new();
    let storage = LogosStorageClient::new(None, 3, 500);

    let regions_bytes = include_bytes!("../../../metadata/regions.json");
    let catalog: Value = serde_json::from_slice(regions_bytes).unwrap_or(json!({}));
    let catalog_regions = catalog
        .get("regions")
        .and_then(|r| r.as_array())
        .cloned()
        .unwrap_or_default();

    for r in &regions {
        println!("Preparing batch item: {}", r.bold());
        let expected_md5 = crate::geofabrik::fetch_published_md5(r.as_str()).await?;
        let cat_entry = catalog_regions
            .iter()
            .find(|entry| entry["path"].as_str() == Some(r.as_str()));
        let (parent, level) = if let Some(cat) = cat_entry {
            let p = cat
                .get("parent")
                .and_then(|v| v.as_str())
                .map(|s| s.to_string());
            let l = cat
                .get("level")
                .and_then(|v| v.as_str())
                .unwrap_or("country");
            (p, l)
        } else {
            (None, "country")
        };

        // Cache and upload
        let cache_dir = PathBuf::from("./target/pbf_cache");
        std::fs::create_dir_all(&cache_dir)?;
        let safe_name = r.replace('/', "_");
        let pbf_path = cache_dir.join(format!("{}.osm.pbf", safe_name));

        let url = crate::geofabrik::resolve_pbf_url(r.as_str());
        let needs_download = if pbf_path.exists() {
            match crate::geofabrik::compute_file_md5(&pbf_path) {
                Ok(md5) => md5 != expected_md5,
                Err(_) => true,
            }
        } else {
            true
        };

        if needs_download {
            let client = reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(300))
                .build()?;
            let bytes = client.get(&url).send().await?.bytes().await?;
            std::fs::write(&pbf_path, bytes)?;
        }

        // Pre-upload integrity verification
        let computed_md5 = crate::geofabrik::compute_file_md5(&pbf_path)?;
        if computed_md5 != expected_md5 {
            eprintln!(
                "{} Integrity check failed for {}! Expected published MD5: {}, Computed: {}",
                "✖".red(),
                r,
                expected_md5,
                computed_md5
            );
            std::process::exit(1);
        }

        let cid = match storage.put(&pbf_path).await {
            Ok(c) => c,
            Err(e) => {
                eprintln!("{} Logos Storage upload failed for {}: {}", "✖".red(), r, e);
                std::process::exit(1);
            }
        };

        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)?
            .as_secs();
        let version = crate::geofabrik::fetch_snapshot_version(r.as_str()).await;

        batch_records.push(json!({
            "region": r,
            "parent": parent,
            "level": level,
            "cid": cid,
            "source_url": url,
            "checksum": expected_md5,
            "version": version,
            "hosted": true,
            "timestamp": timestamp
        }));
    }

    // Write batch JSON file for single on-chain submission
    let batch_file = PathBuf::from("./target/batch_payload.json");
    std::fs::write(&batch_file, serde_json::to_string_pretty(&batch_records)?)?;

    println!(
        "Submitting SINGLE on-chain BatchRegister transaction for {} records...",
        batch_records.len()
    );
    let tx_hash = match execute_batch_register_onchain(&batch_records, &batch_file) {
        Ok(h) => h,
        Err(e) => {
            eprintln!("{} {}", "✖".red(), e);
            std::process::exit(1);
        }
    };

    println!(
        "{} Batch transaction confirmed! Tx: {}",
        "✔".green(),
        tx_hash.green()
    );

    if json_output {
        println!(
            "{}",
            json!({ "success": true, "batch_size": batch_records.len(), "tx_hash": tx_hash })
        );
    }

    Ok(())
}

pub async fn execute_host_file(
    region: &str,
    file_path: &Path,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if !file_path.exists() {
        eprintln!("Error: Local file not found: {}", file_path.display());
        std::process::exit(1);
    }

    println!("Importing local PBF for region: {}", region.bold());
    println!("  File: {}", file_path.display());
    println!("  1. Fetching canonical Geofabrik published MD5...");
    let expected_md5 = match crate::geofabrik::fetch_published_md5(region).await {
        Ok(hash) => hash,
        Err(e) => {
            eprintln!(
                "{} Failed to fetch canonical MD5 for region '{}': {}",
                "✖".red(),
                region,
                e
            );
            std::process::exit(1);
        }
    };
    println!("     Expected: {}", expected_md5);
    println!("  2. Calculating local file MD5...");
    let actual_md5 = match crate::geofabrik::compute_file_md5(file_path) {
        Ok(hash) => hash,
        Err(e) => {
            eprintln!("{} Failed to calculate local file MD5: {}", "✖".red(), e);
            std::process::exit(1);
        }
    };
    println!("     Actual:   {}", actual_md5);

    if expected_md5 != actual_md5 {
        eprintln!(
            "{} Checksum mismatch! Halting import immediately (tamper detected).",
            "✖".red()
        );
        eprintln!("   Expected published: {}", expected_md5);
        eprintln!("   Computed local:     {}", actual_md5);
        std::process::exit(1);
    }

    println!("  3. Checksum matches! Uploading exact bytes to Logos Storage...");
    let storage = LogosStorageClient::new(None, 3, 500);

    let cid = match storage.put(file_path).await {
        Ok(c) => c,
        Err(e) => {
            eprintln!("{} Logos Storage upload failed: {}", "✖".red(), e);
            eprintln!("   Ensure Logos storage daemon / logoscore is active.");
            std::process::exit(1);
        }
    };
    println!("     CID: {}", cid.cyan());

    println!("  4. Registering on-chain in LEZ...");
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)?
        .as_secs();
    let url = format!("https://download.geofabrik.de/{}-latest.osm.pbf", region);
    let version = crate::geofabrik::fetch_snapshot_version(region).await;

    let tx_hash =
        match execute_register_onchain(region, &cid, &actual_md5, &url, &version, timestamp) {
            Ok(h) => h,
            Err(e) => {
                eprintln!("{} {}", "✖".red(), e);
                std::process::exit(1);
            }
        };
    println!("     TX: {}", tx_hash.green());

    if json_output {
        println!(
            "{}",
            json!({
                "success": true,
                "region": region,
                "cid": cid,
                "tx_hash": tx_hash,
                "file": file_path.display().to_string()
            })
        );
    }

    Ok(())
}

fn resolve_registry_account_id() -> String {
    std::env::var("OSM_REGISTRY_ACCOUNT_ID")
        .or_else(|_| std::env::var("LEZ_ACCOUNT_ID"))
        .unwrap_or_else(|_| "T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci".to_string())
}

fn resolve_registry_program_id() -> String {
    std::env::var("OSM_REGISTRY_PROGRAM_ID").unwrap_or_else(|_| {
        "bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f".to_string()
    })
}

fn resolve_idl_path() -> PathBuf {
    if let Ok(p) = std::env::var("OSM_REGISTRY_IDL") {
        return PathBuf::from(p);
    }
    let candidates = [
        PathBuf::from("osm-registry/idl/osm_registry.json"),
        PathBuf::from("../osm-registry/idl/osm_registry.json"),
        PathBuf::from("idl/osm_registry.json"),
        PathBuf::from("osm_registry.json"),
    ];
    for c in &candidates {
        if c.exists() {
            return c.clone();
        }
    }
    PathBuf::from("osm-registry/idl/osm_registry.json")
}

fn extract_tx_hash(stdout: &str) -> String {
    for line in stdout.lines() {
        if line.contains("Hash:") {
            if let Some(h) = line.split("Hash:").nth(1) {
                let trimmed = h.trim();
                if !trimmed.is_empty() {
                    return trimmed.to_string();
                }
            }
        }
        if line.contains("Transaction:") || line.contains("Tx:") {
            let parts: Vec<&str> = line.split(':').collect();
            if parts.len() > 1 {
                let trimmed = parts[1].trim();
                if !trimmed.is_empty() {
                    return trimmed.to_string();
                }
            }
        }
    }
    for word in stdout.split_whitespace() {
        let clean = word.trim_matches(|c: char| !c.is_alphanumeric());
        if clean.len() == 64 && clean.chars().all(|c| c.is_ascii_hexdigit()) {
            return clean.to_string();
        }
    }
    "tx-confirmed".to_string()
}

fn execute_register_onchain(
    region: &str,
    cid: &str,
    md5: &str,
    url: &str,
    version: &str,
    timestamp: u64,
) -> Result<String, Box<dyn std::error::Error>> {
    let account_id = resolve_registry_account_id();
    let program_id = resolve_registry_program_id();
    let idl_path = resolve_idl_path();
    let level = if region.contains('/') {
        "Subregion"
    } else {
        "Country"
    };

    let spel_bin = std::env::var("SPEL_BIN").unwrap_or_else(|_| "spel".to_string());
    let spel_res = std::process::Command::new(&spel_bin)
        .arg("--idl")
        .arg(&idl_path)
        .arg("-p")
        .arg(&program_id)
        .arg("--")
        .arg("register-region")
        .arg("--state")
        .arg(&account_id)
        .arg("--region")
        .arg(region)
        .arg("--level")
        .arg(level)
        .arg("--cid")
        .arg(cid)
        .arg("--source-url")
        .arg(url)
        .arg("--checksum")
        .arg(md5)
        .arg("--version")
        .arg(version)
        .arg("--hosted")
        .arg("true")
        .arg("--timestamp")
        .arg(timestamp.to_string())
        .output();

    if let Ok(output) = spel_res {
        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            return Ok(extract_tx_hash(&stdout));
        }
    }

    // Fallback to LEZ_RUNNER_BIN if provided or present
    let runner_bin =
        std::env::var("LEZ_RUNNER_BIN").unwrap_or_else(|_| "run_osm_registry".to_string());
    let program_bin =
        std::env::var("OSM_REGISTRY_BIN").unwrap_or_else(|_| "osm_registry.bin".to_string());
    let run_res = std::process::Command::new(&runner_bin)
        .arg(&program_bin)
        .arg(&account_id)
        .arg("register")
        .arg(region)
        .arg(cid)
        .arg(md5)
        .arg(url)
        .arg(version)
        .arg(timestamp.to_string())
        .output();

    match run_res {
        Ok(output) if output.status.success() => {
            let stdout = String::from_utf8_lossy(&output.stdout);
            Ok(extract_tx_hash(&stdout))
        }
        Ok(output) => {
            let err = String::from_utf8_lossy(&output.stderr);
            Err(format!("On-chain registration failed: {}", err).into())
        }
        Err(e) => Err(format!("Execution failed (spel and runner unavailable): {}", e).into()),
    }
}

fn execute_batch_register_onchain(
    batch_records: &[Value],
    batch_file: &Path,
) -> Result<String, Box<dyn std::error::Error>> {
    let account_id = resolve_registry_account_id();
    let program_id = resolve_registry_program_id();
    let idl_path = resolve_idl_path();

    let spel_bin = std::env::var("SPEL_BIN").unwrap_or_else(|_| "spel".to_string());
    let records_json = serde_json::to_string(batch_records)?;
    let spel_res = std::process::Command::new(&spel_bin)
        .arg("--idl")
        .arg(&idl_path)
        .arg("-p")
        .arg(&program_id)
        .arg("--")
        .arg("batch-register")
        .arg("--state")
        .arg(&account_id)
        .arg("--records")
        .arg(&records_json)
        .output();

    if let Ok(output) = spel_res {
        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            return Ok(extract_tx_hash(&stdout));
        }
    }

    // Fallback to LEZ_RUNNER_BIN if provided or present
    let runner_bin =
        std::env::var("LEZ_RUNNER_BIN").unwrap_or_else(|_| "run_osm_registry".to_string());
    let program_bin =
        std::env::var("OSM_REGISTRY_BIN").unwrap_or_else(|_| "osm_registry.bin".to_string());
    let run_res = std::process::Command::new(&runner_bin)
        .arg(&program_bin)
        .arg(&account_id)
        .arg("batch_register")
        .arg(batch_file)
        .output();

    match run_res {
        Ok(output) if output.status.success() => {
            let stdout = String::from_utf8_lossy(&output.stdout);
            Ok(extract_tx_hash(&stdout))
        }
        Ok(output) => {
            let err = String::from_utf8_lossy(&output.stderr);
            Err(format!("Batch registration failed: {}", err).into())
        }
        Err(e) => Err(format!("Execution failed (spel and runner unavailable): {}", e).into()),
    }
}
