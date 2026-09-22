# AtlasMirror Ecosystem Integration Guide (LP-0018 A2)

This guide provides turnkey, copy-paste instructions for external developers and Basecamp application authors to consume decentralized OpenStreetMap snapshots distributed by **AtlasMirror**.

---

## 1. Integration Paths

AtlasMirror exposes four independent integration paths:

| Consumer Type | Primary Interface | Integration Artifact | Typical Use Case |
|---|---|---|---|
| **Basecamp GUI App** | QML Module | `atlasmirror_app.lgx` or QML import | Embedded map viewers, city navigators |
| **C++ Native Module** | C++ Shared Library | `atlasmirror-sdk` (`atlasmirror_sdk_impl.h`) | High-performance routing engines, GIS renderers |
| **Rust / ZK Sequencer** | Rust Crate | `osm-registry-core` | State verification, SPEL contract inter-op |
| **CLI / Scripting** | JSON-enabled CLI | `atlasmirror-cli --json` | Automated deployment pipelines, offline caches |

---

## 2. Basecamp QML Integration (Quickstart: < 5 Minutes)

In your Basecamp application QML file, you can directly resolve the `atlasmirror_sdk` to look up snapshot CIDs and trigger downloads:

```qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: mapConsumerRoot
    width: 640
    height: 480
    color: "#000000"

    // Resolves AtlasMirror SDK service without tight UI coupling
    property var osmSdk: (typeof logos !== "undefined") ? logos.module("atlasmirror_sdk") : null

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 12

        Button {
            text: "Fetch Offline Map: asia/pakistan"
            onClicked: {
                if (osmSdk) {
                    let record = osmSdk.resolveRegion("asia/pakistan");
                    console.log("Resolved Storage CID:", record.cid);
                    console.log("Verified Checksum:", record.checksum);
                    
                    // Trigger download to application cache
                    osmSdk.downloadSnapshot(record.cid, "/tmp/pakistan.osm.pbf");
                } else {
                    console.log("AtlasMirror SDK not loaded; falling back to direct cache");
                }
            }
        }
    }
}
```

---

## 3. C++ SDK Integration

To link against `atlasmirror_sdk` in your CMake-based Basecamp module:

### `CMakeLists.txt`
```cmake
find_package(atlasmirror_sdk REQUIRED)

target_link_libraries(my_consumer_module PRIVATE
    atlasmirror_sdk
    Qt6::Core
    Qt6::Quick
)
```

### `consumer.cpp`
```cpp
#include "atlasmirror_sdk_impl.h"
#include <iostream>

void load_region_snapshot() {
    AtlasMirrorSDK sdk;
    
    // Resolve on-chain metadata
    RegionMetadata meta = sdk.resolve_region("europe/monaco");
    std::cout << "Region: " << meta.region << std::endl;
    std::cout << "Logos Storage CID: " << meta.cid << std::endl;
    std::cout << "Published MD5: " << meta.checksum << std::endl;
    
    // Download with byte-level integrity verification
    bool ok = sdk.download_verified(meta.cid, "/tmp/monaco.osm.pbf", meta.checksum);
    if (ok) {
        std::cout << "Snapshot downloaded and integrity verified!" << std::endl;
    }
}
```

---

## 4. Rust Integration (`osm-registry-core`)

Add the dependency to your `Cargo.toml`:
```toml
[dependencies]
osm-registry-core = { git = "https://github.com/Asadlee24/atlasmirror.git", package = "osm-registry-core" }
```

Validate and parse records in Rust:
```rust
use osm_registry_core::{RegionRecord, RegisterRegionArgs, RegionLevel};

fn verify_metadata(args: &RegisterRegionArgs) -> Result<(), osm_registry_core::RegistryError> {
    args.validate()?;
    println!("Region record valid: {}", args.region);
    Ok(())
}
```

---

## 5. CLI / Daemon Integration (`atlasmirror-cli`)

For headless bots, microservices, or shell scripts:

```bash
# Query on-chain record in JSON format
atlasmirror-cli lookup region asia/pakistan --json

# Query available updates
atlasmirror-cli updates --json

# Import and verify local PBF
atlasmirror-cli host --file europe/monaco /path/to/monaco.osm.pbf
```

Sample JSON response:
```json
{
  "region": "asia/pakistan",
  "level": "country",
  "parent": "asia",
  "cid": "zDvZRwzm9WQQrvAZL4NavbFXjmbHTFNyho68zPMxKsCvfGEn2LbD",
  "checksum": "d63c9409c20924d0813b81266eb2f5ad",
  "version": "2026-09-19",
  "hosted": true,
  "timestamp": 1789974237
}
```

---

## 6. Submitting Your Integration to the Official Catalog

We invite community developers, Basecamp module creators, and geospatial applications to integrate with AtlasMirror.

To have your module listed in the official [LP-0018 Adoption Matrix](docs/adoption.md):

1. Integrate `atlasmirror-sdk`, `osm-registry-core`, or QML module into your public repository.
2. Ensure your build passes in CI.
3. Open an issue using the [Ecosystem Integration Issue Template](.github/ISSUE_TEMPLATE/ecosystem_integration.md).
4. Our team will verify the integration, test against canonical testnet 0.3, and add your project to the verified ecosystem tracking table.
