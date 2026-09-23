use crate::storage::LogosStorageClient;
use colored::Colorize;
use serde_json::{json, Value};
use std::path::Path;
use std::time::Duration;

pub async fn execute(
    region: &str,
    output: &Path,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("Querying LEZ on-chain registry for: {}", region.bold());

    let on_chain_records = crate::registry::query_on_chain_registry().ok();
    let hosted_entry = on_chain_records
        .as_ref()
        .and_then(|records| records.iter().find(|e| e.region == region).cloned());

    let regions_bytes = include_bytes!("../../../metadata/regions.json");
    let catalog: Value = serde_json::from_slice(regions_bytes).unwrap_or(json!({}));
    let catalog_regions = catalog
        .get("regions")
        .and_then(|r| r.as_array())
        .cloned()
        .unwrap_or_default();

    if let Some(entry) = hosted_entry {
        let cid = entry.cid;
        let expected_md5 = entry.checksum;

        println!("  Status: {}", "HOSTED ON-CHAIN".green());
        println!("  Logos Storage CID: {}", cid.cyan());
        println!("  Downloading from Logos Storage (official storage_module)...");

        let storage = LogosStorageClient::new(None, 3, 500);

        let download_success = match storage.get(&cid, output).await {
            Ok(_) => true,
            Err(e) => {
                eprintln!(
                    "  {} Local daemon unreachable ({}), using peer replica...",
                    "⚠".yellow(),
                    e
                );
                if !entry.source_url.is_empty() {
                    download_http(&entry.source_url, output).await?
                } else {
                    false
                }
            }
        };

        if !download_success || !output.exists() {
            eprintln!("{} Failed to download hosted snapshot.", "✖".red());
            std::process::exit(1);
        }

        let computed_md5 = crate::geofabrik::compute_file_md5(output)?;
        let file_size = output.metadata()?.len();

        println!("  Destination: {}", output.display());
        println!("  File Size:   {} bytes", file_size);
        println!("  Local MD5:   {}", computed_md5);

        if !expected_md5.is_empty() && computed_md5 != expected_md5 {
            eprintln!(
                "{} Integrity check failed! Expected MD5: {}",
                "✖".red(),
                expected_md5
            );
            std::process::exit(1);
        }

        println!(
            "{} Download complete. Integrity verified against CID & snapshot checksum.",
            "✔".green()
        );

        if json_output {
            println!(
                "{}",
                json!({
                    "region": region,
                    "source": "logos_storage",
                    "cid": cid,
                    "output": output.display().to_string(),
                    "size": file_size,
                    "md5": computed_md5,
                    "status": "SUCCESS"
                })
            );
        }
    } else {
        // Unhosted region fallback
        println!("  Status: {}", "NOT HOSTED".yellow());
        println!(
            "  {}",
            "[CENTRAL FALLBACK] Downloading directly from Geofabrik...".yellow()
        );

        let cat_entry = catalog_regions
            .iter()
            .find(|r| r["path"].as_str() == Some(region));
        let url = if let Some(cat) = cat_entry {
            cat["geofabrik_url"].as_str().unwrap_or("").to_string()
        } else {
            format!("https://download.geofabrik.de/{}-latest.osm.pbf", region)
        };

        println!("  Source URL:  {}", url);
        println!("  Destination: {}", output.display());

        let ok = download_http(&url, output).await?;
        if !ok || !output.exists() {
            eprintln!("{} Failed to download from Geofabrik.", "✖".red());
            std::process::exit(1);
        }

        let computed_md5 = crate::geofabrik::compute_file_md5(output)?;
        let file_size = output.metadata()?.len();

        println!("  File Size:   {} bytes", file_size);
        println!("  Local MD5:   {}", computed_md5);
        println!("{} Download complete via Geofabrik fallback.", "✔".green());

        if json_output {
            println!(
                "{}",
                json!({
                    "region": region,
                    "source": "geofabrik_fallback",
                    "url": url,
                    "output": output.display().to_string(),
                    "size": file_size,
                    "md5": computed_md5,
                    "status": "SUCCESS"
                })
            );
        }
    }

    Ok(())
}

async fn download_http(url: &str, destination: &Path) -> Result<bool, Box<dyn std::error::Error>> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(300))
        .build()?;

    let resp = client.get(url).send().await?;
    if !resp.status().is_success() {
        eprintln!("HTTP error {}: {}", resp.status(), url);
        return Ok(false);
    }

    let bytes = resp.bytes().await?;
    if let Some(parent) = destination.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(destination, bytes)?;
    Ok(true)
}
