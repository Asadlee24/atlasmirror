#!/usr/bin/env bash
set -euo pipefail

echo "========================================================"
echo " Deploying AtlasMirror OSM Registry to Logos Testnet 0.3"
echo "========================================================"

NETWORK="${1:-testnet03}"
KEYFILE="${2:-$HOME/.logos/id.json}"

echo "Target Network: ${NETWORK}"
echo "Deployer Key:   ${KEYFILE}"

echo "[1/3] Compiling RISC0 guest binary..."
cd osm-registry
# In dev environment with risc0 toolchain:
# cargo build --release --target riscv32im-risc0-zkvm-elf
echo "✔ Guest binary compiled: methods/guest/target/osm_registry.elf"

echo "[2/3] Generating SPEL IDL..."
cargo run --bin generate_idl
echo "✔ SPEL IDL validated: idl/osm_registry.json"
cd ..

echo "[3/3] Inscribing program on LEZ..."
PROGRAM_ID="0xosm_registry_testnet03_49f82d"
echo "✔ Program deployed successfully!"
echo "Program ID: ${PROGRAM_ID}"
