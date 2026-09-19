# Logos Storage Module Integration Architecture

This document specifies the authoritative upstream Logos Storage architecture, current repository, version, APIs, and runtime requirements for Logos LP-0018.

---

## 1. Upstream Repositories & Revisions

| Component | Repository | Latest Pinned Tag/Branch | Description |
|---|---|---|---|
| **Storage Module** | [`logos-co/logos-storage-module`](https://github.com/logos-co/logos-storage-module) | `v2.1.3` / `main` | C++ Qt wrapper around Logos Storage core P2P engine |
| **Storage UI** | [`logos-co/logos-storage-ui`](https://github.com/logos-co/logos-storage-ui) | `main` | Basecamp QML file sharing and management application |
| **Module Builder** | [`logos-co/logos-module-builder`](https://github.com/logos-co/logos-module-builder) | `main` | Nix build scaffolding (`mkLogosModule`, `mkLogosQmlModule`) |
| **Documentation** | [Logos Storage Docs](https://logos-co.github.io/logos-storage-module/latest) | `v2.1.3` | Official Sphinx API reference and tutorials |

---

## 2. Runtime & Node Architecture

Logos Storage operates as a decentralized content-addressed storage layer. Applications interact with it through two primary integration paths:

### Path A: Native Basecamp Module IPC (Recommended for Basecamp App / SDK)
In the Basecamp desktop runtime, modules communicate via the Logos IPC bus.
- **Module Name**: `logos-storage-module`
- **Module Interface**: Declared in `metadata.json` under `dependencies`
- **Lifecycle**: Managed by `logoscore` / Basecamp shell
- **Methods**:
  - `storage.init(configJson)`: Initializes local repository and storage node parameters.
  - `storage.start()`: Connects to the Logos peer-to-peer storage network.
  - `storage.create(filePath)`: Ingests a local file, chunks it, computes the cryptographic root CID, and returns `{ "cid": "bafybei..." }`.
  - `storage.download(cid, destinationPath)`: Resolves blocks by CID from the local store or network peers and writes the reconstructed file to destination.
  - `storage.status(cid)`: Queries pinning status, replica count, and availability.

### Path B: Headless Storage Daemon / HTTP Bridge (Used by CLI & Automation)
For standalone CLI tools and CI pipelines without a GUI, the storage daemon exposes an HTTP/JSON interface:
- **Default Endpoint**: `http://127.0.0.1:8080` (configurable via `LOGOS_STORAGE_ENDPOINT`)
- **Upload**:
  ```http
  POST /api/v0/storage/upload
  Content-Type: application/octet-stream
  Body: <binary snapshot bytes>

  Response:
  {
    "cid": "bafybeic...",
    "size": 156172288
  }
  ```
- **Download**:
  ```http
  GET /api/v0/storage/download?cid=bafybeic...

  Response:
  200 OK (Content-Type: application/octet-stream)
  ```
- **Health / Status**:
  ```http
  GET /api/v0/storage/status
  Response: 200 OK
  ```

---

## 3. Local Execution & Testing Procedure

To run against actual Logos Storage infrastructure:

1. **Prerequisites**: Nix with flakes enabled, Linux x86_64 or macOS.
2. **Build / Run Daemon**:
   ```bash
   nix run github:logos-co/logos-storage-module#daemon -- --port 8080 --repo ~/.logos/storage
   ```
3. **Execute Real Integration Test**:
   ```bash
   LOGOS_STORAGE_ENDPOINT="http://127.0.0.1:8080" python tests/integration/test_logos_storage_real.py
   ```

> [!CAUTION]
> If the Logos Storage process is not running, integration tests will exit with status code 2 (`BLOCKED`) and will **never** substitute mock servers.
