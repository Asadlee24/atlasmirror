# AtlasMirror

**Verified OpenStreetMap snapshots distributed through Logos.**

AtlasMirror is a decentralized OpenStreetMap snapshot distribution system built for the Logos ecosystem.

It downloads canonical `.osm.pbf` snapshots from Geofabrik, verifies their published checksum, stores the exact verified bytes in Logos Storage, and registers the resulting CID and snapshot metadata in an on-chain LEZ registry.

AtlasMirror includes:
- a Logos Basecamp application (`atlasmirror-app`)
- a reusable OSM registry SDK module (`atlasmirror-sdk`)
- a command-line interface (`atlasmirror-cli`)
- a SPEL-based LEZ registry program (`osm-registry`)
- reproducible end-to-end tests and A1 storage byte audit
- module catalogue packaging for Logos Basecamp

> Built for Logos λPrize LP-0018.

---

## Live Logos Testnet 0.3 Deployment

| Parameter | Value | Provenance |
|---|---|---|
| **Network** | Logos Testnet 0.3 (LEZ) | `https://testnet.lez.logos.co` |
| **Deployed Program ID** | `bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f` | RISC0 zkVM ELF image ID |
| **Canonical Registry Account** | `T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci` | Deployed on-chain state shard |
| **Deployment Transaction** | `aeb52c595c860392504e790e32d41e8bb84be03141bfea514405465873f5badd` | Block 16926 |
| **Logos Storage Gateway** | `logos.test` / `127.0.0.1:8001` | `storage_module` v2.1.2 |

---

## Basecamp Package Manager Installation

AtlasMirror is published to the official module catalog and installable through the Basecamp Package Manager (`lgpm`):

### 1. Module Catalog URL
```text
https://raw.githubusercontent.com/Asadlee24/logos-modules-release-base/main/logos-repo.json
```

### 2. Install via Basecamp Package Manager
```bash
# Register AtlasMirror repository in Basecamp
lgpm repo add atlasmirror https://raw.githubusercontent.com/Asadlee24/logos-modules-release-base/main/logos-repo.json

# Update catalog index
lgpm update

# Install Core SDK module
lgpm install atlasmirror_sdk

# Install Basecamp GUI application
lgpm install atlasmirror_app
```

> **Target Environment Versions:**
> - Logos Basecamp: `0.3.0-rc.3`
> - `logos-module-builder`: commit `0c5b062fd11b20f85cc7c0720ddcac1cbbb46c4c`
> - Qt Framework: Qt 6.5+ (`Qt6::Core`, `Qt6::Quick`, `Qt6::Qml`, `Qt6::Gui`)

---

## Canonical 72-Region Closed Set

In strict compliance with LP-0018, AtlasMirror enforces an immutable, non-overlapping closed catalog of exactly **72 regions** defined in [`metadata/regions.json`](metadata/regions.json):

- **48 Standalone Countries** (`level: country`, `parent: null`):
  `asia/pakistan`, `europe/germany`, `europe/france`, `europe/great-britain`, `europe/italy`, `europe/spain`, `europe/poland`, `europe/netherlands`, `europe/belgium`, `europe/switzerland`, `europe/austria`, `europe/czech-republic`, `europe/sweden`, `europe/norway`, `europe/denmark`, `europe/finland`, `europe/portugal`, `europe/greece`, `europe/ireland-and-northern-ireland`, `europe/hungary`, `europe/romania`, `europe/bulgaria`, `europe/ukraine`, `europe/belarus`, `europe/turkey`, `north-america/canada`, `north-america/mexico`, `asia/japan`, `asia/south-korea`, `asia/indonesia`, `asia/thailand`, `asia/vietnam`, `asia/malaysia-singapore-brunei`, `asia/philippines`, `asia/bangladesh`, `asia/iran`, `australia-oceania/australia`, `south-america/brazil`, `south-america/argentina`, `south-america/colombia`, `south-america/peru`, `south-america/chile`, `africa/south-africa`, `africa/egypt`, `africa/nigeria`, `africa/kenya`, `africa/morocco`, `africa/ethiopia`.
- **24 Decomposed Subregions** (`level: subregion`, `parent: <country>`):
  - **US (8)**: `us/california`, `us/texas`, `us/florida`, `us/new-york`, `us/washington`, `us/illinois`, `us/georgia`, `us/pennsylvania`
  - **India (6)**: `india/central-zone`, `india/eastern-zone`, `india/north-eastern-zone`, `india/northern-zone`, `india/southern-zone`, `india/western-zone`
  - **China (6)**: `china/guangdong`, `china/jiangsu`, `china/shandong`, `china/zhejiang`, `china/sichuan`, `china/henan`
  - **Russia (4)**: `russia/central-fed-district`, `russia/northwestern-fed-district`, `russia/volga-fed-district`, `russia/siberian-fed-district`

Any region outside this closed set is rejected before network transfer.

---

## Build & Run Instructions

### Linux x86_64

```bash
# 1. Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y cmake qt6-base-dev qt6-declarative-dev libgl1-mesa-dev pkg-config

# 2. Build CLI and Registry Core
cd atlasmirror-cli && cargo build --release
cd ../osm-registry && cargo test --release

# 3. Build SDK (C++)
cmake -S atlasmirror-sdk -B atlasmirror-sdk/build -DCMAKE_BUILD_TYPE=Release
cmake --build atlasmirror-sdk/build --config Release

# 4. Build Basecamp App Backend and Package .lgx Bundle
cmake -S atlasmirror-app -B atlasmirror-app/build -DCMAKE_BUILD_TYPE=Release
cmake --build atlasmirror-app/build --config Release
python3 scripts/package_app_lgx.py
```

### macOS Apple Silicon (ARM64)

```bash
# 1. Install dependencies via Homebrew
brew install cmake qt@6

# 2. Build CLI
cd atlasmirror-cli && cargo build --release

# 3. Build SDK (C++)
cmake -S atlasmirror-sdk -B atlasmirror-sdk/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$(brew --prefix qt@6)"
cmake --build atlasmirror-sdk/build --config Release

# 4. Build Basecamp App Backend and Package .lgx
cmake -S atlasmirror-app -B atlasmirror-app/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$(brew --prefix qt@6)"
cmake --build atlasmirror-app/build --config Release
python3 scripts/package_app_lgx.py
```

---

## CLI Setup & Command Reference

The `atlasmirror` CLI provides comprehensive subcommands for hosting, batching, queries, and downloads:

```bash
# Verify system readiness and dependencies
atlasmirror doctor

# Discover regions from the 72 catalog
atlasmirror regions list
atlasmirror regions list --filter hosted
atlasmirror regions show asia/pakistan

# Host a single region (Fetch -> Verify MD5 -> Logos Storage -> LEZ Register)
atlasmirror host asia/pakistan

# Batch Host multiple regions in a single transaction
atlasmirror host --many us/california us/texas us/florida

# Import a local PBF file with automatic Geofabrik MD5 checksum verification
atlasmirror host --file asia/pakistan /path/to/pakistan-latest.osm.pbf

# Check for newer upstream snapshots
atlasmirror updates
atlasmirror updates check asia/pakistan

# Look up on-chain records from LEZ
atlasmirror lookup region asia/pakistan --json
atlasmirror lookup parent us --json
atlasmirror lookup cid zDvZRwzm9WQQrvAZL4NavbFXjmbHTFNyho68zPMxKsCvfGEn2LbD

# Download verified snapshot by region path (fetches from Logos Storage via CID)
atlasmirror download asia/pakistan --output ./pakistan.osm.pbf
```

---

## Worked SDK Integration Example

Integrating `atlasmirror_sdk` into an external application or Basecamp module takes under 5 minutes:

### C++ Example

```cpp
#include "atlasmirror_sdk_impl.h"
#include <iostream>
#include <nlohmann/json.hpp> // or any standard JSON parser

int main() {
    AtlasmirrorSdkImpl sdk;

    // 1. Resolve live on-chain metadata for region
    std::string metaJson = sdk.resolveRegion("asia/pakistan");
    std::cout << "On-chain record: " << metaJson << std::endl;

    // 2. Download snapshot with byte-level checksum verification
    bool success = sdk.downloadRegion("asia/pakistan", "./pakistan.osm.pbf");
    if (success) {
        std::cout << "Snapshot successfully retrieved from Logos Storage!" << std::endl;
    } else {
        std::cerr << "Download failed or checksum mismatch!" << std::endl;
    }
    return 0;
}
```

### Basecamp QML Example

```qml
import QtQuick
import QtQuick.Controls

Item {
    property var osmSdk: logos.module("atlasmirror_sdk")

    Button {
        text: "Resolve & Fetch Pakistan Map"
        onClicked: {
            if (osmSdk) {
                let info = JSON.parse(osmSdk.resolveRegion("asia/pakistan"));
                console.log("Storage CID:", info.cid);
                console.log("Published Checksum:", info.checksum);
                osmSdk.downloadRegion("asia/pakistan", "/tmp/pakistan.osm.pbf");
            }
        }
    }
}
```

See [`examples/consumer-module/`](examples/consumer-module/) for a complete working Basecamp consumer application.

---

## Documentation

- [Compliance Matrix (LP-0018)](docs/lp0018-matrix.md)
- [Ecosystem Integration Guide](docs/integration-guide.md)
- [Architecture & Design](docs/architecture.md)
- [SPEL On-Chain Registry](docs/registry.md)
- [Core SDK Documentation](docs/sdk.md)
- [Storage Adapter](docs/storage.md)
- [Security & Threat Model](docs/security.md)
- [Privacy & Anonymity](docs/privacy.md)
- [Testnet 0.3 Upstream Discovery](docs/testnet-v03-upstream.md)
- [Cycle Count Benchmarks](docs/performance.md)
- [Adoption & Coverage Tracking](docs/adoption.md)
- [Licensing & ODbL](docs/licensing.md)

---

## Attribution & License

Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), licensed under the [Open Data Commons Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).

AtlasMirror is dual-licensed under [MIT](LICENSE-MIT) and [Apache 2.0](LICENSE-APACHE).
