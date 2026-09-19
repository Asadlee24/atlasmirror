#!/usr/bin/env bash
set -e
export PATH="/root/.risc0/toolchains/v1.97.0-rust-x86_64-unknown-linux-gnu/bin:/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:$PATH"
export RUSTFLAGS='--cfg getrandom_backend="unsupported"'

which rustc
which cc
which cargo

echo "=== Building osm-registry-guest directly with risc0 toolchain and RUSTFLAGS ==="
cd /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry
cargo build --manifest-path methods/guest/Cargo.toml --target riscv32im-risc0-zkvm-elf --release 2>&1 | tee /mnt/c/Users/Aftab/Desktop/atlasmirror/evidence/registry-build.log

echo "=== Searching for built guest binary ==="
find target -name "osm_registry*" -path "*/riscv32im*" | tee -a /mnt/c/Users/Aftab/Desktop/atlasmirror/evidence/registry-build.log
