#!/usr/bin/env bash
set -euo pipefail

echo "========================================================"
echo " Running Full AtlasMirror Test Suite"
echo "========================================================"

echo "[1/3] Testing SPEL OSM Registry (Core & Guest logic)..."
cd osm-registry
cargo test --verbose
cd ..

echo "[2/3] Testing AtlasMirror CLI..."
cd atlasmirror-cli
cargo test --verbose
cd ..

echo "[3/3] Testing Predefined Region Schema..."
python3 -c "
import json
data = json.load(open('metadata/regions.json'))
regions = data['regions']
assert len(regions) == 72, f'Expected 72 regions, found {len(regions)}'
for r in regions:
    assert 'path' in r and 'level' in r and 'geofabrik_url' in r and 'md5_url' in r
    if r['level'] == 'country':
        assert r['parent'] is None
    elif r['level'] == 'subregion':
        assert r['parent'] in ['us', 'india', 'china', 'russia']
print('✔ All 72 region schema constraints validated.')
"

echo "========================================================"
echo "✔ All tests passed successfully!"
echo "========================================================"
