#![allow(dead_code)]

use futures_util::StreamExt;
use md5::{Digest, Md5};
use std::fs::File;
use std::io::{Read, Write};
use std::path::Path;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum GeofabrikError {
    #[error("HTTP request failed: {0}")]
    Network(#[from] reqwest::Error),
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Checksum mismatch: expected {expected}, computed {computed}")]
    ChecksumMismatch { expected: String, computed: String },
    #[error("Failed to parse MD5 checksum response: {0}")]
    InvalidChecksumResponse(String),
}

fn get_catalog_urls(region_path: &str) -> Option<(String, String)> {
    let bytes = include_bytes!("../../metadata/regions.json");
    if let Ok(val) = serde_json::from_slice::<serde_json::Value>(bytes) {
        if let Some(arr) = val.get("regions").and_then(|r| r.as_array()) {
            for item in arr {
                if item.get("path").and_then(|p| p.as_str()) == Some(region_path) {
                    let pbf = item
                        .get("geofabrik_url")
                        .and_then(|u| u.as_str())
                        .map(|s| s.to_string());
                    let md5 = item
                        .get("md5_url")
                        .and_then(|u| u.as_str())
                        .map(|s| s.to_string());
                    if let (Some(p), Some(m)) = (pbf, md5) {
                        return Some((p, m));
                    }
                }
            }
        }
    }
    None
}

/// Resolves the canonical Geofabrik PBF URL for a region path.
pub fn resolve_pbf_url(region_path: &str) -> String {
    if let Some((pbf, _)) = get_catalog_urls(region_path) {
        return pbf;
    }
    format!(
        "https://download.geofabrik.de/{}-latest.osm.pbf",
        region_path
    )
}

/// Resolves the canonical Geofabrik MD5 URL for a region path.
pub fn resolve_md5_url(region_path: &str) -> String {
    if let Some((_, md5)) = get_catalog_urls(region_path) {
        return md5;
    }
    format!(
        "https://download.geofabrik.de/{}-latest.osm.pbf.md5",
        region_path
    )
}

/// Fetches and parses the canonical MD5 checksum published by Geofabrik.
pub async fn fetch_published_md5(region_path: &str) -> Result<String, GeofabrikError> {
    let url = resolve_md5_url(region_path);
    let client = reqwest::Client::builder()
        .user_agent("AtlasMirror/1.0 (LP-0018 Evaluator)")
        .build()
        .unwrap_or_else(|_| reqwest::Client::new());
    let resp = client.get(&url).send().await?.text().await?;

    // Geofabrik MD5 format is typically: "<md5_hex>  <filename>"
    let raw = resp.trim();
    let parts: Vec<&str> = raw.split_whitespace().collect();
    if let Some(hash) = parts.first() {
        if hash.len() == 32 && hash.chars().all(|c| c.is_ascii_hexdigit()) {
            return Ok(hash.to_ascii_lowercase());
        }
    }

    Err(GeofabrikError::InvalidChecksumResponse(raw.to_string()))
}

/// Computes the MD5 checksum of a local file in bounded streaming chunks.
pub fn compute_file_md5(path: &Path) -> Result<String, std::io::Error> {
    let mut file = File::open(path)?;
    let mut hasher = Md5::new();
    let mut buffer = [0u8; 64 * 1024]; // 64 KB streaming buffer

    loop {
        let count = file.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
    }

    Ok(hex::encode(hasher.finalize()))
}

/// Streams download of a PBF snapshot directly to destination, reporting progress.
pub async fn download_pbf_stream(
    url: &str,
    destination: &Path,
    on_progress: impl Fn(u64, Option<u64>),
) -> Result<(), GeofabrikError> {
    let client = reqwest::Client::builder()
        .user_agent("AtlasMirror/1.0 (LP-0018 Evaluator)")
        .build()
        .unwrap_or_else(|_| reqwest::Client::new());
    let resp = client.get(url).send().await?;

    let total_size = resp.content_length();
    let mut stream = resp.bytes_stream();

    let temp_dest = destination.with_extension("part");
    let mut file = File::create(&temp_dest)?;
    let mut downloaded: u64 = 0;

    while let Some(chunk_result) = stream.next().await {
        match chunk_result {
            Ok(chunk) => {
                file.write_all(&chunk)?;
                downloaded += chunk.len() as u64;
                on_progress(downloaded, total_size);
            }
            Err(e) => {
                // Discard partial file on failure
                drop(file);
                let _ = std::fs::remove_file(&temp_dest);
                return Err(GeofabrikError::Network(e));
            }
        }
    }

    file.flush()?;
    drop(file);

    // Atomic rename
    std::fs::rename(&temp_dest, destination)?;
    Ok(())
}

/// Fetches the live snapshot date/version from Geofabrik HTTP headers (Last-Modified).
pub async fn fetch_snapshot_version(region_path: &str) -> String {
    let url = resolve_pbf_url(region_path);
    let client = reqwest::Client::builder()
        .user_agent("AtlasMirror/1.0 (LP-0018 Evaluator)")
        .build()
        .unwrap_or_else(|_| reqwest::Client::new());

    if let Ok(resp) = client.head(&url).send().await {
        if let Some(lm) = resp
            .headers()
            .get("last-modified")
            .and_then(|h| h.to_str().ok())
        {
            if let Ok(dt) = parse_last_modified_date(lm) {
                return dt;
            }
        }
    }

    current_date_string()
}

fn parse_last_modified_date(lm: &str) -> Result<String, ()> {
    let parts: Vec<&str> = lm.split_whitespace().collect();
    if parts.len() >= 4 {
        let day: u32 = parts[1].parse().map_err(|_| ())?;
        let mon = match parts[2] {
            "Jan" => 1,
            "Feb" => 2,
            "Mar" => 3,
            "Apr" => 4,
            "May" => 5,
            "Jun" => 6,
            "Jul" => 7,
            "Aug" => 8,
            "Sep" => 9,
            "Oct" => 10,
            "Nov" => 11,
            "Dec" => 12,
            _ => return Err(()),
        };
        let year: u32 = parts[3].parse().map_err(|_| ())?;
        return Ok(format!("{:04}-{:02}-{:02}", year, mon, day));
    }
    Err(())
}

#[allow(clippy::manual_is_multiple_of)]
fn current_date_string() -> String {
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let days = secs / 86400;
    let mut y = 1970u64;
    let mut d = days;
    loop {
        let leap = (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;
        let days_in_year = if leap { 366 } else { 365 };
        if d < days_in_year {
            break;
        }
        d -= days_in_year;
        y += 1;
    }
    let leap = (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;
    let month_days = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    let mut m = 0usize;
    for md in &month_days {
        if d < *md {
            break;
        }
        d -= *md;
        m += 1;
    }
    format!("{:04}-{:02}-{:02}", y, m + 1, d + 1)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_all_72_regions_canonical_url_resolution() {
        let bytes = include_bytes!("../../metadata/regions.json");
        let val: serde_json::Value =
            serde_json::from_slice(bytes).expect("Failed to parse metadata/regions.json");
        let regions = val
            .get("regions")
            .and_then(|r| r.as_array())
            .expect("metadata/regions.json must contain 'regions' array");

        assert_eq!(
            regions.len(),
            72,
            "Expected exactly 72 closed-set regions in catalog"
        );

        for r in regions {
            let path = r
                .get("path")
                .and_then(|p| p.as_str())
                .expect("Region missing path");
            let expected_pbf = r
                .get("geofabrik_url")
                .and_then(|u| u.as_str())
                .expect("Region missing geofabrik_url");
            let expected_md5 = r
                .get("md5_url")
                .and_then(|u| u.as_str())
                .expect("Region missing md5_url");

            let resolved_pbf = resolve_pbf_url(path);
            let resolved_md5 = resolve_md5_url(path);

            assert_eq!(
                resolved_pbf, expected_pbf,
                "PBF URL mismatch for region '{}'",
                path
            );
            assert_eq!(
                resolved_md5, expected_md5,
                "MD5 URL mismatch for region '{}'",
                path
            );

            assert!(
                resolved_pbf.starts_with("https://download.geofabrik.de/"),
                "PBF URL must be HTTPS canonical download.geofabrik.de for '{}'",
                path
            );
            assert!(
                resolved_pbf.ends_with("-latest.osm.pbf"),
                "PBF URL must end with -latest.osm.pbf for '{}'",
                path
            );
            assert_eq!(
                resolved_md5,
                format!("{}.md5", resolved_pbf),
                "MD5 URL must match PBF URL + .md5 for '{}'",
                path
            );
        }
    }
}
