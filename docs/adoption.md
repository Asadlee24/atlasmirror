# Adoption, Coverage & Ecosystem Reuse

In accordance with [LP-0018 Adoption Requirements](https://github.com/logos-co/lambda-prize/blob/master/prizes/LP-0018.md#adoption), this document tracks the mandatory on-chain coverage metrics (A1) and independent ecosystem reuse (A2).

---

## 1. On-Chain Coverage Tracking (LP-0018 A1)

**Requirements**:
- Minimum **15 countries** covered on Logos Testnet 0.3 and hosted in Logos Storage.
- Minimum **25 verified region entries** covered across the set.
- Each entry must be verified: byte-level hash matches Geofabrik's published MD5, real Logos Storage CID hosted, registered on canonical Logos Testnet, and 100% retrievable externally.

### Current Verified Coverage Manifest

> [!NOTE]
> Only genuinely proven, on-chain verified, and externally retrieved entries are recorded below. All entries are backed by exact SHA256/MD5 match against upstream Geofabrik and queryable on the canonical Logos Testnet (`T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci`).

| # | Region Path | Level | Parent | Country | Size (Bytes) | Published Geofabrik MD5 | Logos Storage CID | Testnet Block | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `china/henan` | subregion | `china` | China | 49,157,919 | `0055ebfc7f14585c56d53a88062d5814` | `zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny` | 16949 | **VERIFIED** |

*Pipeline status: In progress. The automated pipeline (`scripts/run_a1_coverage.py`) is executing the remaining 24 regions (covering 24 additional distinct countries) through the full verification lifecycle.*

---

## 2. Independent Ecosystem Reuse Tracking (LP-0018 A2)

**Requirements**:
- At least **5 independent modules** consuming the OSM distribution module or SDK.
- At least **3 Basecamp UI apps**.
- Public repositories on mainstream forges with genuine commit history and verifiable integration.

### Ecosystem Integration Tracking Table

> [!IMPORTANT]
> A2 requires verifiable, genuine independent ecosystem integrations. No placeholder or hypothetical entries are accepted. The tracking table below remains in pending status until independent external repositories integrate AtlasMirror.

| # | Project / Module Name | Type | Repository | Integration Path | Status |
|---|---|---|---|---|---|
| — | *(Pending external integration)* | Basecamp UI App | — | — | `PENDING` |
| — | *(Pending external integration)* | Basecamp UI App | — | — | `PENDING` |
| — | *(Pending external integration)* | Basecamp UI App | — | — | `PENDING` |
| — | *(Pending external integration)* | Core Module | — | — | `PENDING` |
| — | *(Pending external integration)* | CLI / Daemon | — | — | `PENDING` |

**Current A2 Status**: `NOT_STARTED / PENDING` (awaiting real independent ecosystem consumer deployments).
