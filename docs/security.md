# Security & Threat Model

AtlasMirror implements defense-in-depth across the entire OpenStreetMap snapshot lifecycle.

---

## Threat Analysis & Mitigations

| Threat | Impact | Mitigation in AtlasMirror |
|---|---|---|
| **Malicious / Tampered PBF** | Corrupts consumer GIS software; potential parser exploit | Import-time streaming MD5 verification against Geofabrik's canonical hash; stops before storage or on-chain registration. |
| **Fake Checksum Response** | Attacker serves matching bogus hash for poisoned PBF | Fetches over TLS directly from `download.geofabrik.de`; validates strict 32-character hexadecimal format. |
| **Path Traversal Attacks** | Malicious region string creates/overwrites arbitrary files (e.g. `../../etc/passwd`) | Strict validation against the closed 72-region allowlist in `metadata/regions.json`; all local file paths are normalized and sandboxed. |
| **Memory Exhaustion (DoS)** | Multi-gigabyte PBF crashes client RAM | Fully streaming I/O for download, MD5 hashing, and Logos Storage transfers. Zero buffering of entire files. |
| **Registry Spam / Poisoning** | Unauthorized or malformed on-chain entries | SPEL program bounds string lengths (<= 64 bytes), enforces valid `Country`/`Subregion` level logic, requires non-empty CID, and verifies monotonic timestamps. |
| **Unsafe Shell Interpolation** | Remote command injection if external commands are invoked | No shell commands constructed via string concatenation. All external process invocations use typed argument vectors. |
| **Secret / Key Leakage** | Compromised user credentials or private keys | Zero telemetry, zero hardcoded keys, zero logging of private seed phrases or auth tokens. Sensitive files excluded in `.gitignore`. |
