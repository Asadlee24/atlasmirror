# Third-Party Basecamp Consumer Example

This module demonstrates how an independent Logos Basecamp application or module can integrate the `atlasmirror_sdk` in **under 15 minutes**.

A Basecamp consumer needs only the PBF files locally and the SDK to discover and resolve them. It does **not** need the `atlasmirror-app` distribution UI.

## Integration Steps

1. Declare the SDK dependency in `metadata.json`:
   ```json
   {
     "name": "my_map_app",
     "dependencies": ["atlasmirror_sdk"]
   }
   ```

2. Access the SDK in QML via the standard Logos host injection:
   ```qml
   property var osmSdk: logos.module("atlasmirror_sdk")

   function getMap(region) {
       let record = osmSdk.resolveRegion(region);
       console.log("Storage CID:", record.cid);
       osmSdk.downloadRegion(region, "/tmp/" + region.replace('/', '_') + ".osm.pbf");
   }
   ```

3. Launch and test using `logos-module-builder`:
   ```bash
   nix run .
   ```
