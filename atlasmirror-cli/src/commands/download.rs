use crate::storage::LogosStorageClient;
use colored::Colorize;
use futures_util::StreamExt;
use indicatif::{ProgressBar, ProgressStyle};
use serde_json::json;
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};
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

    let catalog_bytes = include_bytes!("../../../metadata/regions.json");
    let catalog: serde_json::Value = serde_json::from_slice(catalog_bytes).unwrap_or(json!({}));
    let catalog_regions = catalog
        .get("regions")
        .and_then(|r| r.as_array())
        .cloned()
        .unwrap_or_default();

    let cat_item = catalog_regions
        .iter()
        .find(|r| r.get("path").and_then(|p| p.as_str()) == Some(region));

    if cat_item.is_none() {
        return Err(format!(
            "Region '{}' is not in the predefined LP-0018 catalog.",
            region
        )
        .into());
    }
    let cat_item = cat_item.unwrap();

    let temp_dest = if let Some(ext) = output.extension() {
        output.with_extension(format!("{}.part", ext.to_string_lossy()))
    } else {
        PathBuf::from(format!("{}.part", output.display()))
    };

    if let Some(entry) = hosted_entry {
        let cid = entry.cid;
        let expected_md5 = entry.checksum;

        println!("  Status: {}", "HOSTED ON-CHAIN".green());
        println!("  Logos Storage CID: {}", cid.cyan());
        println!("  Expected MD5:      {}", expected_md5);
        println!("  Retrieving via Logos Storage peers...");

        let storage = LogosStorageClient::new(None, 3, 500);
        let download_source = "logos_storage";

        match storage.get(&cid, &temp_dest).await {
            Ok(_) => {}
            Err(e) => {
                eprintln!("  {} Logos Storage retrieval failed: {}", "✖".red(), e);
                eprintln!(
                    "  {} Under LP-0018 requirements, hosted snapshots must be retrieved independently via Logos Storage.",
                    "✖".red()
                );
                std::process::exit(1);
            }
        }

        if !temp_dest.exists() {
            eprintln!(
                "{} Failed to download snapshot from Logos Storage.",
                "✖".red()
            );
            std::process::exit(1);
        }

        let computed_md5 = crate::geofabrik::compute_file_md5(&temp_dest)?;
        let file_size = temp_dest.metadata()?.len();

        println!("  Destination: {}", output.display());
        println!("  File Size:   {} bytes", file_size);
        println!("  Local MD5:   {}", computed_md5);

        if !expected_md5.is_empty() && computed_md5 != expected_md5 {
            let _ = std::fs::remove_file(&temp_dest);
            eprintln!(
                "{} Integrity check failed! Expected MD5: {}, got: {}",
                "✖".red(),
                expected_md5,
                computed_md5
            );
            std::process::exit(1);
        }

        // Atomic rename after checksum verification
        std::fs::rename(&temp_dest, output)?;

        println!(
            "{} Download complete. Integrity verified against published checksum.",
            "✔".green()
        );

        if json_output {
            println!(
                "{}",
                json!({
                    "region": region,
                    "source": download_source,
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

        let url = cat_item["geofabrik_url"].as_str().unwrap_or_default();
        let md5_url = cat_item["md5_url"].as_str().unwrap_or_default();

        let expected_md5 = reqwest::get(md5_url)
            .await?
            .text()
            .await?
            .split_whitespace()
            .next()
            .unwrap_or_default()
            .to_string();

        let ok = stream_http_download(url, &temp_dest).await?;
        if !ok || !temp_dest.exists() {
            eprintln!("{} Failed to download from Geofabrik.", "✖".red());
            std::process::exit(1);
        }

        let computed_md5 = crate::geofabrik::compute_file_md5(&temp_dest)?;
        let file_size = temp_dest.metadata()?.len();

        if !expected_md5.is_empty() && computed_md5 != expected_md5 {
            let _ = std::fs::remove_file(&temp_dest);
            eprintln!(
                "{} Integrity check failed! Expected: {}, got: {}",
                "✖".red(),
                expected_md5,
                computed_md5
            );
            std::process::exit(1);
        }

        std::fs::rename(&temp_dest, output)?;

        println!(
            "{} Central fallback download complete & verified.",
            "✔".green()
        );

        if json_output {
            println!(
                "{}",
                json!({
                    "region": region,
                    "source": "geofabrik_fallback",
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

/// Streams large file download with progress bar without loading entire file in memory
async fn stream_http_download(
    url: &str,
    output: &Path,
) -> Result<bool, Box<dyn std::error::Error>> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(600))
        .build()?;

    let res = client.get(url).send().await?;
    if !res.status().is_success() {
        return Ok(false);
    }

    let total_size = res.content_length().unwrap_or(0);
    let pb = ProgressBar::new(total_size);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {bytes}/{total_bytes} ({eta})")?
            .progress_chars("#>-"),
    );

    let mut file = File::create(output)?;
    let mut stream = res.bytes_stream();

    while let Some(chunk_res) = stream.next().await {
        let chunk = chunk_res?;
        file.write_all(&chunk)?;
        pb.inc(chunk.len() as u64);
    }

    file.flush()?;
    pb.finish_with_message("Download finished");
    Ok(true)
}
