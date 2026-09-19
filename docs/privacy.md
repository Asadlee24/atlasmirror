# Privacy & Anonymity

AtlasMirror adheres to the strict privacy principles of the Logos Network.

---

## Core Privacy Guarantees

1. **Zero Mandatory Analytics & Telemetry**:
   - By default, AtlasMirror does not collect, store, or transmit any telemetry, usage metrics, or crash reports.
   - Any optional analytics in settings is strictly **opt-in** and disabled by default.

2. **No Tracking of User Map Queries**:
   - Looking up regions, parents, or CIDs queries the public on-chain LEZ registry or local state. No centralized telemetry server is queried to monitor what geography a user is interested in.

3. **Decoupled Hosting Identity**:
   - In Logos LEZ, transactions can be submitted using private/anonymous accounts where supported. The registry records the snapshot CID and geographic metadata, not the user's personal identity or IP address.

4. **Decentralized Storage Retrieval**:
   - Downloading hosted snapshots by CID leverages peer-to-peer Logos Storage, avoiding centralized download logs common to traditional mirror hosts.
