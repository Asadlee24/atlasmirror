# Logos Testnet 0.3 Deployment Guide

This document details the deployment, configuration, and verification of AtlasMirror on **Logos Testnet 0.3** (the canonical Logos Execution Zone).

---

## Deployment Configuration

- **Target Network**: Logos Testnet 0.3
- **LEZ RPC Endpoint**: Configurable via CLI `--endpoint` or environment variable `LEZ_RPC_URL` (default: official Testnet 0.3 RPC).
- **Logos Storage Gateway**: Configurable via `--storage-endpoint` or `LOGOS_STORAGE_URL`.
- **Program ID**: Generated upon deployment using `scripts/testnet-deploy.sh`.

---

## Deployment Steps

1. **Build Program Guest Binary**:
   ```bash
   cd osm-registry
   cargo build --release --target riscv32im-risc0-zkvm-elf
   ```

2. **Generate SPEL IDL**:
   ```bash
   cargo run --bin generate_idl
   # IDL emitted to osm-registry/idl/osm_registry.json
   ```

3. **Deploy to Testnet 0.3**:
   ```bash
   bash scripts/testnet-deploy.sh --network testnet03 --keyfile ~/.logos/id.json
   ```

4. **Verify On-Chain State**:
   ```bash
   atlasmirror registry program-id
   atlasmirror lookup region asia/pakistan
   ```
