use crate::storage::LogosStorageClient;
use colored::Colorize;
use serde_json::{json, Value};
use std::path::{Path, PathBuf};

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
    let url = crate::geofabrik::resolve_pbf_url(region);
    let needs_download = if pbf_path.exists() {
        match crate::geofabrik::compute_file_md5(&pbf_path) {
            Ok(md5) => md5 != expected_md5,
            Err(_) => true,
        }
    } else {
        true
    };

    if needs_download {
        if let Err(e) =
            crate::geofabrik::download_pbf_stream(&url, &pbf_path, |_downloaded, _total| {}).await
        {
            eprintln!(
                "{} Failed to download snapshot from Geofabrik: {}",
                "✖".red(),
                e
            );
            std::process::exit(1);
        }
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

    for r in &regions {
        println!("Preparing batch item: {}", r.bold());
        let expected_md5 = crate::geofabrik::fetch_published_md5(r.as_str()).await?;
        let (level, parent) = resolve_region_metadata(r.as_str());

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
            if let Err(e) =
                crate::geofabrik::download_pbf_stream(&url, &pbf_path, |_downloaded, _total| {})
                    .await
            {
                eprintln!(
                    "{} Failed to download snapshot from Geofabrik for {}: {}",
                    "✖".red(),
                    r,
                    e
                );
                std::process::exit(1);
            }
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
    let url = crate::geofabrik::resolve_pbf_url(region);
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

pub fn resolve_region_metadata(region_path: &str) -> (String, Option<String>) {
    let candidates = [
        PathBuf::from("metadata/regions.json"),
        PathBuf::from("../metadata/regions.json"),
        PathBuf::from("../../metadata/regions.json"),
    ];

    for c in &candidates {
        if c.exists() {
            if let Ok(content) = std::fs::read_to_string(c) {
                if let Ok(val) = serde_json::from_str::<serde_json::Value>(&content) {
                    if let Some(arr) = val.get("regions").and_then(|r| r.as_array()) {
                        for item in arr {
                            if item.get("path").and_then(|p| p.as_str()) == Some(region_path) {
                                let level_str = item
                                    .get("level")
                                    .and_then(|l| l.as_str())
                                    .unwrap_or("country");
                                let level = if level_str.eq_ignore_ascii_case("subregion") {
                                    "Subregion".to_string()
                                } else {
                                    "Country".to_string()
                                };
                                let parent = item
                                    .get("parent")
                                    .and_then(|p| p.as_str())
                                    .filter(|s| !s.is_empty() && *s != "null")
                                    .map(|s| s.to_string());
                                return (level, parent);
                            }
                        }
                    }
                }
            }
        }
    }

    // Official LP-0018 closed set specification fallback:
    // Only official decomposed subregions in US, India, China, Russia are Subregions with parent.
    // All other regions (e.g. asia/pakistan, europe/germany, africa/egypt) are Country with parent None.
    if region_path.starts_with("us/") {
        ("Subregion".to_string(), Some("us".to_string()))
    } else if region_path.starts_with("india/") {
        ("Subregion".to_string(), Some("india".to_string()))
    } else if region_path.starts_with("china/") {
        ("Subregion".to_string(), Some("china".to_string()))
    } else if region_path.starts_with("russia/") {
        ("Subregion".to_string(), Some("russia".to_string()))
    } else {
        ("Country".to_string(), None)
    }
}

fn extract_tx_hash(stdout: &str) -> Result<String, String> {
    for line in stdout.lines() {
        if line.contains("Hash:") {
            if let Some(h) = line.split("Hash:").nth(1) {
                let trimmed = h.trim();
                if !trimmed.is_empty() {
                    return Ok(trimmed.to_string());
                }
            }
        }
        if line.contains("Transaction:") || line.contains("Tx:") {
            let parts: Vec<&str> = line.split(':').collect();
            if parts.len() > 1 {
                let trimmed = parts[1].trim();
                if !trimmed.is_empty() {
                    return Ok(trimmed.to_string());
                }
            }
        }
    }
    for word in stdout.split_whitespace() {
        let clean = word.trim_matches(|c: char| !c.is_alphanumeric());
        if clean.len() == 64 && clean.chars().all(|c| c.is_ascii_hexdigit()) {
            return Ok(clean.to_string());
        }
    }
    Err("Failed to parse genuine transaction hash from on-chain output".to_string())
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
    let (level, parent) = resolve_region_metadata(region);

    let spel_bin = std::env::var("SPEL_BIN").unwrap_or_else(|_| "spel".to_string());
    let mut spel_cmd = std::process::Command::new(&spel_bin);
    spel_cmd
        .arg("--idl")
        .arg(&idl_path)
        .arg("-p")
        .arg(&program_id)
        .arg("--")
        .arg("register-region")
        .arg("--state")
        .arg(&account_id)
        .arg("--region")
        .arg(region);

    if let Some(p) = &parent {
        spel_cmd.arg("--parent").arg(p);
    }

    spel_cmd
        .arg("--level")
        .arg(&level)
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
        .arg(timestamp.to_string());

    let spel_res = spel_cmd.output();

    if let Ok(output) = spel_res {
        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            return extract_tx_hash(&stdout).map_err(|e| e.into());
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
            extract_tx_hash(&stdout).map_err(|e| e.into())
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
            return extract_tx_hash(&stdout).map_err(|e| e.into());
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
            extract_tx_hash(&stdout).map_err(|e| e.into())
        }
        Ok(output) => {
            let err = String::from_utf8_lossy(&output.stderr);
            Err(format!("Batch registration failed: {}", err).into())
        }
        Err(e) => Err(format!("Execution failed (spel and runner unavailable): {}", e).into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resolve_pakistan_hierarchy() {
        let (level, parent) = resolve_region_metadata("asia/pakistan");
        assert_eq!(level, "Country");
        assert_eq!(parent, None);
    }

    #[test]
    fn test_resolve_china_henan_hierarchy() {
        let (level, parent) = resolve_region_metadata("china/henan");
        assert_eq!(level, "Subregion");
        assert_eq!(parent, Some("china".to_string()));
    }

    #[test]
    fn test_resolve_germany_hierarchy() {
        let (level, parent) = resolve_region_metadata("europe/germany");
        assert_eq!(level, "Country");
        assert_eq!(parent, None);
    }

    #[test]
    fn test_resolve_us_subregion_hierarchy() {
        let (level, parent) = resolve_region_metadata("us/california");
        assert_eq!(level, "Subregion");
        assert_eq!(parent, Some("us".to_string()));
    }

    #[test]
    fn test_extract_tx_hash_parsing() {
        let out = "Instruction: register_region\nTx: a1b2c3d4e5f6\nSuccess";
        assert_eq!(extract_tx_hash(out).unwrap(), "a1b2c3d4e5f6");

        let out_hash =
            "Transaction Hash: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
        assert_eq!(
            extract_tx_hash(out_hash).unwrap(),
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        );

        let out_fail = "Something broke completely without any hash";
        assert!(extract_tx_hash(out_fail).is_err());
    }
}
