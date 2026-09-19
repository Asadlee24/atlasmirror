#!/usr/bin/env python3
"""
Unit Test: Checksum Verification and Tamper Detection
Verifies:
1. Live published MD5 fetching from Geofabrik.
2. Streaming MD5 computation on arbitrary-sized files.
3. Tampered-file detection: corrupting 1 byte must immediately fail verification.
"""

import hashlib
import sys
import tempfile
import urllib.request
from pathlib import Path

def fetch_published_md5(region_path: str) -> str:
    md5_url = f"https://download.geofabrik.de/{region_path}-latest.osm.pbf.md5"
    req = urllib.request.Request(md5_url, headers={"User-Agent": "AtlasMirror/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8").strip()
        return content.split()[0].lower()

def compute_file_md5(file_path: Path, chunk_size: int = 64 * 1024) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest().lower()

def verify_file_md5(file_path: Path, expected_md5: str) -> bool:
    computed = compute_file_md5(file_path)
    return computed == expected_md5.lower()

def test_checksum():
    print("Running Milestone 2: Checksum Unit Tests...")

    # 1. Fetch live published MD5
    sample_region = "asia/pakistan"
    print(f"[1/3] Fetching live published MD5 for '{sample_region}'...")
    published_md5 = fetch_published_md5(sample_region)
    print(f"  Live published MD5: {published_md5}")
    assert len(published_md5) == 32, "Invalid MD5 length"

    # 2. Test compute_file_md5 on local test data
    print("[2/3] Verifying compute_file_md5 on test data...")
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf_path = Path(tf.name)
        test_payload = b"OSM_HEADER_PBF_TEST_INTEGRITY_CHECK_DATA_BLOCK" * 1024
        tf.write(test_payload)

    try:
        expected_local_md5 = hashlib.md5(test_payload).hexdigest().lower()
        actual_local_md5 = compute_file_md5(tf_path)
        assert actual_local_md5 == expected_local_md5, "Computed MD5 does not match expected"
        assert verify_file_md5(tf_path, expected_local_md5), "verify_file_md5 failed on matching data"
        print("  Genuine file verification: [PASS]")

        # 3. Tampered file test
        print("[3/3] Tampered-file test: corrupting 1 byte and asserting mismatch...")
        with open(tf_path, "r+b") as f:
            f.seek(42)
            orig_byte = f.read(1)
            corrupted_byte = bytes([(orig_byte[0] ^ 0xFF)])
            f.seek(42)
            f.write(corrupted_byte)

        tampered_result = verify_file_md5(tf_path, expected_local_md5)
        assert not tampered_result, "CRITICAL: Tampered file was incorrectly marked as verified!"
        print("  Tampered file rejection:   [PASS]")

    finally:
        if tf_path.exists():
            tf_path.unlink()

    print("\n[PASS] All Checksum unit tests passed successfully!")

if __name__ == "__main__":
    test_checksum()
