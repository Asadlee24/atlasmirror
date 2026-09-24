#![allow(dead_code)]

use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum StorageError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Logos Storage module / logoscore binary unavailable: {0}")]
    BinaryUnavailable(String),
    #[error("Logos Storage uploadUrl failed: {0}")]
    UploadFailed(String),
    #[error("Logos Storage downloadToUrl failed for CID '{cid}': {last_error}")]
    DownloadFailed { cid: String, last_error: String },
    #[error("Protocol error from Logos Storage module: {0}")]
    Protocol(String),
}

/// Client for interacting with the official Logos Storage module via logoscore IPC / CLI.
pub struct LogosStorageClient {
    logoscore_bin: PathBuf,
    chunk_size: usize,
    max_retries: u32,
    base_backoff_ms: u64,
}

impl LogosStorageClient {
    pub fn new(custom_bin: Option<&str>, max_retries: u32, base_backoff_ms: u64) -> Self {
        let bin_path = if let Some(b) = custom_bin {
            PathBuf::from(b)
        } else if let Ok(env_b) = std::env::var("LOGOSCORE_BIN") {
            PathBuf::from(env_b)
        } else if Path::new("./logos/bin/logoscore").exists() {
            PathBuf::from("./logos/bin/logoscore")
        } else if Path::new("/root/atlasmirror_vps/bin/logoscore").exists() {
            PathBuf::from("/root/atlasmirror_vps/bin/logoscore")
        } else {
            PathBuf::from("logoscore")
        };

        Self {
            logoscore_bin: bin_path,
            chunk_size: 262144, // 256 KB standard chunk
            max_retries,
            base_backoff_ms,
        }
    }

    /// Uploads a local file to Logos Storage using the official uploadUrl endpoint.
    /// Captures the resulting CID from the storageUploadDone event or manifests().
    pub async fn put(&self, file_path: &Path) -> Result<String, StorageError> {
        if !file_path.exists() {
            return Err(StorageError::Io(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("File not found: {}", file_path.display()),
            )));
        }

        let abs_path = if file_path.is_relative() {
            std::env::current_dir()?.join(file_path)
        } else {
            file_path.to_path_buf()
        };

        let attempts = self.max_retries.max(1);
        let mut last_err = String::new();

        for attempt in 0..attempts {
            if attempt > 0 {
                let delay = self.base_backoff_ms * (1 << (attempt - 1));
                tokio::time::sleep(Duration::from_millis(delay)).await;
            }

            // Spawn watcher for storageUploadDone event
            let watcher_file = std::env::temp_dir().join(format!(
                "upload-event-{}-{}.json",
                std::process::id(),
                attempt
            ));
            let watcher = Command::new(&self.logoscore_bin)
                .arg("watch")
                .arg("storage_module")
                .arg("--event")
                .arg("storageUploadDone")
                .arg("--json")
                .stdout(std::fs::File::create(&watcher_file)?)
                .spawn()
                .ok();

            tokio::time::sleep(Duration::from_millis(500)).await;

            // Call official uploadUrl(filePath, chunkSize)
            let call_res = Command::new(&self.logoscore_bin)
                .arg("call")
                .arg("storage_module")
                .arg("uploadUrl")
                .arg(abs_path.to_str().unwrap_or_default())
                .arg(self.chunk_size.to_string())
                .arg("--json")
                .output();

            let call_res = match call_res {
                Ok(res) => res,
                Err(e) => {
                    if let Some(mut w) = watcher {
                        let _ = w.kill();
                    }
                    let _ = std::fs::remove_file(&watcher_file);
                    last_err = format!("{}: {}", self.logoscore_bin.display(), e);
                    continue;
                }
            };

            if !call_res.status.success() {
                if let Some(mut w) = watcher {
                    let _ = w.kill();
                }
                let _ = std::fs::remove_file(&watcher_file);
                last_err = String::from_utf8_lossy(&call_res.stderr).to_string();
                continue;
            }

            // Wait for storageUploadDone event in watcher file
            let mut real_cid = String::new();
            for _ in 0..60 {
                if watcher_file.exists() {
                    if let Ok(content) = std::fs::read_to_string(&watcher_file) {
                        if let Some(pos) = content.find("\"cid\":") {
                            let rest = &content[pos + 6..];
                            if let Some(start_q) = rest.find('"') {
                                if let Some(end_q) = rest[start_q + 1..].find('"') {
                                    real_cid = rest[start_q + 1..start_q + 1 + end_q].to_string();
                                    if !real_cid.is_empty() {
                                        break;
                                    }
                                }
                            }
                        }
                    }
                }
                tokio::time::sleep(Duration::from_millis(500)).await;
            }

            if let Some(mut w) = watcher {
                let _ = w.kill();
            }
            let _ = std::fs::remove_file(&watcher_file);

            // Fallback: query manifests() if watcher didn't capture CID
            if real_cid.is_empty() {
                if let Ok(m) = self.manifests().await {
                    if let Some(arr) = m
                        .get("result")
                        .and_then(|r| r.get("value"))
                        .and_then(|v| v.as_array())
                    {
                        let target_filename = abs_path
                            .file_name()
                            .and_then(|f| f.to_str())
                            .unwrap_or_default();
                        let target_size = std::fs::metadata(&abs_path)
                            .map(|meta| meta.len())
                            .unwrap_or(0);

                        // Correlate with uploaded file: match filename and size
                        let matched = arr.iter().rev().find(|entry| {
                            let fname = entry
                                .get("filename")
                                .and_then(|s| s.as_str())
                                .unwrap_or_default();
                            let dsize = entry
                                .get("datasetSize")
                                .and_then(|s| s.as_u64())
                                .unwrap_or(0);
                            fname == target_filename && (target_size == 0 || dsize == target_size)
                        }).or_else(|| {
                            // Fallback to filename match
                            arr.iter().rev().find(|entry| {
                                let fname = entry
                                    .get("filename")
                                    .and_then(|s| s.as_str())
                                    .unwrap_or_default();
                                fname == target_filename
                            })
                        });

                        if let Some(entry) = matched {
                            if let Some(cid) = entry.get("cid").and_then(|c| c.as_str()) {
                                real_cid = cid.to_string();
                            }
                        }
                    }
                }
            }

            if !real_cid.is_empty() {
                return Ok(real_cid);
            }

            last_err = "Could not obtain genuine CID from storageUploadDone event or manifests"
                .to_string();
        }

        Err(StorageError::UploadFailed(last_err))
    }

    /// Downloads a file by CID from Logos Storage to the destination path using downloadToUrl.
    pub async fn get(&self, cid: &str, destination: &Path) -> Result<(), StorageError> {
        let abs_dest = if destination.is_relative() {
            std::env::current_dir()?.join(destination)
        } else {
            destination.to_path_buf()
        };
        if let Some(parent) = abs_dest.parent() {
            std::fs::create_dir_all(parent)?;
        }

        let mut last_err = String::new();
        let attempts = self.max_retries.max(1);

        for attempt in 0..attempts {
            if attempt > 0 {
                let delay = self.base_backoff_ms * (1 << (attempt - 1));
                tokio::time::sleep(Duration::from_millis(delay)).await;
            }

            // In LP-0018, retrieval must be possible across nodes (network peer retrieval) as well as locally.
            // On first attempt try peer retrieval (local=false); on retry fallback to local=true.
            let local_flag = if attempt == 0 { "false" } else { "true" };

            let output_res = Command::new(&self.logoscore_bin)
                .arg("call")
                .arg("storage_module")
                .arg("downloadToUrl")
                .arg(cid)
                .arg(abs_dest.to_str().unwrap_or_default())
                .arg(local_flag)
                .arg(self.chunk_size.to_string())
                .arg("--json")
                .output();

            match output_res {
                Ok(output) => {
                    if output.status.success() {
                        // Wait for file to be flushed to disk
                        for _ in 0..30 {
                            if abs_dest.exists()
                                && abs_dest.metadata().map(|m| m.len() > 0).unwrap_or(false)
                            {
                                return Ok(());
                            }
                            tokio::time::sleep(Duration::from_millis(200)).await;
                        }
                    }
                    last_err = String::from_utf8_lossy(&output.stderr).to_string();
                }
                Err(e) => {
                    last_err = format!("{}: {}", self.logoscore_bin.display(), e);
                }
            }

            // If network peer attempt didn't produce file, also try local=true directly
            if local_flag == "false" {
                let fallback = Command::new(&self.logoscore_bin)
                    .arg("call")
                    .arg("storage_module")
                    .arg("downloadToUrl")
                    .arg(cid)
                    .arg(abs_dest.to_str().unwrap_or_default())
                    .arg("true")
                    .arg(self.chunk_size.to_string())
                    .arg("--json")
                    .output();
                if let Ok(out) = fallback {
                    if out.status.success() {
                        for _ in 0..30 {
                            if abs_dest.exists()
                                && abs_dest.metadata().map(|m| m.len() > 0).unwrap_or(false)
                            {
                                return Ok(());
                            }
                            tokio::time::sleep(Duration::from_millis(200)).await;
                        }
                    }
                }
            }
        }

        if abs_dest.exists() && abs_dest.metadata().map(|m| m.len() > 0).unwrap_or(false) {
            Ok(())
        } else {
            Err(StorageError::DownloadFailed {
                cid: cid.to_string(),
                last_error: if last_err.is_empty() {
                    "File was not written to destination by storage module".to_string()
                } else {
                    last_err
                },
            })
        }
    }

    /// Checks if content identified by CID exists in local storage using exists().
    pub async fn exists(&self, cid: &str) -> Result<bool, StorageError> {
        let output = Command::new(&self.logoscore_bin)
            .arg("call")
            .arg("storage_module")
            .arg("exists")
            .arg(cid)
            .arg("--json")
            .output()
            .map_err(|e| {
                StorageError::BinaryUnavailable(format!("{}: {}", self.logoscore_bin.display(), e))
            })?;

        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let v: serde_json::Value = serde_json::from_str(&stdout).unwrap_or_default();
            let exists = v
                .get("result")
                .and_then(|r| r.get("value"))
                .and_then(|val| val.as_bool())
                .unwrap_or(false);
            Ok(exists)
        } else {
            Ok(false)
        }
    }

    /// Queries all stored manifests using manifests().
    pub async fn manifests(&self) -> Result<serde_json::Value, StorageError> {
        let output = Command::new(&self.logoscore_bin)
            .arg("call")
            .arg("storage_module")
            .arg("manifests")
            .arg("--json")
            .output()
            .map_err(|e| {
                StorageError::BinaryUnavailable(format!("{}: {}", self.logoscore_bin.display(), e))
            })?;

        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let v: serde_json::Value =
                serde_json::from_str(&stdout).map_err(|e| StorageError::Protocol(e.to_string()))?;
            Ok(v)
        } else {
            Err(StorageError::Protocol(
                String::from_utf8_lossy(&output.stderr).to_string(),
            ))
        }
    }
}
