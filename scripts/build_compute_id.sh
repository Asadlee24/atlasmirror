#!/bin/bash
set -e
mkdir -p /root/lez-v021/build_utils/src/bin
cp /mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/compute_id.rs /root/lez-v021/build_utils/src/bin/compute_id.rs
export PATH='/root/.risc0/toolchains/v1.97.0-rust-x86_64-unknown-linux-gnu/bin:/root/.risc0/bin:/usr/local/bin:/usr/bin:/bin:$PATH'
cd /root/lez-v021 && cargo build --release --bin compute_id -p build_utils
/root/lez-v021/target/release/compute_id /root/lez-v021/artifacts/lez/programs/authenticated_transfer.bin
