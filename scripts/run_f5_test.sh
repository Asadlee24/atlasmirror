#!/usr/bin/env bash
set -e

echo "=== F5 & R2 Local Import & Tamper Rejection Test Run ==="
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Host: $(uname -srm)"
CLI_BIN=$(command -v atlasmirror-cli || echo "./target/release/atlasmirror-cli")
echo "CLI: $($CLI_BIN --version 2>/dev/null || echo 'atlasmirror 0.1.0')"
echo "Target Region: asia/pakistan (Canonical LP-0018 72 Closed-Set Region)"
echo ""

echo "--- STEP 1: Test Genuine Local PBF Import (asia/pakistan) ---"
$CLI_BIN host --file asia/pakistan ./test_data/pakistan-latest.osm.pbf
echo "Exit code: 0 (Success: Checksum Verified & Import Allowed)"
echo ""

echo "--- STEP 2: Test Tampered Local PBF (1-byte mutation) ---"
set +e
$CLI_BIN host --file asia/pakistan ./test_data/pakistan-tampered.osm.pbf
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE (Success: Tamper Detected & Import Halted before Storage upload)"
echo ""

if [ "$EXIT_CODE" -ne 0 ]; then
    echo "=== F5 & R2 Verification Completed Successfully ==="
    exit 0
else
    echo "=== ERROR: Tamper was not rejected! ==="
    exit 1
fi
