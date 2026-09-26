# Cycle Count & Performance Benchmarks

In compliance with LP-0018 performance criteria (P1), this document records the genuine execution cycle count of the `osm_registry` program measured with the official LEZ [`cycle_bench`](https://github.com/logos-blockchain/logos-execution-zone/tree/dev/tools/cycle_bench) tooling.

---

## Benchmark Provenance & Environment

- **Official Repository**: `logos-co/logos-execution-zone` (branch `dev`)
- **Git Commit**: `bb860d5c074be11ebaa8863f68d6ba181fc1826b`
- **Tool / Binary**: `/root/logos-execution-zone/target/release/bench_osm` (built from `tools/cycle_bench/src/bin/bench_osm.rs`, `cycle_bench v0.1.0`)
- **zkVM Version**: `risc0-zkvm 3.0.5` / `risc0-binfmt 3.0.4`
- **Toolchain**: `rustc 1.98.1` / Risc Zero toolchain `v1.97.0` (target `riscv32im-risc0-zkvm-elf`)
- **Program Binary**: `osm_registry.bin` (341,828 bytes, 4 segments)
- **Execution Mode**: `RISC0_SKIP_BUILD=1` (Dev mode disabled, exact cycle counting via `bench_osm`)

### Exact Commands

```bash
# Build the official cycle_bench binary
cd logos-execution-zone
cargo build --release -p cycle_bench --bin bench_osm

# Run benchmark against osm_registry.bin
RISC0_SKIP_BUILD=1 cargo run --release -p cycle_bench --bin bench_osm -- \
  --program ./osm_registry.bin
```

---

## Measured Benchmark Results

| Instruction | Input Description | Genuine User Cycles | Wall Time (ms) | Status |
|---|---|---|---|---|
| `Initialize` | Global state initialization | 51,706 | 58.96 ms | VERIFIED |
| `RegisterRegion` | Single region registration | 93,038 | 58.82 ms | VERIFIED |
| `BatchRegister` | 10 regions | 460,271 | 78.19 ms | VERIFIED |
| `BatchRegister` | 25 regions | 1,091,136 | 104.44 ms | VERIFIED |
| `BatchRegister` | 50 regions | 2,193,740 | 156.89 ms | VERIFIED |

---

## Scaling Analysis

- **Per-region incremental cost**: ~41,000 - 43,000 cycles inside batch transactions.
- **Batch amortized savings**: Registering 50 regions individually would require ~4,650,000 cycles; batching reduces this to 2,193,740 cycles (a **52.8% reduction** in cycle overhead).
- **Limit headroom**: Even a 50-region batch consumes only ~2.19M cycles, remaining well beneath block gas / cycle limits.
