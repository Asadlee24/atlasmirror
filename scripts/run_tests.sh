#!/usr/bin/env bash
set -e
export PATH="/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:$PATH"

echo "========================================================"
echo " AtlasMirror Full Automated Test & Verification Suite"
echo "========================================================"

echo "=== 1. SPEL On-Chain OSM Registry Tests ==="
cd /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry
cargo test --workspace

echo "=== 2. Predefined 72-Region Catalog Validation ==="
cd /mnt/c/Users/Aftab/Desktop/atlasmirror
python3 tests/unit/validate_catalog.py

echo "=== 3. Unit Tests (Geofabrik, Storage, Checksum, Model) ==="
python3 tests/unit/test_checksum.py
python3 tests/unit/test_geofabrik.py
python3 tests/unit/test_registry_model.py
python3 tests/unit/test_storage_mock.py

echo "=== 4. Rust CLI Tests ==="
cd /mnt/c/Users/Aftab/Desktop/atlasmirror/atlasmirror-cli
cargo test

echo "========================================================"
echo " [PASS] ALL VERIFICATION TESTS PASSED SUCCESSFULLY!"
echo "========================================================"
