# Local LEZ Sequencer & SPEL Registry Evidence

This document details the upstream tooling, build and deployment workflow, and current execution status for running the SPEL OSM Registry against the Logos Execution Zone (LEZ) standalone sequencer.

---

## 1. Upstream Frameworks & Revisions

| Component | Repository | Source Reference |
|---|---|---|
| **SPEL Framework** | [`logos-co/spel`](https://github.com/logos-co/spel) | `scripts/smoke-test.sh`, `scripts/init-e2e-test.sh` |
| **LEZ Sequencer** | [`logos-blockchain/logos-execution-zone`](https://github.com/logos-blockchain/logos-execution-zone) | `lez/sequencer/service/configs/debug` |

---

## 2. Official SPEL Build, Deploy & Execution Workflow

All interaction is handled through the SPEL build tooling and generated CLI rather than custom REST endpoints.

### Step 1: Start the LEZ Standalone Sequencer
```bash
git clone https://github.com/logos-blockchain/logos-execution-zone.git
cd logos-execution-zone
RUST_LOG=info cargo run --features standalone -p sequencer_service \
  lez/sequencer/service/configs/debug
```

### Step 2: Build Guest Binary & Generate SPEL IDL
```bash
cd osm-registry
make build
make idl
# Produces: idl/osm_registry.json
```

### Step 3: Deploy Program via SPEL Tooling
```bash
# Deploys compiled guest binary to sequencer and captures returned Program ID
spel deploy \
  --sequencer-url http://127.0.0.1:9944 \
  --keypair ~/.logos/dev-keypair.json
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
  --cid "bafybei..." \
  --source-url "https://download.geofabrik.de/china/henan-latest.osm.pbf" \
  --checksum "49134316..." \
  --version "2026-09-19" \
  --timestamp 1726700000

# Query On-Chain Registry Account / State
spel inspect --program-id <PROGRAM_ID> --account <REGISTRY_PDA>
```

---

## 3. Current Execution Status

> [!WARNING]
> **Status: BLOCKED**
> The LEZ standalone sequencer service is not currently running, and the `spel` CLI is not installed in the local environment.
> Consequently:
> - Program ID: **BLOCKED** (no deploy transaction executed)
> - Transaction ID: **BLOCKED** (no sequencer transaction submitted)
> - Queried on-chain state: **BLOCKED** (no on-chain account state exists)
>
> In accordance with LP-0018 rules, no simulated transaction IDs (`0xlez_tx_...`) or fake program IDs are generated.
