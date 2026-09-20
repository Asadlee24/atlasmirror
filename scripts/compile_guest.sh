#!/usr/bin/env bash
set -e
export PATH="/root/.risc0/toolchains/v1.97.0-rust-x86_64-unknown-linux-gnu/bin:/root/.risc0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export RUSTFLAGS='--cfg getrandom_backend="custom"'

cd /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/methods/guest
cargo build --target riscv32im-risc0-zkvm-elf --release
