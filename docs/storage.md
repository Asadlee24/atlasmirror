# Logos Storage Adapter Specification

AtlasMirror integrates directly with **Logos Storage** to store and retrieve large `.osm.pbf` binary snapshots.

---

## Core Principles

1. **Content-Addressed Immutability**: All stored files are referenced by their cryptographic Content Identifier (CID). Once a CID is published, any consumer can verify that downloaded bytes match the CID.
2. **Streaming I/O**: OpenStreetMap files can reach 10 GB or more. The storage adapter operates strictly in streaming chunks (e.g. 64KB – 1MB blocks), preventing memory exhaustion.
3. **No Central Fallback for Hosted Content**: When a snapshot is marked `Hosted`, AtlasMirror will retrieve it exclusively via Logos Storage CIDs.
4. **Resilient Retry & Backoff**: Network interruptions or transient peer-to-peer delays trigger exponential backoff with jitter up to a configurable maximum retry count (default: 5 retries).

---

## Storage Operations

### `storagePut(localPath: &Path) -> Result<String, StorageError>`
- Opens the verified local `.osm.pbf` file.
- Computes content address chunks and streams bytes into the Logos Storage node.
- Returns the immutable storage CID upon receipt of successful persistence acknowledgment.

### `storageGet(cid: &str, destination: &Path) -> Result<(), StorageError>`
- Resolves the CID from Logos Storage peers.
- Streams received chunks directly into a temporary file (`destination.part`).
- Verifies integrity of downloaded bytes against the CID.
- Atomically renames `destination.part` to `destination`.

### `storageStatus(cid: &str) -> Result<StorageStatus, StorageError>`
- Queries local node and network peers for availability, replica count, and pinned status of the specified CID.

---

## Retry and Backoff State Machine

```text
┌──────────────┐
│  Upload/Get  │
└──────┬───────┘
       │
       ▼
   [Attempt] ──Success──► [Complete]
       │
     Error
       │
       ▼
  [Is Transient?]
   ├── No ──────────────► [Terminal Error]
   └── Yes
       │
  [Attempt < Max Retries?]
   ├── No ──────────────► [Terminal Error (Retries Exhausted)]
   └── Yes
       │
       ▼
  [Sleep: base_ms * 2^(attempt-1) + jitter]
       │
       └────────────────► [Next Attempt]
```
