# Local LEZ Sequencer & SPEL Registry Evidence

This document details the upstream tooling, build and deployment workflow, and current execution status for running the SPEL OSM Registry against the Logos Execution Zone (LEZ) standalone sequencer.

---

## 1. Upstream Frameworks & Revisions

| Component | Repository | Source Reference |
|---|---|---|
| **SPEL Framework** | [`logos-co/spel`](https://github.com/logos-co/spel) | `scripts/smoke-test.sh`, `scripts/init-e2e-test.sh` |
| **LEZ Sequencer & Wallet** | [`logos-blockchain/logos-execution-zone`](https://github.com/logos-blockchain/logos-execution-zone) | `lez/sequencer/service/configs/debug`, `wallet` CLI |

---

## 2. Official SPEL Build, Deploy & Execution Workflow

Follows `logos-co/spel/scripts/smoke-test.sh` and the official SPEL project scaffold:

### Step 1: Start the LEZ Standalone Sequencer
```bash
git clone https://github.com/logos-blockchain/logos-execution-zone.git
cd logos-execution-zone
RUST_LOG=info cargo run --features standalone -p sequencer_service \
  lez/sequencer/service/configs/debug
```

### Step 2: Build RISC0 Guest Binary & Generate SPEL IDL
```bash
cd osm-registry
# Builds the guest binary via cargo-risczero
cargo risczero build --manifest-path methods/guest/Cargo.toml
# Generates IDL from #[lez_program] annotations
cargo run --bin generate_idl
# Produces: idl/osm_registry.json
```

### Step 3: Deploy Program via LEZ Wallet
```bash
wallet deploy-program target/riscv32im-risc0-zkvm-elf/release/osm_registry
# Captures returned Program ID
```

### Step 4: Execute Transactions via Generated SPEL CLI
```bash
# Initialize Registry
spel --idl idl/osm_registry.json -p <PROGRAM_ID> -- \
  initialize

# Register Region
spel --idl idl/osm_registry.json -p <PROGRAM_ID> -- \
  register-region \
  --region "china/henan" \
  --level "subregion" \
  --cid "<REAL_CID>" \
  --source-url "https://download.geofabrik.de/china/henan-latest.osm.pbf" \
  --checksum "<COMPUTED_MD5>" \
  --version "2026-09-19" \
  --timestamp 1726700000

# Query On-Chain Registry Account / State
spel inspect --program-id <PROGRAM_ID> --account <REGISTRY_PDA>
```

---

## 3. Current Execution Status: VERIFIED ON CANONICAL TESTNET

> [!NOTE]
> **Environment**: Testnet v0.3 release environment with the currently documented LEZ CLI compatibility path targeting v0.2.2.
> **Sequencer URL**: `https://testnet.lez.logos.co`

The AtlasMirror `osm_registry` program has been compiled, wrapped into a `ProgramBinary`, deployed to the canonical Logos testnet, and verified with an on-chain registration transaction and state query.

### Verified Deployment Receipt
- **Program ID (u32 Array)**: `[347481232, 1299102719, 2328279976, 197338152, 796010409, 3372189242, 412881757, 1852548037]`
- **Program ID (Hex)**: `9024b614ffbb6e4da8bbc68a2824c30ba927722f3a86ffc85d139c18c5a36b6e`
- **Deployment Transaction Hash**: `eb12cd28cd4358aa77bf5c617b94f220e36317742d30701bd1c6e7dbf2cee758`
- **Included in Block**: `16907`

### Verified Region Registration Transaction
- **Target State Account**: `Public/4CSAM4M1GtrF1tGMJmnCaipbkHH3kYjsMNmWYs6jJHJQ`
- **Registered Region**: `china/henan` (Subregion under `china`)
- **Transaction Hash**: `8c59838b2b516df84bad7a6086658c37d3ac1ba1bc79c9b53555a971782a7b34`
- **Included in Block**: `16908`
- **Status**: `TransactionExecuted` (Finalized)

### Verified On-Chain State Query
- **Program Owner**: `9024b614ffbb6e4da8bbc68a2824c30ba927722f3a86ffc85d139c18c5a36b6e`
- **Total Registered Regions**: `1`
- **Last Updated Timestamp**: `1726747200`
- **State Data**:
  ```text
  REGION_RECORD: region=china/henan, parent=Some("china"), level=Subregion, cid=zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4, source_url=https://download.geofabrik.de/asia/china/henan-latest.osm.pbf, checksum=378df25f824177ebcbe9aa11d88bbd6b, version=2026-09-19, hosted=true, timestamp=1726747200
  ```
Full audit log is preserved at [evidence/testnet-deployment-and-registration.log](file:///c:/Users/Aftab/Desktop/atlasmirror/evidence/testnet-deployment-and-registration.log).
