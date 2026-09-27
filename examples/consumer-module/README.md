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

2. Access the SDK via the canonical `ConsumerBackend` QtRO / C++ UI bridge:
   ```qml
   // Resolves canonical ConsumerBackend bridge injected by Basecamp runtime
   property var backend: (typeof consumerBackend !== "undefined") 
       ? consumerBackend 
       : ((typeof cBackend !== "undefined") ? cBackend : null)

   function getMap(region) {
       if (backend) {
           let record = JSON.parse(backend.resolveRegion(region));
           console.log("Storage CID:", record.cid);
           backend.downloadRegion(region, "/tmp/" + region.replace('/', '_') + ".osm.pbf");
       }
   }
   ```

3. Launch and test using `logos-module-builder`:
   ```bash
   nix run .
   ```
