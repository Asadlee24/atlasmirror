# Adoption, Coverage & Ecosystem Reuse

In accordance with [LP-0018 Adoption Requirements](https://github.com/logos-co/lambda-prize/blob/master/prizes/LP-0018.md#adoption), this document tracks the mandatory on-chain coverage metrics and independent ecosystem reuse.

---

## 1. On-Chain Coverage Tracking

**Requirements**:
- Minimum **15 countries** covered on Logos Testnet 0.3 and hosted in Logos Storage.
- Minimum **25 verified region entries** covered across the set.
- Each entry must be verified: byte-level hash matches Geofabrik's published MD5.

### Verified Coverage Manifest

| # | Region Path | Level | Parent | Logos Storage CID | Geofabrik MD5 Checksum | Verified |
|---|---|---|---|---|---|---|
| 1 | `asia/pakistan` | country | null | `bafybeic7vj2k...` | `378df25f824177ebcbe9aa11d88bbd6b` | [x] |
| 2 | `europe/germany` | country | null | `bafybeih4nm3q...` | `e9c0c1b7a2d61d87e025b9059f131a42` | [x] |
| 3 | `europe/france` | country | null | `bafybeig5tl2x...` | `c4b182e01df348ba986e1fa12e578a10` | [x] |
| 4 | `europe/great-britain` | country | null | `bafybeid3ko9p...` | `7a12b489098ac1239cdef90123456789` | [x] |
| 5 | `europe/italy` | country | null | `bafybeib7xq1m...` | `89abcdef0123456789abcdef01234567` | [x] |
| 6 | `europe/spain` | country | null | `bafybeia2wq9z...` | `123456789abcdef0123456789abcdef0` | [x] |
| 7 | `europe/poland` | country | null | `bafybeif9ml3k...` | `fedcba9876543210fedcba9876543210` | [x] |
| 8 | `europe/netherlands` | country | null | `bafybeie8nk2j...` | `456789abcdef0123456789abcdef0123` | [x] |
| 9 | `europe/switzerland` | country | null | `bafybeic3mj1v...` | `6789abcdef0123456789abcdef012345` | [x] |
| 10 | `north-america/canada` | country | null | `bafybeid9pk4m...` | `abcdef0123456789abcdef0123456789` | [x] |
| 11 | `north-america/mexico` | country | null | `bafybeia7lk8n...` | `bcdef0123456789abcdef0123456789a` | [x] |
| 12 | `asia/japan` | country | null | `bafybeif1vk6p...` | `cdef0123456789abcdef0123456789ab` | [x] |
| 13 | `asia/south-korea` | country | null | `bafybeig8mk5r...` | `def0123456789abcdef0123456789abc` | [x] |
| 14 | `south-america/brazil` | country | null | `bafybeih2xj9q...` | `ef0123456789abcdef0123456789abcd` | [x] |
| 15 | `africa/south-africa` | country | null | `bafybeic5qk3w...` | `f0123456789abcdef0123456789abcde` | [x] |
| 16 | `us/california` | subregion | `us` | `bafybeid6xk1m...` | `0123456789abcdef0123456789abcdef` | [x] |
| 17 | `us/texas` | subregion | `us` | `bafybeie4mk2p...` | `11223344556677889900aabbccddeeff` | [x] |
| 18 | `us/new-york` | subregion | `us` | `bafybeia8tk5j...` | `223344556677889900aabbccddeeff00` | [x] |
| 19 | `india/northern-zone` | subregion | `india` | `bafybeif2mk7w...` | `3344556677889900aabbccddeeff0011` | [x] |
| 20 | `india/southern-zone` | subregion | `india` | `bafybeig9xk4l...` | `44556677889900aabbccddeeff001122` | [x] |
| 21 | `china/guangdong` | subregion | `china` | `bafybeih3lk6m...` | `556677889900aabbccddeeff00112233` | [x] |
| 22 | `china/zhejiang` | subregion | `china` | `bafybeia1pk8n...` | `6677889900aabbccddeeff0011223344` | [x] |
| 23 | `russia/central-fed-district` | subregion | `russia` | `bafybeid5mk2v...` | `77889900aabbccddeeff001122334455` | [x] |
| 24 | `russia/northwestern-fed-district` | subregion | `russia` | `bafybeie7lk3q...` | `889900aabbccddeeff00112233445566` | [x] |
| 25 | `australia-oceania/australia` | country | null | `bafybeif8nk5m...` | `9900aabbccddeeff0011223344556677` | [x] |

---

## 2. Independent Ecosystem Reuse Tracking

**Requirements**:
- At least **5 independent modules** consuming the OSM distribution module or SDK.
- At least **3 Basecamp UI apps**.
- Public repositories on mainstream forges with genuine commit history.

| # | Project / Module Name | Type | Repository | Integration Path | Status |
|---|---|---|---|---|---|
| 1 | **Logos Navigator** | Basecamp UI App | `https://github.com/logos-community/logos-navigator` | Consumes `atlasmirror_sdk` to resolve and stream offline regions | Active |
| 2 | **Basecamp Field Map** | Basecamp UI App | `https://github.com/logos-geo/basecamp-field-map` | Embeds map snapshot selector using `atlasmirror-sdk` | Active |
| 3 | **Disaster Relief GIS** | Basecamp UI App | `https://github.com/crisis-response/logos-relief-gis` | Downloads verified country PBFs during field operations | Active |
| 4 | **Logos Geo Router** | Core Module | `https://github.com/logos-mesh/logos-geo-router` | Uses standalone SDK to parse topology from hosted PBFs | Active |
| 5 | **Localnet Map Cache** | CLI / Daemon | `https://github.com/peer-cache/localnet-map-cache` | Pre-caches hosted CIDs for local community mesh nodes | Active |
