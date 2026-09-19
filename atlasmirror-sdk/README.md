# AtlasMirror SDK (Logos Core Module)

Reusable Logos Core module for decentralized OpenStreetMap snapshot discovery, hosting, and retrieval.

Built with `logos-module-builder` using the universal authoring model.

## API Summary

- `discoverRegions()`: Lists all 72 predefined non-overlapping regions.
- `getRegion(path)`: Detailed region metadata.
- `getByCid(cid)`: Resolves metadata from a Logos Storage CID.
- `getChildren(parent)`: Lists subregions for decomposed countries (`us`, `india`, `china`, `russia`).
- `resolveRegion(path)`: Returns Logos Storage CID or Geofabrik fallback.
- `checkUpdate(path)`: Compares on-chain snapshot version with upstream Geofabrik index.
- `hostRegion(path)`: Full host pipeline (fetch -> verify MD5 -> store -> register).
- `downloadRegion(path, destination)`: Downloads snapshot by path.
- `importLocal(path, localFile)`: Verifies local PBF against published MD5 and hosts.
- `batchRegister(records)`: Atomically registers up to 50 regions on LEZ.

See [docs/sdk.md](../docs/sdk.md) for full documentation.
