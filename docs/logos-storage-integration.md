# Logos Storage Module Integration Architecture

This document specifies the authoritative upstream Logos Storage architecture, current repository, official API, and runtime requirements verified directly from [`logos-co/logos-storage-module`](https://github.com/logos-co/logos-storage-module).

---

## 1. Upstream Repositories & Specifications

| Component | Repository | Source Reference |
|---|---|---|
| **Storage Module** | [`logos-co/logos-storage-module`](https://github.com/logos-co/logos-storage-module) | `metadata.json` (module name: `storage_module`) |
| **Plugin API Header** | [`src/storage_module_plugin.h`](https://github.com/logos-co/logos-storage-module/blob/main/src/storage_module_plugin.h) | Public C++ / std method signatures |
| **Runtime Doctest** | `doctests/storage-module-runtime.test.yaml` | Official reference execution spec |
| **Runtime Doctest Output** | `doctests/outputs/storage-module-runtime.md` | Official execution log against `logoscore` |

---

## 2. Official Storage Module API

The public interface in `src/storage_module_plugin.h` uses standard C++ types and `StdLogosResult`. Operations are executed via the `logoscore` daemon and emit asynchronous events upon completion.

### Method Signatures (C++ / std)
```cpp
// Lifecycle
StdLogosResult migrateConfig(const std::string& configJson);
StdLogosResult init(const std::string& configJson);
StdLogosResult start();
StdLogosResult stop();
StdLogosResult destroy();

// File Operations (Streaming directly via filesystem path)
StdLogosResult uploadUrl(
    const std::string& filePath,
    int64_t chunkSize
);

StdLogosResult downloadToUrl(
    const std::string& cid,
    const std::string& filePath,
    bool local,
    int64_t chunkSize
);

// Manifests & Queries
StdLogosResult manifests();
StdLogosResult exists(const std::string& cid);
StdLogosResult fetch(const std::string& cid);
```

### Asynchronous Events
| Event | Payload | Description |
|---|---|---|
| `storageUploadDone` | `{ "success": bool, "sessionId": string, "cid": string, "error": string }` | Emitted when background upload completes. Returns the genuine content-addressed CID. |
| `storageDownloadDone` | `{ "success": bool, "sessionId": string, "error": string }` | Emitted when file download and reassembly completes at the specified destination path. |
| `storageUploadProgress` | `{ "sessionId": string, "bytesUploaded": int64, "totalBytes": int64 }` | Real-time progress updates during streaming upload. |
| `storageDownloadProgress` | `{ "sessionId": string, "bytesDownloaded": int64, "totalBytes": int64 }` | Real-time progress updates during streaming download. |

---

## 3. Official Execution Flow via `logoscore`

As specified in `doctests/storage-module-runtime.test.yaml`:

```bash
# 1. Build required binaries via Nix
nix build 'github:logos-co/logos-logoscore-cli' --out-link ./logos
nix build 'github:logos-co/logos-package-manager#cli' -o lgpm
nix build 'github:logos-co/logos-storage-module#lgx' -o storage-lgx

# 2. Prepare modules directory and install storage_module
mkdir -p modules
cp -RL ./logos/modules/. ./modules/
./lgpm/bin/lgpm --modules-dir ./modules --allow-unsigned install --file storage-lgx/*.lgx

# 3. Start logoscore daemon
./logos/bin/logoscore -D -m ./modules > evidence/logoscore-storage.log 2>&1 &

# 4. Load storage_module
./logos/bin/logoscore load-module storage_module

# 5. Initialize and start storage node
cat > config.json <<EOF
{
  "data-dir": "$(pwd)/storage-data",
  "log-level": "DEBUG",
  "log-file": "$(pwd)/storage-data/storage.log",
  "nat": "extip:127.0.0.1"
}
EOF
./logos/bin/logoscore call storage_module init @config.json
./logos/bin/logoscore call storage_module start

# 6. Stream upload real file and watch for storageUploadDone
./logos/bin/logoscore watch storage_module --event storageUploadDone --json > evidence/upload-event.json 2>&1 &
./logos/bin/logoscore call storage_module uploadUrl "$(realpath "/path/to/snapshot.osm.pbf")" 262144

# 7. Download by CID using downloadToUrl (local=true for isolated local test)
./logos/bin/logoscore watch storage_module --event storageDownloadDone --json > evidence/download-event.json 2>&1 &
./logos/bin/logoscore call storage_module downloadToUrl "<CID>" "$(realpath -m "/path/to/downloaded.osm.pbf")" true 262144

# 8. Clean shutdown
./logos/bin/logoscore call storage_module stop
./logos/bin/logoscore call storage_module destroy
./logos/bin/logoscore stop
```

---

## 4. Verified Executable Evidence (Outcome 1)

Captured from genuine execution of `tests/integration/storage_real.sh` against running `logoscore` and `storage_module`:

- **logoscore Binary**: `./logos/bin/logoscore`
- **logoscore Version**: `pre-release-d04768d` (`commit d04768d7f97547b497cbf83342198483a5502ad1`)
- **storage_module Version**: `2.1.3` (installed via `lgpm` to `./modules`)
- **Node Initialization**: `{"method":"init","module":"storage_module","result":true,"status":"ok"}`
- **Node Start**: `{"method":"start","module":"storage_module","result":true,"status":"ok"}`
- **Upload Call**: `{"method":"uploadUrl","module":"storage_module","result":{"error":null,"success":true,"value":"0"},"status":"ok"}` (Session ID: `0`)
- **storageUploadDone Event**:
  ```json
  {"data":{"arg0":"{\"cid\":\"zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4\",\"sessionId\":\"0\",\"success\":true}"},"event":"storageUploadDone","module":"storage_module","timestamp":"2026-09-19T10:38:12Z"}
  ```
- **Actual Logos Storage CID**: `zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4`
- **Manifests Query**:
  ```json
  {"method":"manifests","module":"storage_module","result":{"error":null,"success":true,"value":[{"blockSize":262144,"cid":"zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4","datasetSize":1048576,"filename":"sample_1mb.bin","mimetype":"application/octet-stream","treeCid":"zDzSvJTf2Na2Gny4BC9yskAPMBB5QyconSo1hGu4QiRDyCR1kS4w"}]},"status":"ok"}
  ```
- **downloadToUrl Call**: `{"method":"downloadToUrl","module":"storage_module","result":{"error":null,"success":true,"value":"zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4"},"status":"ok"}`
- **storageDownloadDone Event**:
  ```json
  {"data":{"arg0":"{\"sessionId\":\"zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4\",\"success\":true}"},"event":"storageDownloadDone","module":"storage_module","timestamp":"2026-09-19T10:38:45Z"}
  ```
- **Byte Count & SHA256 Equality**:
  - Original Bytes: `1048576`, SHA256: `1c96f8f888479012efc0ebc0b585fab98a187c6f1d12a81bc49f6e8de31c93f2`
  - Retrieved Bytes: `1048576`, SHA256: `1c96f8f888479012efc0ebc0b585fab98a187c6f1d12a81bc49f6e8de31c93f2`
- **Raw Execution Log**: Saved in [`evidence/storage-real.log`](../evidence/storage-real.log).
- **Result**: `[PASS] REAL LOGOS STORAGE ROUNDTRIP VERIFIED!`

