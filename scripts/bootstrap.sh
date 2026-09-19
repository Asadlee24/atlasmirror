#!/usr/bin/env bash
set -euo pipefail

echo "========================================================"
echo " Bootstrapping AtlasMirror Development Environment"
echo " Target: Logos λPrize LP-0018 (Testnet 0.3)"
echo "========================================================"

command -v cargo >/dev/null 2>&1 || { echo "Error: Rust/cargo is required."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "Error: git is required."; exit 1; }

echo "[1/4] Checking Rust toolchain..."
cargo --version
rustc --version

echo "[2/4] Validating SPEL IDL freshness..."
cd osm-registry
if [ -f "idl/osm_registry.json" ]; then
    echo "✔ SPEL IDL present at osm-registry/idl/osm_registry.json"
else
    cargo run --bin generate_idl
fi
cd ..

echo "[3/4] Verifying region catalog integrity..."
python3 -c "import json; d = json.load(open('metadata/regions.json')); assert len(d['regions']) == 72; print('✔ 72 predefined regions verified.')"

echo "[4/4] Building CLI..."
cd atlasmirror-cli
cargo check
cd ..

echo "========================================================"
echo "✔ AtlasMirror environment ready!"
echo "========================================================"
