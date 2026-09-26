# AtlasMirror Core SDK Documentation

The **AtlasMirror SDK** (`atlasmirror-sdk`) is a reusable Logos Core module developed with `logos-module-builder` using the universal authoring model. It provides C++ and QML-compatible APIs for discovering, resolving, hosting, and downloading verified OpenStreetMap snapshots.

Third-party Basecamp applications can consume `atlasmirror-sdk` directly without depending on the `atlasmirror-app` GUI.

---

## Architecture

The SDK class `AtlasMirrorSdkImpl` inherits from `LogosModuleContext`. Its public methods constitute the module API, and `logos-module-builder` automatically generates the LIDL contract (`generated_code/atlasmirror_sdk.lidl`), C-ABI export dispatchers, and Qt plugin glue.

```text
┌───────────────────────────────────────────────┐
│              Basecamp Application             │
└───────────────────────┬───────────────────────┘
                        │ QML / C++
                        ▼
┌───────────────────────────────────────────────┐
│               atlasmirror-sdk                 │
│  ┌─────────────────────────────────────────┐  │
│  │   AtlasMirrorSdkImpl (Public API)       │  │
│  └────────────────────┬────────────────────┘  │
│                       │                       │
│        ┌──────────────┴──────────────┐        │
│        ▼                             ▼        │
│ ┌───────────────┐            ┌──────────────┐ │
│ │ Storage Engine│            │ LEZ RPC Client││
│ └───────────────┘            └──────────────┘ │
└───────────────────────────────────────────────┘
```

---

## Public API Reference

### Region Discovery & Resolution

#### `discoverRegions() -> QJsonArray`
Returns the predefined list of 72 regions with their names, tree levels, parents, and current hosted statuses.

#### `getRegion(const QString &path) -> QJsonObject`
Returns detailed metadata for a specific canonical region path (e.g. `"asia/pakistan"`).

#### `getByCid(const QString &cid) -> QJsonObject`
Resolves metadata for a specific Logos Storage CID.

#### `getChildren(const QString &parent) -> QJsonArray`
Returns all child subregions for a decomposed country (e.g. `"us"`, `"india"`, `"china"`, `"russia"`).

#### `resolveRegion(const QString &path) -> QJsonObject`
Resolves the download source for a region:
- If hosted: returns `{"source": "logos_storage", "cid": "...", "checksum": "..."}`
- If not hosted: returns `{"source": "geofabrik_fallback", "url": "...", "checksum": "..."}`

#### `checkUpdate(const QString &path) -> QJsonObject`
Compares the on-chain snapshot version against the latest Geofabrik index, returning:
`UP_TO_DATE`, `UPDATE_AVAILABLE`, `NOT_HOSTED`, or `SOURCE_UNAVAILABLE`.

---

### Hosting & Downloading (Full Distribution API)

#### `hostRegion(const QString &path) -> QJsonObject`
Executes the full hosting workflow:
1. Fetch latest PBF and MD5 from Geofabrik.
2. Verify local streaming MD5 against published MD5.
3. Upload exact bytes to Logos Storage.
4. Register CID and metadata on LEZ.

#### `downloadRegion(const QString &path, const QString &destination) -> bool`
Downloads the PBF snapshot to `destination`. If hosted, downloads by CID from Logos Storage; if unhosted, uses direct Geofabrik fallback.

#### `importLocal(const QString &path, const QString &localFilePath) -> QJsonObject`
Verifies an existing local `.osm.pbf` file against Geofabrik's published MD5 and hosts it.

---

## 15-Minute Consumer Integration Guide

To consume AtlasMirror in another Logos Basecamp module:

1. Add `atlasmirror-sdk` to `metadata.json`:
   ```json
   {
     "dependencies": ["atlasmirror_sdk"]
   }
   ```
2. In your QML view:
   ```qml
   import QtQuick
   import QtQuick.Controls

   Item {
       property var osmSdk: logos.module("atlasmirror_sdk")

       Button {
           text: "Fetch Pakistan Map"
           onClicked: {
               let info = JSON.parse(osmSdk.resolveRegion("asia/pakistan"));
               console.log("Resolved CID:", info.cid);
               osmSdk.downloadRegion("asia/pakistan", "/tmp/pakistan.osm.pbf");
           }
       }
   }
   ```
See [examples/consumer-module/](../examples/consumer-module/) for a complete working implementation.
