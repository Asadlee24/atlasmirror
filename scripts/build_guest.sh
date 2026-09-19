#!/usr/bin/env bash
set -e
export PATH="/root/.risc0/bin:/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:/usr/local/bin:$PATH"

mkdir -p /mnt/c/Users/Aftab/Desktop/atlasmirror/evidence
echo "=== Building osm-registry guest binary ==="
cd /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry
cargo risczero build --manifest-path methods/guest/Cargo.toml 2>&1 | tee /mnt/c/Users/Aftab/Desktop/atlasmirror/evidence/registry-build.log

echo "=== Searching for built guest binary ==="
find . -name "*.bin" -o -name "osm_registry" -path "*/riscv32im*" | tee -a /mnt/c/Users/Aftab/Desktop/atlasmirror/evidence/registry-build.log
