# Logos Storage Module Integration Architecture

This document specifies the authoritative upstream Logos Storage architecture, current repository, official API, and runtime requirements verified directly from [`logos-co/logos-storage-module`](https://github.com/logos-co/logos-storage-module).

---

## 1. Upstream Repositories & Specifications

| Component | Repository | Source Reference |
|---|---|---|
| **Storage Module** | [`logos-co/logos-storage-module`](https://github.com/logos-co/logos-storage-module) | `metadata.json` (module name: `storage_module`) |
| **Plugin API Header** | [`src/storage_module_plugin.h`](https://github.com/logos-co/logos-storage-module/blob/main/src/storage_module_plugin.h) | Public C++ / QML method signatures |
| **Runtime Doctest** | `doctests/storage-module-runtime.test.yaml` | Official reference execution spec |
| **Runtime Doctest Output** | `doctests/outputs/storage-module-runtime.md` | Official execution log against `logoscore` |

---

## 2. Official Storage Module API

The public API is defined in `src/storage_module_plugin.h`. Operations are executed within the `logoscore` daemon and emit asynchronous events upon completion.

### Methods
```cpp
// Lifecycle
void migrateConfig(const QString &configJson);
void init(const QString &configJson);
void start();
void stop();
void destroy();

// File Operations (Streaming directly via filesystem path)
void uploadUrl(const QString &filePath, int chunkSize);
void downloadToUrl(const QString &cid, const QString &destinationPath, bool localFlag, int chunkSize);

// Chunked Buffer Operations (Alternative)
void uploadInit(qint64 totalSize, int chunkSize);
void uploadChunk(const QString &sessionId, const QByteArray &data);
void uploadFinalize(const QString &sessionId);
void downloadChunks(const QString &cid, bool localFlag, int chunkSize);

// Status & Query
bool exists(const QString &cid);
void fetch(const QString &cid);
```

### Asynchronous Events
| Event | Signature / Payload | Description |
|---|---|---|
| `storageUploadDone` | `(bool success, QString sessionId, QString cid, QString error)` | Emitted when background upload completes. Returns the genuine content-addressed CID. |
| `storageDownloadDone` | `(bool success, QString sessionId, QString error)` | Emitted when file download and reassembly completes at the specified destination path. |
| `storageUploadProgress` | `(QString sessionId, qint64 bytesUploaded, qint64 totalBytes)` | Real-time progress updates during streaming upload. |
| `storageDownloadProgress` | `(QString sessionId, qint64 bytesDownloaded, qint64 totalBytes)` | Real-time progress updates during streaming download. |

> [!IMPORTANT]
> **No REST Bridge:** The official `logos-storage-module` does NOT expose `/api/v0/storage/upload` or `/api/v0/storage/download` HTTP endpoints. All interaction occurs via the `logoscore` daemon loading `storage_module` as a native plugin / `.lgx`.

---

## 3. Reference Execution Flow via `logoscore`

As demonstrated in `doctests/storage-module-runtime.test.yaml`:

```bash
# 1. Start logoscore daemon with modules directory
logoscore -m ./modules --load-modules storage_module

# 2. Initialize and start storage node
logoscore call storage_module init @config.json --json
logoscore call storage_module start --json

# 3. Stream upload real file from disk (Logos Storage streams/chunks internally)
#    Arguments: <absolute_file_path> <chunk_size>
logoscore call storage_module uploadUrl "/path/to/snapshot.osm.pbf" 1048576 --json
# Observe storageUploadDone event -> captures real CID (e.g. "bafybei...")

# 4. Download file by CID to destination
#    Arguments: <cid> <destination_path> <local_flag> <chunk_size>
logoscore call storage_module downloadToUrl "<CID>" "/path/to/downloaded.osm.pbf" false 1048576 --json
# Observe storageDownloadDone event -> completion

# 5. Verify byte integrity
sha256sum /path/to/snapshot.osm.pbf /path/to/downloaded.osm.pbf
```

---

## 4. Current Execution Status

> [!WARNING]
> **Status: BLOCKED**
> Neither `logoscore` nor the compiled `storage_module` plugin is currently present or running in the local environment.
> Real storage integration cannot be verified until `logoscore` and `storage_module` are built and executed.
