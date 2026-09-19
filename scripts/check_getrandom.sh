#!/usr/bin/env bash
export PATH="/root/.risc0/toolchains/v1.97.0-rust-x86_64-unknown-linux-gnu/bin:$PATH"
cd /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry
cargo tree --target riscv32im-risc0-zkvm-elf -i getrandom@0.3.4
