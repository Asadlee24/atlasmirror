# SPEL On-Chain Registry Specification

The AtlasMirror on-chain registry is implemented as an LEZ program using the **SPEL framework**. It maintains an immutable index of verified OpenStreetMap snapshots hosted on Logos Storage.

---

## State & Account Design

### 1. Program Derived Addresses (PDAs)

To ensure deterministic, trustless lookups, account keys are derived from predictable seeds:

1. **Global Registry State Account**:
   - Seed: `[program_id, "state"]`
   - Stores global registry statistics, admin authority (if any), and total registered region count.

2. **Region Entry Account**:
   - Seed: `[program_id, "region", region_path]`
   - Derived using the canonical Geofabrik path (e.g. `"asia/pakistan"`, `"us/california"`).
   - Guarantees that each region has exactly one canonical on-chain state record.

3. **CID Lookup Index Account**:
   - Seed: `[program_id, "cid", cid_bytes]`
   - Maps a storage CID directly to its associated region path.

4. **Parent Index Account**:
   - Seed: `[program_id, "parent", parent_path]`
   - Maintains an index of child subregions under a decomposed parent country (e.g. `"us"` -> `["us/california", "us/texas", ...]`).

---

## Data Structures

```rust
#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq)]
pub enum RegionLevel {
    Country,
    Subregion,
}

#[account_type]
#[derive(BorshSerialize, BorshDeserialize, Clone, Debug)]
pub struct RegionRecord {
    pub region: String,          // Bounded <= 64 bytes (e.g. "asia/pakistan")
    pub parent: Option<String>,  // Bounded <= 64 bytes (e.g. Some("us") or None)
    pub level: RegionLevel,      // Country or Subregion
    pub cid: String,             // Logos Storage CID, bounded <= 128 bytes
    pub source_url: String,      // Canonical Geofabrik URL, bounded <= 256 bytes
    pub checksum: String,        // MD5 hex string, exactly 32 bytes
    pub version: String,         // Snapshot date/version string, <= 32 bytes
    pub hosted: bool,            // true if active on Logos Storage
    pub timestamp: u64,          // Unix timestamp in seconds
}
```

---

## Instructions

### 1. `initialize`
Initializes the global state account.
- **Signer**: Deployer / Owner.
- **Accounts**:
  - `state`: `#[account(init, pda = literal("state"))]`
  - `owner`: `#[account(signer)]`

### 2. `register_region`
Registers or updates a single verified region.
- **Validation**:
  - Region string length `1 <= len <= 64`.
  - Level must be valid `Country` or `Subregion`.
  - If `level == Subregion`, `parent` must not be `None`.
  - If `level == Country`, `parent` must be `None`.
  - CID must not be empty.
  - Checksum must be 32 ASCII hexadecimal characters.
  - Timestamp must be monotonically increasing for subsequent updates to the same region.
- **Accounts**:
  - `region_account`: `#[account(mut, pda = arg("region"))]`
  - `cid_account`: `#[account(mut, pda = arg("cid"))]`
  - `signer`: `#[account(signer)]`

### 3. `batch_register`
Atomically registers up to 50 region records in a single transaction.
- **Maximum Batch Size**: `MAX_BATCH = 50`.
- Protects against transaction gas/cycle limits while supporting bulk hosting flows.
- Validates all records before state transition; any invalid record causes atomic reversion.

---

## IDL Generation

The SPEL IDL is generated at compile time using:
```rust
spel_framework::generate_idl!("../methods/guest/src/bin/osm_registry.rs");
```
The resulting JSON IDL is committed at `osm-registry/idl/osm_registry.json`.
