# Adoption, Coverage & Ecosystem Reuse

In accordance with [LP-0018 Adoption Requirements](https://github.com/logos-co/lambda-prize/blob/master/prizes/LP-0018.md#adoption), this document tracks the mandatory on-chain coverage metrics (A1) and independent ecosystem reuse (A2).

---

## 1. On-Chain Coverage Tracking (LP-0018 A1)

**Requirements**:
- Minimum **15 countries** covered on Logos Testnet 0.3 and hosted in Logos Storage.
- Minimum **25 verified region entries** covered across the set.
- Each entry must be verified: byte-level hash matches Geofabrik's published MD5, real Logos Storage CID hosted, registered on canonical Logos Testnet, and 100% retrievable externally.

### Current Verified Coverage Manifest (LP-0018 Closed Set Audit)

> [!NOTE]
> Coverage is strictly measured against the frozen **72 Predefined Regions closed set** specified in [LP-0018 Predefined Regions](#predefined-regions-closed-set). Entries outside this closed set are preserved in the ecosystem ledger as `NON_COUNTING_EXTRA` and excluded from official A1 totals.

#### Officially Counting Closed-Set Entries (A1 Metric)

| # | Region Path | Level | Parent | Country | Size (Bytes) | Published Geofabrik MD5 | Logos Storage CID | Testnet Block | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `china/henan` | subregion | china | China | 49,157,919 | `0055ebfc7f14585c56d53a88062d5814` | `zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny` | 16949 | **A1_VERIFIED** |
| 2 | `africa/ethiopia` | country | null | Ethiopia | 139,741,759 | `c2e00ecddf7ae4ed89bf05bf104d3f10` | `zDvZRwzm7o1JcgDFrsC8zYrEYnhPkY52qThJLjojMvswjj8pVjPX` | 18252 | **A1_VERIFIED** |
| 3 | `asia/pakistan` | country | null | Pakistan | 156,230,629 | `d63c9409c20924d0813b81266eb2f5ad` | `zDvZRwzm9WQQrvAZL4NavbFXjmbHTFNyho68zPMxKsCvfGEn2LbD` | 18293 | **A1_VERIFIED** |
| 4 | `europe/bulgaria` | country | null | Bulgaria | 174,092,672 | `25801cfabc5bfe8e1ae56ded0fa5ed13` | `zDvZRwzm72Y7GBdMzdT7ibQWieQSmUhvk54VHfhcsUDcqnPhma51` | 18337 | **A1_VERIFIED** |
| 5 | `africa/egypt` | country | null | Egypt | 178,421,161 | `04a4d557c902a5f29ba0e7a1394e0232` | `zDvZRwzmDbJCqSLbyt1Fw4mSvrGFkJGBLaBAogpw8VF66wA469mm` | 18353 | **A1_VERIFIED** |
| 6 | `asia/iran` | country | null | Iran | 229,501,907 | `e503562d3826bec67e6f87b899da4098` | `zDvZRwzkybLEXZoEjDetaF4yKT73jszhgkMTboXedKCt4En1gUKV` | 18390 | **A1_VERIFIED** |
| 7 | `africa/morocco` | country | null | Morocco | 243,471,217 | `ac60aed8b36bac264f2c17c89a584b94` | `zDvZRwzmD3VCUxT9UqAh7mXpT4XmWarwKBFR6p2eRiY7PxjQg3kt` | 18444 | **A1_VERIFIED** |
| 8 | `asia/malaysia-singapore-brunei` | country | null | Malaysia | 251,169,608 | `203cebee0dbaa4e8464b777cd10698e6` | `zDvZRwzkxgamWxqXcSCp2m8Z5WicCRd79MVy8B3duQ8gCZJSc11Y` | 18481 | **A1_VERIFIED** |

**A1 Valid Closed-Set Count**: **8 / 25 entries** across **8 represented countries**.
**Status**: `IN_PROGRESS_CLOSED_SET_REMEDIATION` (Active expansion underway to reach 25 valid closed-set entries across ≥15 countries).

#### Supplementary On-Chain & Storage Entries (Preserved, Marked `NON_COUNTING_EXTRA`)

> These genuine regions were uploaded, verified, and registered on Logos Testnet 0.3, but originate outside the official closed set (e.g. small European / Central American states). They are preserved on the Logos DHT and ledger, but do not contribute to the 25-entry A1 score.

| # | Region Path | Country | Size (Bytes) | Logos Storage CID | Testnet Block | Status |
|---|---|---|---|---|---|---|
| E1 | `europe/malta` | Malta | 8,914,777 | `zDvZRwzm66tTqLYiHoTD3VTiAgRQZhEjEsFdXqSFyPdvzkp57Wi3` | 18549 | `NON_COUNTING_EXTRA` |
| E2 | `central-america/belize` | Belize | 18,262,587 | `zDvZRwzm7Z6itHsGr4c8SuTbvo7ehQQefCrZdvMasJk3FmL8fQez` | 18570 | `NON_COUNTING_EXTRA` |
| E3 | `europe/macedonia` | North Macedonia | 29,716,707 | `zDvZRwzmAnj1vZ5wsTrts84vhLyANg5QDA9pwr2AHJXMiZK3zKSp` | 18575 | `NON_COUNTING_EXTRA` |
| E4 | `europe/kosovo` | Kosovo | 30,756,603 | `zDvZRwzm3wzchHb9wx7nUsEpk84WiyU1HsnAhsn33swcJZSR94Cv` | 18869 | `NON_COUNTING_EXTRA` |
| E5 | `asia/jordan` | Jordan | 31,025,485 | `zDvZRwzm6MwoW2D4XMndjWQf2LpJQBmiZZufCLdShbswbD3DE1NK` | 18879 | `NON_COUNTING_EXTRA` |
| E6 | `europe/montenegro` | Montenegro | 34,401,613 | `zDvZRwzm7tnpibhnK3xXWXXSohtNrcDzAi1p7P1DMPEZEVEkw29L` | 18908 | `NON_COUNTING_EXTRA` |
| E7 | `central-america/el-salvador` | El Salvador | 35,039,469 | `zDvZRwzm4zWDM9qx8xKLDeio9iQ6j5NSRBX5KTwjLisew5tqLAnR` | 18932 | `NON_COUNTING_EXTRA` |
| E8 | `central-america/panama` | Panama | 36,190,818 | `zDvZRwzm5WVgFx2S4UJibpBTc5hby1ApFCisoiaDxuXuzivGcbSf` | 18936 | `NON_COUNTING_EXTRA` |
| E9 | `europe/cyprus` | Cyprus | 37,394,174 | `zDvZRwzmDHgovpf7wPvvWDfwVHiQWzUzW4cwaz6mgYRY1DNH9jzv` | 18942 | `NON_COUNTING_EXTRA` |
| E10 | `central-america/costa-rica` | Costa Rica | 38,970,721 | `zDvZRwzm6iHE4SCa6ZN1hf6jYxKRPJoTeUyoWsb85mPMYeFCnA4W` | 18948 | `NON_COUNTING_EXTRA` |
| E11 | `asia/azerbaijan` | Azerbaijan | 46,199,081 | `zDvZRwzmCC9F9gCZS9LFy41LSDFnvRELWA2Ufj3XL74vANmDvieC` | 18952 | `NON_COUNTING_EXTRA` |
| E12 | `europe/luxembourg` | Luxembourg | 47,554,636 | `zDvZRwzm5Aoyj7sWd2mrVNHNrU1RRdUhmMsaPEadCMNghbR1C6A8` | 18956 | `NON_COUNTING_EXTRA` |
| E13 | `asia/tajikistan` | Tajikistan | 48,435,989 | `zDvZRwzmAynrFYf1f5MkJJFgK7Xn8pkTBUuHgUgR3fLW2zcvT6AP` | 18960 | `NON_COUNTING_EXTRA` |
| E14 | `asia/lebanon` | Lebanon | 52,497,605 | `zDvZRwzm1oidxJtpGW4zFTpWkte5KdmQDygUJNQBbfHu7yFEGRTF` | 18964 | `NON_COUNTING_EXTRA` |
| E15 | `asia/armenia` | Armenia | 53,186,007 | `zDvZRwzmCRBHtCD5xRDh86525iUpW236xw4osztJpCes3xWxMyNK` | 18968 | `NON_COUNTING_EXTRA` |
| E16 | `europe/albania` | Albania | 54,070,075 | `zDvZRwzkyMTaCuE8K9FP1r4YPs8i37Z91NGuycpCmhrtwupMRMHw` | 18972 | `NON_COUNTING_EXTRA` |
| E17 | `central-america/nicaragua` | Nicaragua | 61,444,052 | `zDvZRwzkxK4PdRtekurF3iKtn7YUKMSPiTDZzPTGnD4tcgvXZRgp` | 18977 | `NON_COUNTING_EXTRA` |

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
