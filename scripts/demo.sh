#!/usr/bin/env bash
set -euo pipefail

echo "========================================================"
echo " AtlasMirror Real End-to-End Pipeline Demo"
echo " Flow: Geofabrik -> Checksum -> Storage -> Register -> Query -> Download"
echo "========================================================"

# Run the real end-to-end integration pipeline
# Requires live Logos Storage daemon and LEZ sequencer. Never uses mocks.
python3 tests/integration/test_e2e_real.py || python tests/integration/test_e2e_real.py

echo "========================================================"
echo " Real end-to-end pipeline completed successfully!"
echo "========================================================"

