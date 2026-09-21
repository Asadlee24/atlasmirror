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
| 1 | `china/henan` | subregion | china | China | 49,157,919 | `0055ebfc7f14585c56d53a88062d5814` | `zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny` | 16949 | **VERIFIED** |
| 2 | `africa/ethiopia` | country | null | Ethiopia | 139,741,759 | `c2e00ecddf7ae4ed89bf05bf104d3f10` | `zDvZRwzm7o1JcgDFrsC8zYrEYnhPkY52qThJLjojMvswjj8pVjPX` | 18252 | **VERIFIED** |
| 3 | `asia/pakistan` | country | null | Pakistan | 156,230,629 | `d63c9409c20924d0813b81266eb2f5ad` | `zDvZRwzm9WQQrvAZL4NavbFXjmbHTFNyho68zPMxKsCvfGEn2LbD` | 18293 | **VERIFIED** |
| 4 | `europe/bulgaria` | country | null | Bulgaria | 174,092,672 | `25801cfabc5bfe8e1ae56ded0fa5ed13` | `zDvZRwzm72Y7GBdMzdT7ibQWieQSmUhvk54VHfhcsUDcqnPhma51` | 18337 | **VERIFIED** |
| 5 | `africa/egypt` | country | null | Egypt | 178,421,161 | `04a4d557c902a5f29ba0e7a1394e0232` | `zDvZRwzmDbJCqSLbyt1Fw4mSvrGFkJGBLaBAogpw8VF66wA469mm` | 18353 | **VERIFIED** |
| 6 | `asia/iran` | country | null | Iran | 229,501,907 | `e503562d3826bec67e6f87b899da4098` | `zDvZRwzkybLEXZoEjDetaF4yKT73jszhgkMTboXedKCt4En1gUKV` | 18390 | **VERIFIED** |
| 7 | `africa/morocco` | country | null | Morocco | 243,471,217 | `ac60aed8b36bac264f2c17c89a584b94` | `zDvZRwzmD3VCUxT9UqAh7mXpT4XmWarwKBFR6p2eRiY7PxjQg3kt` | 18444 | **VERIFIED** |
| 8 | `asia/malaysia-singapore-brunei` | country | null | Malaysia | 251,169,608 | `203cebee0dbaa4e8464b777cd10698e6` | `zDvZRwzkxgamWxqXcSCp2m8Z5WicCRd79MVy8B3duQ8gCZJSc11Y` | 18481 | **VERIFIED** |
| 9 | `europe/malta` | country | null | Malta | 8,914,777 | `7315b7284ffe89c8286882398eb2394b` | `zDvZRwzm66tTqLYiHoTD3VTiAgRQZhEjEsFdXqSFyPdvzkp57Wi3` | 18549 | **VERIFIED** |
| 10 | `central-america/belize` | country | null | Belize | 18,262,587 | `871fd979e6f5112d2fdadd578b0ecd3d` | `zDvZRwzm7Z6itHsGr4c8SuTbvo7ehQQefCrZdvMasJk3FmL8fQez` | 18570 | **VERIFIED** |
| 11 | `europe/macedonia` | country | null | North Macedonia | 29,716,707 | `10ccfc90c9d91cb2f913d289c51bbb0e` | `zDvZRwzmAnj1vZ5wsTrts84vhLyANg5QDA9pwr2AHJXMiZK3zKSp` | 18575 | **VERIFIED** |
| 12 | `europe/kosovo` | country | null | Kosovo | 30,756,603 | `fcd283f004aa4c359d16110cbdfce275` | `zDvZRwzm3wzchHb9wx7nUsEpk84WiyU1HsnAhsn33swcJZSR94Cv` | 18869 | **VERIFIED** |
| 13 | `asia/jordan` | country | null | Jordan | 31,025,485 | `55aed7483c97278ad17b73509481f916` | `zDvZRwzm6MwoW2D4XMndjWQf2LpJQBmiZZufCLdShbswbD3DE1NK` | 18879 | **VERIFIED** |

*Pipeline status: In progress (13/25 regions verified across 13/15 countries).*

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
