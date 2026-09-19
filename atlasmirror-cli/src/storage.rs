use std::path::Path;
use std::time::Duration;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum StorageError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Logos Storage endpoint unavailable on {0}: {1}")]
    EndpointUnavailable(String, String),
    #[error("Logos Storage upload failed after {attempts} attempts: {last_error}")]
    UploadExhausted { attempts: u32, last_error: String },
    #[error("Logos Storage download failed for CID '{cid}' after {attempts} attempts: {last_error}")]
    DownloadExhausted { cid: String, attempts: u32, last_error: String },
    #[error("Protocol error from Logos Storage: {0}")]
    Protocol(String),
}

/// Client for interacting with the official Logos Storage daemon / module.
pub struct LogosStorageClient {
    endpoint: String,
    max_retries: u32,
    base_backoff_ms: u64,
}

impl LogosStorageClient {
    pub fn new(endpoint: Option<&str>, max_retries: u32, base_backoff_ms: u64) -> Self {
        Self {
            endpoint: endpoint.unwrap_or("http://127.0.0.1:5001").to_string(),
            max_retries,
            base_backoff_ms,
        }
    }

    /// Uploads a local file to Logos Storage using the official uploadUrl endpoint with exponential backoff.
    pub async fn put(&self, file_path: &Path) -> Result<String, StorageError> {
        if !file_path.exists() {
            return Err(StorageError::Io(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("File not found: {}", file_path.display()),
            )));
        }

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(300))
            .build()
            .map_err(|e| StorageError::Protocol(e.to_string()))?;

        let mut attempt = 0;
        let mut last_error = String::new();

        while attempt < self.max_retries {
            attempt += 1;

            let url = format!("{}/api/v0/storage/upload", self.endpoint);
            let file_bytes = std::fs::read(file_path)?;

            let res = client
                .post(&url)
                .header("Content-Type", "application/octet-stream")
                .body(file_bytes)
                .send()
                .await;

            match res {
                Ok(resp) if resp.status().is_success() => {
                    let body: serde_json::Value = resp
                        .json()
                        .await
                        .map_err(|e| StorageError::Protocol(e.to_string()))?;

                    if let Some(cid) = body.get("cid").and_then(|c| c.as_str()) {
                        return Ok(cid.to_string());
                    } else {
                        return Err(StorageError::Protocol("Missing CID in storage response".to_string()));
                    }
                }
                Ok(resp) => {
                    last_error = format!("HTTP error {}", resp.status());
                }
                Err(e) => {
                    last_error = e.to_string();
                }
            }

            // Exponential backoff with jitter
            let backoff = Duration::from_millis(
                self.base_backoff_ms * 2u64.pow(attempt - 1) + (rand_jitter() % 50),
            );
            tokio::time::sleep(backoff).await;
        }

        Err(StorageError::UploadExhausted {
            attempts: self.max_retries,
            last_error,
        })
    }

    /// Downloads a file by CID from Logos Storage to the destination path.
    pub async fn get(&self, cid: &str, destination: &Path) -> Result<(), StorageError> {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(300))
            .build()
            .map_err(|e| StorageError::Protocol(e.to_string()))?;

        let mut attempt = 0;
        let mut last_error = String::new();

        let temp_dest = destination.with_extension("part");

        while attempt < self.max_retries {
            attempt += 1;

            let url = format!("{}/api/v0/storage/download?cid={}", self.endpoint, cid);
            let res = client.get(&url).send().await;

            match res {
                Ok(resp) if resp.status().is_success() => {
                    let bytes = resp
                        .bytes()
                        .await
                        .map_err(|e| StorageError::Protocol(e.to_string()))?;

                    std::fs::write(&temp_dest, bytes)?;
                    std::fs::rename(&temp_dest, destination)?;
                    return Ok(());
                }
                Ok(resp) => {
                    last_error = format!("HTTP error {}", resp.status());
                }
                Err(e) => {
                    last_error = e.to_string();
                }
            }

            let backoff = Duration::from_millis(
                self.base_backoff_ms * 2u64.pow(attempt - 1) + (rand_jitter() % 50),
            );
            tokio::time::sleep(backoff).await;
        }

        if temp_dest.exists() {
            let _ = std::fs::remove_file(&temp_dest);
        }

        Err(StorageError::DownloadExhausted {
            cid: cid.to_string(),
            attempts: self.max_retries,
            last_error,
        })
    }

    /// Checks the status and availability of a CID in Logos Storage.
    pub async fn status(&self, cid: &str) -> Result<serde_json::Value, StorageError> {
        let client = reqwest::Client::new();
        let url = format!("{}/api/v0/storage/status?cid={}", self.endpoint, cid);

        let resp = client
            .get(&url)
            .send()
            .await
            .map_err(|e| StorageError::EndpointUnavailable(self.endpoint.clone(), e.to_string()))?;

        resp.json()
            .await
            .map_err(|e| StorageError::Protocol(e.to_string()))
    }
}

fn rand_jitter() -> u64 {
    use std::time::SystemTime;
    SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.subsec_nanos() as u64 % 50)
        .unwrap_or(10)
}
