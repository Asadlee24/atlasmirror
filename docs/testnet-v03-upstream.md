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
- **Program ID (u32 Array)**: `[347481232, 1299102719, 2328279976, 197338152, 796010409, 3372189242, 412881757, 1852548037]`
- **Program ID (Hex)**: `9024b614ffbb6e4da8bbc68a2824c30ba927722f3a86ffc85d139c18c5a36b6e`
- **Deploy Tx Hash**: `eb12cd28cd4358aa77bf5c617b94f220e36317742d30701bd1c6e7dbf2cee758`
- **Block**: `16907`

### Execution Receipt (Single Region Test)
- **Target Account**: `Public/4CSAM4M1GtrF1tGMJmnCaipbkHH3kYjsMNmWYs6jJHJQ`
- **Region**: `china/henan`
- **Register Tx Hash**: `8c59838b2b516df84bad7a6086658c37d3ac1ba1bc79c9b53555a971782a7b34`
- **Block**: `16908`
- **Status**: `TransactionExecuted`

### Query Verification
- **Total Regions**: `1`
- **Last Updated**: `1726747200`
- **Verified Record**:
  ```text
  region=china/henan, parent=Some("china"), level=Subregion, cid=zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4, source_url=https://download.geofabrik.de/asia/china/henan-latest.osm.pbf, checksum=378df25f824177ebcbe9aa11d88bbd6b, version=2026-09-19, hosted=true, timestamp=1726747200
  ```
Full log: [evidence/testnet-deployment-and-registration.log](file:///c:/Users/Aftab/Desktop/atlasmirror/evidence/testnet-deployment-and-registration.log)
