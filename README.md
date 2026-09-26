# AtlasMirror

**Verified OpenStreetMap snapshots distributed through Logos.**

AtlasMirror is a decentralized OpenStreetMap snapshot distribution system built for the Logos ecosystem.

It downloads canonical `.osm.pbf` snapshots from Geofabrik, verifies their published checksum, stores the exact verified bytes in Logos Storage, and registers the resulting CID and snapshot metadata in an on-chain LEZ registry.

AtlasMirror includes:

- a Logos Basecamp application
- a reusable OSM registry SDK/module
- a command-line interface
- a SPEL-based LEZ registry program
- reproducible end-to-end tests
- module catalogue packaging

> Built for Logos λPrize LP-0018.

## Status

Status: Active development  
Target: Logos Testnet 0.3

## Architecture

```text
Geofabrik
    │
    │ OSM PBF + checksum
    ▼
AtlasMirror
    │
    ├── Verify snapshot (MD5)
    │
    ├── Logos Storage ──────► CID
    │
    └── LEZ Registry ───────► metadata + CID
                               │
                               ▼
                    Basecamp apps / SDK / CLI
```

### Why AtlasMirror?

OpenStreetMap snapshots are commonly distributed through central download providers.

AtlasMirror adds a Logos-native distribution layer where verified map snapshots can be mirrored through content-addressed storage and discovered through an on-chain registry.

The original OpenStreetMap data remains attributed to OpenStreetMap contributors.

## Components

| Component | Purpose | Technology |
|---|---|---|
| **[atlasmirror-app](atlasmirror-app/)** | Logos Basecamp GUI | QML / Qt / C++ backend (`logos-module-builder`) |
| **[atlasmirror-sdk](atlasmirror-sdk/)** | Reusable registry and Storage module | C++ (`mkLogosModule`, `interface: universal`) |
| **[atlasmirror-cli](atlasmirror-cli/)** | CLI for hosting, downloading, and registry queries | Rust |
| **[osm-registry](osm-registry/)** | LEZ on-chain registry | Rust / SPEL framework (RISC0 guest) |
| **[examples/consumer-module](examples/consumer-module/)** | Third-party SDK integration example | C++ / QML Logos module |

## Features & Workflows

1. **Region Discovery**: Discovers regions from the 72 predefined non-overlapping set (48 countries and 24 decomposed subregions across US, India, China, and Russia).
2. **Host Workflow**: Download PBF from Geofabrik → verify MD5 checksum → upload exact bytes to Logos Storage → register CID and metadata on LEZ.
3. **Download Workflow**: Query LEZ registry by region path → fetch via CID from Logos Storage (or direct Geofabrik fallback if unhosted). Content-addressed retrieval ensures byte-level integrity.
4. **Bulk Hosting**: Select multiple regions, inspect estimated download sizes, and execute bounded concurrent hosting jobs with individual retry and cancellation.
5. **Local Import**: Provide a local `.osm.pbf` file, verify against published Geofabrik MD5, store to Logos Storage, and register on-chain.
6. **Update Checker**: Compare local/on-chain snapshot timestamps against current Geofabrik indices.
7. **Environment Doctor**: Diagnose toolchain readiness, LEZ RPC connectivity, Storage module status, and directory permissions via `atlasmirror doctor`.

## Quick Start

### Prerequisites

- **Nix** with Flakes enabled (recommended for reproducible builds)
- **Rust** 1.80+ (for CLI and SPEL registry)
- **CMake** 3.22+ & C++17 compiler (for SDK and App)
- **Logos Basecamp** (for running the desktop GUI)

### Build

```bash
# Build the CLI (Rust)
cargo build --release --manifest-path atlasmirror-cli/Cargo.toml

# Or build CLI with Nix Flakes
nix build .#atlasmirror-cli

# Build the SDK C++ module
cmake -S atlasmirror-sdk -B atlasmirror-sdk/build -DCMAKE_BUILD_TYPE=Release
cmake --build atlasmirror-sdk/build --config Release

# Build the Basecamp App Backend and package .lgx bundle
cmake -S atlasmirror-app -B atlasmirror-app/build -DCMAKE_BUILD_TYPE=Release
cmake --build atlasmirror-app/build --config Release
python3 scripts/package_app_lgx.py
```

### Run the CLI

```bash
# Check system readiness
atlasmirror doctor

# List available regions in the predefined set
atlasmirror regions list

# Host a region (download -> verify MD5 -> store -> register)
atlasmirror host asia/pakistan

# Check updates
atlasmirror updates

# Download a region by path (resolves CID from LEZ registry)
atlasmirror download asia/pakistan --output ./pakistan.osm.pbf
```

### Run the End-to-End Demo

```bash
# Runs full pipeline against a local LEZ sequencer
bash scripts/demo.sh
```

## Documentation

- [Compliance Matrix (LP-0018)](docs/lp0018-matrix.md)
- [Upstream Snapshot](docs/upstream-snapshot.md)
- [Architecture & Design](docs/architecture.md)
- [SPEL On-Chain Registry](docs/registry.md)
- [Core SDK Documentation](docs/sdk.md)
- [Storage Adapter](docs/storage.md)
- [Security & Threat Model](docs/security.md)
- [Privacy & Anonymity](docs/privacy.md)
- [Testnet 0.3 Deployment](docs/testnet.md)
- [Cycle Count Benchmarks](docs/performance.md)
- [Adoption & Coverage Evidence](docs/adoption.md)
- [Brand & Visual System](docs/brand.md)
- [Licensing & ODbL](docs/licensing.md)

## Attribution

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).  
OpenStreetMap data is licensed under the [Open Data Commons Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

## License

AtlasMirror source code is dual-licensed under:

- **MIT License** ([LICENSE-MIT](LICENSE-MIT))
- **Apache License 2.0** ([LICENSE-APACHE](LICENSE-APACHE))
