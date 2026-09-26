# Logos Testnet v0.3 Upstream Discovery & Specifications

This document records the official, verified network configurations, endpoints, tooling, and command interfaces for **Logos Testnet v0.3** discovered directly from official Logos upstream repositories (`logos-co/logos-docs`, `logos-blockchain/logos-blockchain`, `logos-co/logos-logoscore-cli`).

---

## 1. Canonical Network Endpoints & Identifiers

| Service | Canonical URL / Identifier | Upstream Source |
|---|---|---|
| **Blockchain Dashboard** | `https://testnet.blockchain.logos.co/web/` | `logos-blockchain` release `0.3.0-rc.3` |
| **Blockchain L1 Faucet** | `https://testnet.blockchain.logos.co/web/faucet/` | `logos-blockchain` release `0.3.0-rc.3` |
| **LEZ Sequencer (L2)** | `https://testnet.lez.logos.co` | `docs/lez/get-started/run-lez-wallet-via-cli.md` |
| **LEZ Testnet Faucet (Piñata)** | `wallet pinata claim --to <account_id>` | `docs/lez/get-started/run-lez-wallet-via-cli.md` |
| **Logos Storage Network** | `logos.test` | `docs/storage/get-started/run-logos-storage-node.md` |

---

## 2. Upstream Software Versions & Tags

- **`logos-logoscore-cli` (`logosctl`)**: `0.3.0-rc.3` (Release: [logos-co/logos-logoscore-cli@0.3.0-rc.3](https://github.com/logos-co/logos-logoscore-cli/releases/tag/0.3.0-rc.3))
- **`logos-blockchain`**: `0.3.0-rc.3` (Release: [logos-blockchain/logos-blockchain@0.3.0-rc.3](https://github.com/logos-blockchain/logos-blockchain/releases/tag/0.3.0-rc.3))
- **`logos-execution-zone` (LEZ)**: `v0.2.5-rc3` / `0.3` (Release: [logos-blockchain/logos-execution-zone](https://github.com/logos-blockchain/logos-execution-zone))
- **Storage Module Package**: `storage_module` version `2.1.2`

---

## 3. Tooling Transition: `logosctl` Unified CLI

`logosctl` is the new unified node management CLI that replaces legacy separate scripts (`logoscore`, `lgpm`, `lgpd`).

### Installation
Official installation script:
```bash
export LOGOSCTL_TAG=0.3.0-rc.3
curl -fsSL https://raw.githubusercontent.com/logos-co/logos-docs/main/resources/scripts/install-logosctl.sh | sudo sh
```
Binary is installed to `/usr/local/bin/logosctl`.

### Core `logosctl` Command Mappings

| Action | Legacy / Local Command | `logosctl` v0.3 Command |
|---|---|---|
| **Start Daemon** | `logoscore &` | `logosctl daemon start` |
| **Daemon Status** | `curl localhost:8080/status` | `logosctl daemon status --json` |
| **Refresh Catalog** | `lgpm update` | `logosctl catalog refresh` |
| **Install Module** | `lgpm install storage` | `logosctl package install storage_module --version 2.1.2 --yes` |
| **Load Module** | `logoscore --module storage` | `logosctl module load storage_module` |
| **List Loaded** | `curl ...` | `logosctl ls --loaded` |
| **Storage Init** | custom config | `logosctl call storage_module init @config.json` |
| **Storage Start** | custom daemon | `logosctl call storage_module start` |
| **Storage Upload** | custom API | `logosctl call storage_module uploadUrl <abs_path> 65536` |
| **Storage Download** | custom API | `logosctl call storage_module downloadToUrl <cid> <abs_dest> false 65536` |
| **Storage Manifests** | custom API | `logosctl call storage_module manifests` |
| **Stop Daemon** | `killall logoscore` | `logosctl daemon stop` |

---

## 4. LEZ Wallet & Program Deployment

### Connecting to Canonical Testnet
```bash
wallet change-network testnet
wallet check-health
```
This updates the wallet configuration to connect to `https://testnet.lez.logos.co`.

### Account Funding
New public accounts require native tokens to fund transaction fees:
```bash
wallet account new public
wallet pinata claim --to <account_id>
wallet account get --account-id <account_id>
```

### Program Deployment
```bash
wallet program-loader deploy \
  --elf <path_to_elf_binary> \
  --header <header_account_id> \
  --segments <segment_account_ids...> \
  --payer <funded_account_id>
```

### Transaction Invocation
Transactions must declare fees via `FeeDeclaration` signed by the designated payer:
- Target program: Header account ID
- Shard selector: `ProgramShardSelector::new(header_id, header_id)`
- Nonces: Matched to signer public keys in witness set

---

## 5. Live Testnet Deployment & Execution Verification

The AtlasMirror `osm_registry` guest program has been compiled, deployed, and verified on the canonical Logos Testnet (`https://testnet.lez.logos.co`).

### Deployment Receipt
- **Environment**: Testnet v0.3 release environment with the currently documented LEZ CLI compatibility path targeting v0.2.2
- **Program ID (u32 Array)**: `[1108401340, 224902513, 3719279011, 2256696779, 2279479750, 2288278838, 1677050569, 1334542228]`
- **Program ID (Hex)**: `bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f`
- **Deploy Tx Hash**: `aeb52c595c860392504e790e32d41e8bb84be03141bfea514405465873f5badd`
- **Block**: `16926`

### Execution Receipt (Single Region Test)
- **Target Account**: `Public/T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci`
- **Region**: `china/henan`
- **Register Tx Hash**: `dbf2fd2af1c54454d50613bbe9b57e6db2f06a311f774249cd77943078c8e487`
- **Block**: `16927`
- **Status**: `TransactionExecuted`

### Query Verification
- **Total Regions**: `1`
- **Last Updated**: `1789905600`
- **Verified Record**:
  ```text
  region=china/henan, parent=Some("china"), level=Subregion, cid=zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny, source_url=https://download.geofabrik.de/asia/china/henan-latest.osm.pbf, checksum=0055ebfc7f14585c56d53a88062d5814, version=2026-09-20, hosted=true, timestamp=1789905600
  ```
Full log: [evidence/henan-e2e.log](../evidence/henan-e2e.log) and [evidence/henan-testnet-query.log](../evidence/henan-testnet-query.log)
