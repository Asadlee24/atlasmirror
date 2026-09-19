# AtlasMirror Architecture & Design

AtlasMirror is built to solve a critical resilience and decentralization problem in the geospatial ecosystem: OpenStreetMap snapshot distribution currently relies almost entirely on centralized mirror infrastructure (e.g. Geofabrik).

AtlasMirror creates a **Logos-native decentralized distribution pipeline**:
1. Canonical snapshot metadata and bytes are imported from Geofabrik.
2. Snapshot integrity is validated at import time via published MD5 checksums.
3. The exact verified bytes are persisted to **Logos Storage**, yielding an immutable Content Identifier (CID).
4. The CID, canonical path, tree level, parent, checksum, and version timestamp are registered on-chain in an **LEZ SPEL program**.
5. Logos Basecamp apps, third-party modules, and CLI tools discover and fetch verified snapshots by CID directly from Logos Storage without depending on centralized web servers.

---

## High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Geofabrik Canonical Source               │
│                (index-v1-nogeom.json + .md5)                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                Download PBF & │ Checksum
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 AtlasMirror Core Engine                     │
│    (Streaming I/O, Checksum Verifier, Allowlist Filter)     │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
    Store PBF  │                    Register   │
    Bytes      │                    Metadata   │
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│        Logos Storage         │ │    Logos Execution Zone     │
│   (Content-Addressed CID)    │ │   (SPEL On-Chain Registry)  │
└──────────────┬───────────────┘ └─────────────┬───────────────┘
               │                               │
               └───────────────┬───────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Consumer Layer                          │
│                                                             │
│   ┌─────────────────────┐       ┌───────────────────────┐   │
│   │   atlasmirror-app   │       │    atlasmirror-cli    │   │
│   │   (Basecamp QML)    │       │     (Rust Engine)     │   │
│   └─────────────────────┘       └───────────────────────┘   │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │   atlasmirror-sdk (Reusable Logos Core Module)      │   │
│   │   └── Third-Party Basecamp Consumer Modules         │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Core System Components

### 1. Predefined Region Catalog (`metadata/regions.json`)
LP-0018 mandates a **closed, non-overlapping set of 72 regions**:
- **48 Countries**: Represented at the country level (`level: country`, `parent: null`).
- **24 Subregions**: 4 decomposed large countries (`us`: 8 states, `india`: 6 zones, `china`: 6 provinces, `russia`: 4 federal districts).
- **Non-Overlapping Invariant**: No region in the active set contains any other region in the set. For example, `us` is never hosted as a country; only its 8 subregions are hosted.

### 2. Geofabrik Ingestion & Verification Adapter
- **Streaming Fetch**: Large PBF extracts (100MB – 15GB+) are streamed with progress callbacks. Partial files are discarded on fatal failure.
- **Import Checksum**: Fetches `<pbf_url>.md5`, extracts the 32-character hexadecimal MD5 hash, computes the streaming MD5 of the local file, and halts immediately on mismatch.

### 3. Logos Storage Adapter
- Uploads exact verified PBF bytes to Logos Storage.
- Obtains the content-addressed CID.
- Implements exponential backoff with jitter on transient failures and surfaces clear terminal errors.
- Provides CID-based content retrieval with integrity verification.

### 4. SPEL On-Chain Registry (`osm-registry`)
- Built for the Logos Execution Zone (LEZ) using the SPEL framework.
- Stores per-region entries:
  - `region`: Geofabrik path (e.g. `asia/pakistan`, `us/california`)
  - `parent`: Parent identifier (e.g. `null` or `"us"`)
  - `level`: `country` or `subregion`
  - `cid`: Content identifier in Logos Storage
  - `source_url`: Canonical Geofabrik snapshot URL
  - `checksum`: Published MD5 hash
  - `version`: Snapshot version/date
  - `hosted`: Boolean flag
  - `timestamp`: Monotonic Unix timestamp of registration
- Supports batch registration up to 50 regions per transaction.
- Queryable by region, parent, or CID.

### 5. Logos Core SDK Module (`atlasmirror-sdk`)
- Authored with `logos-module-builder` using the universal interface.
- Exposes a clean, stable API to Basecamp apps without requiring distribution UI code.

### 6. Basecamp Application (`atlasmirror-app`)
- Native QML application running inside Logos Basecamp.
- Adheres strictly to the Logos Brand Guidelines: monochrome palette (#000000 / #FFFFFF), clear typography, zero distracting Web3 animations.
- Primary views: Regions, Hosting Queue, Downloads, Registry Inspector, Settings, and About.

### 7. Rust CLI (`atlasmirror-cli`)
- Scriptable, standalone binary supporting all administrative and querying functions with `--json` output.
- Features `atlasmirror doctor` for rapid environment diagnosis.
