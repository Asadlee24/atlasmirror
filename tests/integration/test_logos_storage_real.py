#!/usr/bin/env python3
"""
Integration Test: Real Logos Storage Process
Requires:
- A running Logos Storage daemon/module process (default: http://127.0.0.1:8080 or LOGOS_STORAGE_ENDPOINT)
This test NEVER falls back to a mock HTTP server.
If the real Logos Storage daemon is unavailable, it stops and fails loudly.
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = os.environ.get("LOGOS_STORAGE_ENDPOINT", "http://127.0.0.1:8080")

def check_daemon_alive(endpoint: str) -> bool:
    try:
        req = urllib.request.Request(f"{endpoint}/api/v0/storage/status", headers={"User-Agent": "AtlasMirror/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status in (200, 204)
    except Exception:
        return False

def test_real_logos_storage():
    print(f"Checking for real Logos Storage daemon at {ENDPOINT}...")
    if not check_daemon_alive(ENDPOINT):
        print(f"\n[BLOCKED] Real Logos Storage daemon is NOT running at {ENDPOINT}.")
        print("To run this test:")
        print("  1. Build and run logos-storage-module (or logoscore headless with storage-module).")
        print("  2. Ensure the daemon is listening on " + ENDPOINT)
        print("  3. Re-run: python tests/integration/test_logos_storage_real.py\n")
        print("Integration Status: NOT_VERIFIED (Logos Storage daemon absent)")
        sys.exit(2) # Exit code 2 = Dependency absent / Blocked

    print("[1/3] Uploading real payload to Logos Storage...")
    payload = b"LOGOS_STORAGE_GENUINE_INTEGRITY_TEST_DATA_BLOCK_" * 100
    expected_sha256 = hashlib.sha256(payload).hexdigest()

    upload_req = urllib.request.Request(
        f"{ENDPOINT}/api/v0/storage/upload",
        data=payload,
        headers={"Content-Type": "application/octet-stream"}
    )
    with urllib.request.urlopen(upload_req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        real_cid = res.get("cid")
        assert real_cid, "Logos Storage did not return a valid CID"
        print(f"  Real CID returned by Logos Storage: {real_cid}")

    print(f"[2/3] Retrieving file by CID '{real_cid}' from Logos Storage...")
    download_url = f"{ENDPOINT}/api/v0/storage/download?cid={real_cid}"
    with urllib.request.urlopen(download_url, timeout=30) as resp:
        retrieved_bytes = resp.read()

    print("[3/3] Verifying byte-for-byte equality...")
    retrieved_sha256 = hashlib.sha256(retrieved_bytes).hexdigest()
    assert len(retrieved_bytes) == len(payload), f"Length mismatch: {len(retrieved_bytes)} vs {len(payload)}"
    assert retrieved_sha256 == expected_sha256, f"SHA-256 mismatch: {retrieved_sha256} vs {expected_sha256}"
    print(f"  Exact byte equality verified ({len(retrieved_bytes)} bytes, SHA-256: {retrieved_sha256})")

    print("\n[PASS] Real Logos Storage integration test verified successfully!")

if __name__ == "__main__":
    test_real_logos_storage()
