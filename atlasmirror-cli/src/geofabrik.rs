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

/// Resolves the canonical Geofabrik PBF URL for a region path.
pub fn resolve_pbf_url(region_path: &str) -> String {
    format!("https://download.geofabrik.de/{}-latest.osm.pbf", region_path)
}

/// Resolves the canonical Geofabrik MD5 URL for a region path.
pub fn resolve_md5_url(region_path: &str) -> String {
    format!("https://download.geofabrik.de/{}-latest.osm.pbf.md5", region_path)
}

/// Fetches and parses the canonical MD5 checksum published by Geofabrik.
pub async fn fetch_published_md5(region_path: &str) -> Result<String, GeofabrikError> {
    let url = resolve_md5_url(region_path);
    let client = reqwest::Client::new();
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
    let client = reqwest::Client::new();
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
