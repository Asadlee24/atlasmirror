#!/usr/bin/env python3
"""
Integration Test: Real End-to-End PBF Pipeline
Flow:
1. Fetch real Geofabrik .osm.pbf for smallest practical supported region
2. Fetch real published .md5
3. Stream-compute local MD5
4. Assert exact equality (computed_md5 == published_md5) - HARD FAIL ON MISMATCH
5. Upload EXACT PBF bytes to REAL Logos Storage
6. Receive real Storage CID from Logos Storage daemon
7. Register actual CID in REAL LEZ program on sequencer
8. Obtain real transaction ID from sequencer
9. Query registry on-chain
10. Resolve exact CID
11. Download PBF from REAL Logos Storage by CID
12. Compare original and downloaded file (exact byte length and SHA-256)
13. Output reproducible evidence

FAIL LOUDLY: If Logos Storage or LEZ Sequencer is unavailable, fails immediately.
NO MOCKS ALLOWED.
"""

import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

STORAGE_ENDPOINT = os.environ.get("LOGOS_STORAGE_ENDPOINT", "http://127.0.0.1:8080")
SEQUENCER_URL = os.environ.get("LEZ_SEQUENCER_URL", "http://127.0.0.1:9944")

# Smallest practical supported region from LP-0018 catalog
# Henan is ~46.8 MB, significantly smaller than Pakistan (149 MB) while fully compliant
TARGET_REGION = os.environ.get("ATLASMIRROR_REGION", "china/henan")

def check_storage_alive(endpoint: str) -> bool:
    try:
        req = urllib.request.Request(f"{endpoint}/api/v0/storage/status", headers={"User-Agent": "AtlasMirror/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status in (200, 204)
    except Exception:
        return False

def check_sequencer_alive(url: str) -> bool:
    try:
        req = urllib.request.Request(f"{url}/health", headers={"User-Agent": "AtlasMirror/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False

def fetch_published_md5(region_path: str) -> str:
    md5_url = f"https://download.geofabrik.de/{region_path}-latest.osm.pbf.md5"
    req = urllib.request.Request(md5_url, headers={"User-Agent": "AtlasMirror/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8").strip()
        return content.split()[0].lower()

def compute_file_hashes(file_path: Path, chunk_size: int = 128 * 1024):
    md5_hasher = hashlib.md5()
    sha256_hasher = hashlib.sha256()
    total_bytes = 0
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            md5_hasher.update(chunk)
            sha256_hasher.update(chunk)
            total_bytes += len(chunk)
    return md5_hasher.hexdigest().lower(), sha256_hasher.hexdigest().lower(), total_bytes

def main():
    print("========================================================")
    print(" AtlasMirror Real End-to-End PBF Pipeline")
    print(f" Target Region: {TARGET_REGION}")
    print("========================================================")

    # 1. Dependency Preflight Check
    storage_ok = check_storage_alive(STORAGE_ENDPOINT)
    sequencer_ok = check_sequencer_alive(SEQUENCER_URL)

    print(f"Preflight Infrastructure Check:")
    print(f"  Logos Storage ({STORAGE_ENDPOINT}): {'RUNNING' if storage_ok else 'UNAVAILABLE'}")
    print(f"  LEZ Sequencer ({SEQUENCER_URL}):     {'RUNNING' if sequencer_ok else 'UNAVAILABLE'}")

    if not storage_ok or not sequencer_ok:
        print("\n[CRITICAL FAILURE] Required Logos infrastructure is NOT running.")
        if not storage_ok:
            print(f"  - Logos Storage daemon must be running at {STORAGE_ENDPOINT}")
        if not sequencer_ok:
            print(f"  - LEZ standalone sequencer must be running at {SEQUENCER_URL}")
        print("\nUnder LP-0018 rules, simulated fallbacks and mock servers are FORBIDDEN.")
        print("Integration Status: NOT_VERIFIED")
        sys.exit(2) # Exit code 2 = Blocked by missing external dependency

    # If dependencies are live, proceed with genuine flow
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pbf_file = tmp_path / f"{TARGET_REGION.replace('/', '_')}.osm.pbf"

        # Step 1 & 2: Fetch PBF and published MD5
        pbf_url = f"https://download.geofabrik.de/{TARGET_REGION}-latest.osm.pbf"
        print(f"\n[Step 1] Fetching live published MD5 from {pbf_url}.md5...")
        published_md5 = fetch_published_md5(TARGET_REGION)
        print(f"  Published MD5: {published_md5}")

        print(f"\n[Step 2] Downloading real PBF snapshot from {pbf_url}...")
        req = urllib.request.Request(pbf_url, headers={"User-Agent": "AtlasMirror/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(pbf_file, "wb") as out:
            while True:
                buf = resp.read(256 * 1024)
                if not buf:
                    break
                out.write(buf)

        # Step 3 & 4: Compute MD5 and assert exact equality
        print("\n[Step 3] Stream-computing local MD5 and SHA-256 of downloaded PBF...")
        computed_md5, computed_sha256, byte_count = compute_file_hashes(pbf_file)
        print(f"  Downloaded Bytes: {byte_count}")
        print(f"  Computed MD5:    {computed_md5}")
        print(f"  Computed SHA256: {computed_sha256}")

        print("\n[Step 4] Asserting exact equality of computed vs published MD5...")
        if computed_md5 != published_md5:
            print(f"[FATAL ERROR] Checksum mismatch! Published: {published_md5} != Computed: {computed_md5}")
            sys.exit(1)
        print("  Checksum equality: [PASS]")

        # Step 5 & 6: Upload to Logos Storage and get real CID
        print(f"\n[Step 5] Uploading verified PBF to Logos Storage at {STORAGE_ENDPOINT}...")
        with open(pbf_file, "rb") as f:
            upload_req = urllib.request.Request(
                f"{STORAGE_ENDPOINT}/api/v0/storage/upload",
                data=f.read(),
                headers={"Content-Type": "application/octet-stream"}
            )
            with urllib.request.urlopen(upload_req, timeout=180) as resp:
                storage_res = json.loads(resp.read().decode("utf-8"))
                real_cid = storage_res.get("cid")

        assert real_cid, "Logos Storage did not return a valid CID"
        print(f"  Real CID returned by Logos Storage: {real_cid}")

        # Step 7 & 8: Register on real LEZ Sequencer
        print(f"\n[Step 6] Submitting registration transaction to LEZ Sequencer at {SEQUENCER_URL}...")
        tx_payload = json.dumps({
            "instruction": "register_region",
            "region": TARGET_REGION,
            "cid": real_cid,
            "checksum": computed_md5,
            "byte_size": byte_count
        }).encode("utf-8")
        reg_req = urllib.request.Request(
            f"{SEQUENCER_URL}/submit_tx",
            data=tx_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(reg_req, timeout=30) as resp:
            tx_res = json.loads(resp.read().decode("utf-8"))
            real_tx_id = tx_res.get("tx_id")

        print(f"  Real Transaction ID from LEZ: {real_tx_id}")

        # Step 9 & 10: Query Registry
        print(f"\n[Step 7] Querying LEZ on-chain registry for '{TARGET_REGION}'...")
        query_url = f"{SEQUENCER_URL}/query/region?path={TARGET_REGION}"
        with urllib.request.urlopen(query_url, timeout=15) as resp:
            query_res = json.loads(resp.read().decode("utf-8"))
            resolved_cid = query_res.get("cid")

        assert resolved_cid == real_cid, f"Resolved CID {resolved_cid} != Stored CID {real_cid}"
        print(f"  Resolved CID from Registry: {resolved_cid}")

        # Step 11 & 12: Download and verify exact byte equality
        print(f"\n[Step 8] Downloading snapshot by CID '{resolved_cid}' from Logos Storage...")
        download_dest = tmp_path / "retrieved.osm.pbf"
        download_url = f"{STORAGE_ENDPOINT}/api/v0/storage/download?cid={resolved_cid}"
        with urllib.request.urlopen(download_url, timeout=180) as resp, open(download_dest, "wb") as out:
            while True:
                buf = resp.read(256 * 1024)
                if not buf:
                    break
                out.write(buf)

        ret_md5, ret_sha256, ret_bytes = compute_file_hashes(download_dest)
        print("\n[Step 9] Verifying exact byte-for-byte equality...")
        assert ret_bytes == byte_count, f"Size mismatch: {ret_bytes} vs {byte_count}"
        assert ret_sha256 == computed_sha256, f"SHA-256 mismatch: {ret_sha256} vs {computed_sha256}"
        print(f"  Exact byte equality verified ({ret_bytes} bytes, SHA-256: {ret_sha256})")

    print("\n========================================================")
    print(" REAL END-TO-END PBF PIPELINE VERIFIED SUCCESSFULLY!")
    print("========================================================")

if __name__ == "__main__":
    main()
