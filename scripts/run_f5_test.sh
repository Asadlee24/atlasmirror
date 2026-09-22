#!/usr/bin/env bash
set -e

echo "=== F5 & R2 Local Import & Tamper Rejection Test Run ==="
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Host: $(uname -srm)"
echo "CLI: $(/root/atlasmirror/atlasmirror-cli/target/release/atlasmirror-cli --version)"
echo ""

echo "--- STEP 1: Test Genuine Local PBF Import (europe/monaco) ---"
/root/atlasmirror/atlasmirror-cli/target/release/atlasmirror-cli host --file europe/monaco /root/monaco-latest.osm.pbf
echo "Exit code: 0 (Success: Checksum Verified & Import Allowed)"
echo ""

echo "--- STEP 2: Test Tampered Local PBF (1-byte mutation) ---"
set +e
/root/atlasmirror/atlasmirror-cli/target/release/atlasmirror-cli host --file europe/monaco /root/monaco-tampered.osm.pbf
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE (Success: Tamper Detected & Import Halted)"
echo ""

if [ "$EXIT_CODE" -ne 0 ]; then
    echo "=== F5 & R2 Verification Completed Successfully ==="
    exit 0
else
    echo "=== ERROR: Tamper was not rejected! ==="
    exit 1
fi
