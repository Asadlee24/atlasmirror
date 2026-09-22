//! Core types and validation logic for the AtlasMirror OSM on-chain registry.

use borsh::{BorshDeserialize, BorshSerialize};
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Maximum number of region records allowed in a single batch registration.
pub const MAX_BATCH_SIZE: usize = 50;

/// Maximum length of a region identifier path (e.g. "asia/pakistan").
pub const MAX_REGION_PATH_LEN: usize = 64;

/// Maximum length of a Content Identifier (CID).
pub const MAX_CID_LEN: usize = 128;

/// Maximum length of a canonical source URL.
pub const MAX_SOURCE_URL_LEN: usize = 256;

/// Maximum length of a version/date string.
pub const MAX_VERSION_LEN: usize = 32;

/// Exactly 32 hexadecimal characters for an MD5 checksum.
pub const MD5_CHECKSUM_LEN: usize = 32;

#[derive(Error, Debug, PartialEq, Eq, Clone, Serialize, Deserialize)]
pub enum RegistryError {
    #[error("Region path cannot be empty or exceed {MAX_REGION_PATH_LEN} characters")]
    InvalidRegionPath,
    #[error("Parent path exceeds {MAX_REGION_PATH_LEN} characters")]
    InvalidParentPath,
    #[error("CID cannot be empty or exceed {MAX_CID_LEN} characters")]
    InvalidCid,
    #[error("Source URL cannot be empty or exceed {MAX_SOURCE_URL_LEN} characters")]
    InvalidSourceUrl,
    #[error("Checksum must be exactly {MD5_CHECKSUM_LEN} hexadecimal characters")]
    InvalidChecksum,
    #[error("Version string cannot be empty or exceed {MAX_VERSION_LEN} characters")]
    InvalidVersion,
    #[error("Country level regions cannot have a parent")]
    CountryMustNotHaveParent,
    #[error("Subregion level regions must have a parent")]
    SubregionMustHaveParent,
    #[error("Batch size {0} exceeds maximum limit of {MAX_BATCH_SIZE}")]
    BatchTooLarge(usize),
    #[error("Batch cannot be empty")]
    EmptyBatch,
    #[error("Update timestamp {new_ts} must be greater than existing timestamp {existing_ts}")]
    TimestampRegression { existing_ts: u64, new_ts: u64 },
    #[error("Region '{0}' is already registered and overwrite was not requested")]
    AlreadyExists(String),
    #[error("Region '{0}' not found in registry")]
    NotFound(String),
    #[error("Unauthorized signer")]
    Unauthorized,
}

/// Hierarchy level of a region within the non-overlapping predefined set.
#[derive(
    BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq,
)]
pub enum RegionLevel {
    Country,
    Subregion,
}

impl std::fmt::Display for RegionLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RegionLevel::Country => write!(f, "country"),
            RegionLevel::Subregion => write!(f, "subregion"),
        }
    }
}

/// An immutable or updated on-chain record representing a verified OSM snapshot.
#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct RegionRecord {
    /// Canonical Geofabrik path (e.g. "asia/pakistan", "us/california").
    pub region: String,
    /// Parent region if subregion (e.g. Some("us")), or None for countries.
    pub parent: Option<String>,
    /// Hierarchy level.
    pub level: RegionLevel,
    /// Content Identifier in Logos Storage.
    pub cid: String,
    /// Canonical Geofabrik snapshot download URL.
    pub source_url: String,
    /// Published 32-character hexadecimal MD5 checksum.
    pub checksum: String,
    /// Version or snapshot date (e.g. "2026-09-19").
    pub version: String,
    /// Whether this region is actively hosted in Logos Storage.
    pub hosted: bool,
    /// Monotonic timestamp in Unix seconds.
    pub timestamp: u64,
}

/// Instruction arguments for registering a single region.
#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct RegisterRegionArgs {
    pub region: String,
    pub parent: Option<String>,
    pub level: RegionLevel,
    pub cid: String,
    pub source_url: String,
    pub checksum: String,
    pub version: String,
    pub hosted: bool,
    pub timestamp: u64,
}

impl RegisterRegionArgs {
    /// Validates all fields according to protocol constraints.
    pub fn validate(&self) -> Result<(), RegistryError> {
        if self.region.is_empty() || self.region.len() > MAX_REGION_PATH_LEN {
            return Err(RegistryError::InvalidRegionPath);
        }

        if let Some(ref p) = self.parent {
            if p.is_empty() || p.len() > MAX_REGION_PATH_LEN {
                return Err(RegistryError::InvalidParentPath);
            }
        }

        match self.level {
            RegionLevel::Country => {
                if self.parent.is_some() {
                    return Err(RegistryError::CountryMustNotHaveParent);
                }
            }
            RegionLevel::Subregion => {
                if self.parent.is_none() {
                    return Err(RegistryError::SubregionMustHaveParent);
                }
            }
        }

        if self.cid.is_empty() || self.cid.len() > MAX_CID_LEN {
            return Err(RegistryError::InvalidCid);
        }

        if self.source_url.is_empty() || self.source_url.len() > MAX_SOURCE_URL_LEN {
            return Err(RegistryError::InvalidSourceUrl);
        }

        if self.checksum.len() != MD5_CHECKSUM_LEN
            || !self.checksum.chars().all(|c| c.is_ascii_hexdigit())
        {
            return Err(RegistryError::InvalidChecksum);
        }

        if self.version.is_empty() || self.version.len() > MAX_VERSION_LEN {
            return Err(RegistryError::InvalidVersion);
        }

        Ok(())
    }

    /// Converts into a canonical `RegionRecord`.
    pub fn into_record(self) -> RegionRecord {
        RegionRecord {
            region: self.region,
            parent: self.parent,
            level: self.level,
            cid: self.cid,
            source_url: self.source_url,
            checksum: self.checksum.to_ascii_lowercase(),
            version: self.version,
            hosted: self.hosted,
            timestamp: self.timestamp,
        }
    }
}

/// Instruction arguments for batch registration of multiple regions.
#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub struct BatchRegisterArgs {
    pub records: Vec<RegisterRegionArgs>,
}

impl BatchRegisterArgs {
    /// Validates the batch size and each individual record.
    pub fn validate(&self) -> Result<(), RegistryError> {
        if self.records.is_empty() {
            return Err(RegistryError::EmptyBatch);
        }
        if self.records.len() > MAX_BATCH_SIZE {
            return Err(RegistryError::BatchTooLarge(self.records.len()));
        }
        for record in &self.records {
            record.validate()?;
        }
        Ok(())
    }
}

/// Global registry state account.
#[derive(
    BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, Default, PartialEq, Eq,
)]
pub struct GlobalRegistryState {
    /// Total number of unique registered regions.
    pub total_regions: u64,
    /// Timestamp of last registration.
    pub last_updated: u64,
}

/// Complete on-chain registry state stored in the program's account shard.
#[derive(
    BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, Default, PartialEq, Eq,
)]
pub struct RegistryState {
    /// Total number of unique registered regions.
    pub total_regions: u64,
    /// Timestamp of last registration.
    pub last_updated: u64,
    /// Collection of all registered region records.
    pub records: Vec<RegionRecord>,
}

/// Instructions supported by the OSM Registry guest program.
#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
pub enum RegistryInstruction {
    Initialize,
    RegisterRegion(RegisterRegionArgs),
    BatchRegister(BatchRegisterArgs),
}

/// Entry point / state transition function for the SPEL OSM Registry.
pub fn process_instruction(
    instruction_data: &[u8],
    state: &mut GlobalRegistryState,
    records: &mut Vec<RegionRecord>,
) -> Result<(), RegistryError> {
    let instruction = RegistryInstruction::try_from_slice(instruction_data)
        .map_err(|_| RegistryError::InvalidRegionPath)?;

    match instruction {
        RegistryInstruction::Initialize => {
            state.total_regions = 0;
            state.last_updated = 0;
            Ok(())
        }
        RegistryInstruction::RegisterRegion(args) => {
            args.validate()?;
            let ts = args.timestamp;

            if let Some(existing) = records.iter_mut().find(|r| r.region == args.region) {
                if ts <= existing.timestamp {
                    return Err(RegistryError::TimestampRegression {
                        existing_ts: existing.timestamp,
                        new_ts: ts,
                    });
                }
                *existing = args.into_record();
            } else {
                records.push(args.into_record());
                state.total_regions += 1;
            }

            state.last_updated = ts;
            Ok(())
        }
        RegistryInstruction::BatchRegister(batch) => {
            batch.validate()?;

            for args in batch.records {
                let ts = args.timestamp;
                if let Some(existing) = records.iter_mut().find(|r| r.region == args.region) {
                    if ts <= existing.timestamp {
                        return Err(RegistryError::TimestampRegression {
                            existing_ts: existing.timestamp,
                            new_ts: ts,
                        });
                    }
                    *existing = args.into_record();
                } else {
                    records.push(args.into_record());
                    state.total_regions += 1;
                }
                if ts > state.last_updated {
                    state.last_updated = ts;
                }
            }

            Ok(())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_country_record() {
        let args = RegisterRegionArgs {
            region: "asia/pakistan".to_string(),
            parent: None,
            level: RegionLevel::Country,
            cid: "bafybeic7vj2k...".to_string(),
            source_url: "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf".to_string(),
            checksum: "378df25f824177ebcbe9aa11d88bbd6b".to_string(),
            version: "2026-09-19".to_string(),
            hosted: true,
            timestamp: 1726747200,
        };
        assert!(args.validate().is_ok());
    }

    #[test]
    fn test_valid_subregion_record() {
        let args = RegisterRegionArgs {
            region: "us/california".to_string(),
            parent: Some("us".to_string()),
            level: RegionLevel::Subregion,
            cid: "bafybeid6xk1m...".to_string(),
            source_url: "https://download.geofabrik.de/north-america/us/california-latest.osm.pbf"
                .to_string(),
            checksum: "0123456789abcdef0123456789abcdef".to_string(),
            version: "2026-09-19".to_string(),
            hosted: true,
            timestamp: 1726747200,
        };
        assert!(args.validate().is_ok());
    }

    #[test]
    fn test_country_with_parent_fails() {
        let args = RegisterRegionArgs {
            region: "europe/germany".to_string(),
            parent: Some("europe".to_string()),
            level: RegionLevel::Country,
            cid: "bafybeih...".to_string(),
            source_url: "https://download.geofabrik.de/europe/germany-latest.osm.pbf".to_string(),
            checksum: "e9c0c1b7a2d61d87e025b9059f131a42".to_string(),
            version: "2026-09-19".to_string(),
            hosted: true,
            timestamp: 1726747200,
        };
        assert_eq!(
            args.validate(),
            Err(RegistryError::CountryMustNotHaveParent)
        );
    }

    #[test]
    fn test_subregion_without_parent_fails() {
        let args = RegisterRegionArgs {
            region: "us/texas".to_string(),
            parent: None,
            level: RegionLevel::Subregion,
            cid: "bafybeie...".to_string(),
            source_url: "https://download.geofabrik.de/north-america/us/texas-latest.osm.pbf"
                .to_string(),
            checksum: "11223344556677889900aabbccddeeff".to_string(),
            version: "2026-09-19".to_string(),
            hosted: true,
            timestamp: 1726747200,
        };
        assert_eq!(args.validate(), Err(RegistryError::SubregionMustHaveParent));
    }

    #[test]
    fn test_invalid_checksum_length() {
        let args = RegisterRegionArgs {
            region: "asia/japan".to_string(),
            parent: None,
            level: RegionLevel::Country,
            cid: "bafybei...".to_string(),
            source_url: "https://download.geofabrik.de/asia/japan-latest.osm.pbf".to_string(),
            checksum: "short_hash".to_string(),
            version: "2026-09-19".to_string(),
            hosted: true,
            timestamp: 1726747200,
        };
        assert_eq!(args.validate(), Err(RegistryError::InvalidChecksum));
    }

    #[test]
    fn test_batch_limit_exceeded() {
        let valid_item = RegisterRegionArgs {
            region: "asia/pakistan".to_string(),
            parent: None,
            level: RegionLevel::Country,
            cid: "bafybeic7vj2k...".to_string(),
            source_url: "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf".to_string(),
            checksum: "378df25f824177ebcbe9aa11d88bbd6b".to_string(),
            version: "2026-09-19".to_string(),
            hosted: true,
            timestamp: 1726747200,
        };
        let batch = BatchRegisterArgs {
            records: vec![valid_item; 51],
        };
        assert_eq!(batch.validate(), Err(RegistryError::BatchTooLarge(51)));
    }
}
