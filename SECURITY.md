# Security Policy

## Reporting Vulnerabilities

Security is foundational to AtlasMirror and the Logos decentralized ecosystem. If you discover a security vulnerability, please do NOT disclose it publicly on GitHub issues or social channels.

Please report vulnerabilities via encrypted email or direct message to the maintainers:
- **Email**: `security@atlasmirror.org` (or open a GitHub Security Advisory)
- **Response Window**: Within 48 hours

## Threat Model

AtlasMirror explicitly mitigates the following threat vectors:

1. **Malicious or Tampered PBF Files**:
   - Every file downloaded from Geofabrik is hashed and verified against the published MD5 before it is uploaded to Logos Storage or registered on-chain.
   - Once stored, content-addressing (CID) provides cryptographic immutability.
2. **Fake Checksum Responses**:
   - Checksums are retrieved over TLS from Geofabrik's canonical endpoints.
   - Any checksum parsing failure or mismatch immediately halts the pipeline.
3. **Path Traversal & Malicious File Names**:
   - Region paths are strictly validated against the closed allowlist in `metadata/regions.json`.
   - Local output paths are sanitized; no arbitrary file overwrite or directory escape is permitted.
4. **Oversized Files & Memory Exhaustion**:
   - PBF files can exceed 10 GB. All downloads, checksum calculations, and storage transfers are strictly **streamed** in bounded chunks. PBF files are never buffered entirely in RAM.
5. **On-Chain Registry Spam & Manipulation**:
   - The SPEL LEZ registry program enforces strict limits: bounded string lengths, valid region levels (`country` or `subregion`), valid parent relationships, non-empty CIDs, and monotonic timestamp sorting.
6. **Credential & Secret Protection**:
   - No private keys, mnemonics, or tokens are logged or tracked in Git.
   - Zero telemetry by default.
