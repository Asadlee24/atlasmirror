# Local LEZ Sequencer & SPEL Registry Evidence

This document details the environment, tooling, pinned upstream revisions, commands, and current execution status for running the SPEL OSM Registry on a local Logos Execution Zone (LEZ) standalone sequencer.

---

## 1. Upstream Frameworks & Revisions

| Component | Repository | Pinned Branch/Tag | Description |
|---|---|---|---|
| **SPEL Framework** | [`logos-co/spel`](https://github.com/logos-co/spel) | `main` | Smart contract framework for Logos Execution Zone (RISC Zero zkVM based) |
| **LEZ Sequencer** | [`logos-blockchain/logos-execution-zone`](https://github.com/logos-blockchain/logos-execution-zone) | `main` | Execution engine and standalone sequencer service |

---

## 2. Program Build & Deployment Commands

### Step 1: Build the SPEL OSM Registry Program
```bash
cd osm-registry
# Builds the RISC Zero guest binary and core crate
cargo build --release
# Generates the official SPEL IDL
cargo run --bin generate_idl
```

### Step 2: Start the Standalone LEZ Sequencer
```bash
git clone https://github.com/logos-blockchain/logos-execution-zone.git
cd logos-execution-zone
RUST_LOG=info cargo run --features standalone -p sequencer_service lez/sequencer/service/configs/debug
# Sequencer listens on http://127.0.0.1:9944
```

### Step 3: Deploy the Program to Sequencer
```bash
cd osm-registry
# Using SPEL deployment CLI
spel-cli deploy \
  --sequencer-url http://127.0.0.1:9944 \
  --program-binary target/riscv32im-risc0-zkvm-elf/release/osm_registry \
  --keypair ~/.logos/dev-keypair.json
```

### Step 4: Submit Initialize & Register Transactions
```bash
# Initialize registry
spel-cli tx call \
  --sequencer-url http://127.0.0.1:9944 \
  --program-id <DEPLOYED_PROGRAM_ID> \
  --instruction initialize

# Register region
spel-cli tx call \
  --sequencer-url http://127.0.0.1:9944 \
  --program-id <DEPLOYED_PROGRAM_ID> \
  --instruction register_region \
  --args '{"region":"asia/pakistan","parent":null,"level":"country","cid":"bafybei...","source_url":"https://download.geofabrik.de/asia/pakistan-latest.osm.pbf","checksum":"59227227dab323be9d50da2fbdef2c64","version":"2026-09-18","timestamp":1726700000}'
```

---

## 3. Current Execution Status & Environment Blockers

> [!WARNING]
> **Status: NOT_VERIFIED (LEZ Sequencer Absent)**
> In the current execution environment (Windows host without an active background LEZ sequencer process):
> - The LEZ standalone sequencer service is **not running**.
> - The SPEL deployment CLI (`spel-cli`) is not connected to a live node.
> - Therefore, **no blockchain transaction IDs or live program IDs are claimed**.
> - Tests in `tests/integration/test_lez_registry_real.py` will report `BLOCKED` with exit code 2 until a live sequencer is started.
>
> Simulation is strictly prohibited. Transaction IDs will only be populated when captured from a genuine live LEZ sequencer run.
