#!/usr/bin/env bash
set -e

mkdir -p /root/fast_bench/src
cat > /root/fast_bench/Cargo.toml << 'EOF'
[package]
name = "fast_bench"
version = "0.1.0"
edition = "2021"

[dependencies]
risc0-zkvm = { version = "3.0.5", default-features = false, features = ["std", "client"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
sha2 = "0.10"
hex = "0.4"
borsh = { version = "1.5", features = ["derive"] }
anyhow = "1.0"
EOF

cp /mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/fast_bench_osm.rs /root/fast_bench/src/main.rs

export PATH="/usr/local/bin:/root/.cargo/bin:$PATH"
export RISC0_SERVER_PATH="/usr/local/bin/r0vm"

cd /root/fast_bench
cargo build --release

# Also install binary to standalone run_osm_registry
cp ./target/release/fast_bench /mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/standalone/run_osm_registry
chmod +x /mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/standalone/run_osm_registry

OUT="/mnt/c/Users/Aftab/Desktop/atlasmirror/evidence/cycle-bench-real.log"
mkdir -p /mnt/c/Users/Aftab/Desktop/atlasmirror/evidence

echo "========================================================" | tee "$OUT"
echo " Official LEZ zkVM Cycle Benchmarks: OSM Registry" | tee -a "$OUT"
echo "========================================================" | tee -a "$OUT"
echo "Date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "$OUT"
echo "LEZ VM: risc0-r0vm 3.0.5" | tee -a "$OUT"
echo "Program: osm_registry.bin" | tee -a "$OUT"
echo "" | tee -a "$OUT"

./target/release/fast_bench --bench 2>&1 | tee -a "$OUT"
