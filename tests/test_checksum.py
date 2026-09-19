import urllib.request
import hashlib
import tempfile
import os
import sys

def fetch_published_md5(region_path: str) -> str:
    url = f"https://download.geofabrik.de/{region_path}-latest.osm.pbf.md5"
    req = urllib.request.Request(url, headers={"User-Agent": "AtlasMirror/0.1"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode("utf-8").strip()
    
    parts = content.split()
    if not parts:
        raise ValueError(f"Empty checksum response from {url}")
    
    hash_str = parts[0].strip().lower()
    if len(hash_str) != 32 or not all(c in "0123456789abcdef" for c in hash_str):
        raise ValueError(f"Invalid MD5 hash format: '{hash_str}'")
    
    return hash_str

def compute_file_md5(file_path: str) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(64 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest().lower()

def verify_md5(file_path: str, expected_md5: str) -> bool:
    computed = compute_file_md5(file_path)
    return computed == expected_md5.lower()

def main():
    print("Running Milestone 2: Real Checksum Tests...")

    # Test 1: Fetch real published MD5 for asia/pakistan
    print("[1/3] Fetching live published MD5 for 'asia/pakistan'...")
    real_md5 = fetch_published_md5("asia/pakistan")
    print(f"  Live published MD5: {real_md5}")
    assert len(real_md5) == 32, "Published MD5 must be 32 characters"

    # Test 2: Compute hash on genuine local content
    print("[2/3] Verifying compute_file_md5 on test data...")
    test_data = b"OpenStreetMap verified snapshot test bytes"
    expected_hash = hashlib.md5(test_data).hexdigest().lower()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(test_data)
        tmp_path = tmp.name

    try:
        assert verify_md5(tmp_path, expected_hash) is True, "Valid checksum must verify"
        print("  Genuine file verification: [PASS]")

        # Test 3: Tampered file test - proving mismatch fails!
        print("[3/3] Tampered-file test: corrupting 1 byte and asserting mismatch...")
        with open(tmp_path, "r+b") as f:
            f.seek(0)
            f.write(b"X") # Tamper first byte

        assert verify_md5(tmp_path, expected_hash) is False, "Tampered file MUST NOT verify!"
        print("  Tampered file rejection:   [PASS]")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    print("\n[PASS] All Milestone 2 real checksum tests passed successfully!")

if __name__ == "__main__":
    main()
