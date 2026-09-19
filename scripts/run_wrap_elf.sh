#!/usr/bin/env bash
set -e
export PATH="/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:$PATH"

cd /tmp/lez
echo "=== Building wrap_elf ==="
cargo build -p program_loader_core --bin wrap_elf

echo "=== Wrapping osm_registry ELF into ProgramBinary ==="
/tmp/lez/target/debug/wrap_elf \
    /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry \
    /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry.bin

ls -lh /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry.bin
