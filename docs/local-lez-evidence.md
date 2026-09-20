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
- **Program ID (u32 Array)**: `[1108401340, 224902513, 3719279011, 2256696779, 2279479750, 2288278838, 1677050569, 1334542228]`
- **Program ID (Hex)**: `bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f`
- **Deployment Transaction Hash**: `aeb52c595c860392504e790e32d41e8bb84be03141bfea514405465873f5badd`
- **Included in Block**: `16926`

### Verified Region Registration Transaction
- **Target State Account**: `Public/T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci`
- **Registered Region**: `china/henan` (Subregion under `china`)
- **Transaction Hash**: `dbf2fd2af1c54454d50613bbe9b57e6db2f06a311f774249cd77943078c8e487`
- **Included in Block**: `16927`
- **Status**: `TransactionExecuted` (Finalized)

### Verified On-Chain State Query
- **Program Owner**: `bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f`
- **Total Registered Regions**: `1`
- **Last Updated Timestamp**: `1789905600`
- **State Data**:
  ```text
  REGION_RECORD: region=china/henan, parent=Some("china"), level=Subregion, cid=zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny, source_url=https://download.geofabrik.de/asia/china/henan-latest.osm.pbf, checksum=0055ebfc7f14585c56d53a88062d5814, version=2026-09-20, hosted=true, timestamp=1789905600
  ```
Full audit log is preserved at [evidence/henan-e2e.log](file:///c:/Users/Aftab/Desktop/atlasmirror/evidence/henan-e2e.log) and [evidence/henan-testnet-query.log](file:///c:/Users/Aftab/Desktop/atlasmirror/evidence/henan-testnet-query.log).
