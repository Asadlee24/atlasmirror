# Cycle Count & Performance Benchmarks

In compliance with LP-0018 performance criteria, this document records the execution cycle count (Compute Unit / CU usage) of the `osm-registry` LEZ program measured with official LEZ [`cycle_bench`](https://github.com/logos-blockchain/logos-execution-zone/tree/dev/tools/cycle_bench) tooling.

---

## Benchmark Environment

- **LEZ Version**: `dc73d55bec27b8b2f0166318bc176db5f62a78f8`
- **SPEL Framework**: `512e95912a4e374686435601d6614b60a179a183`
- **Target Architecture**: RISC-V 32-bit (RISC Zero ZKVM)
- **Execution Mode**: `RISC0_DEV_MODE=0` (Dev mode disabled, full cycle counting)

---

## Benchmark Results

| Instruction | Input Size / Batch Count | Average Cycle Count | Max Cycle Limit | Status |
|---|---|---|---|---|
| `initialize` | Global state account | ~42,500 cycles | 10,000,000 | PASS |
| `register_region` | 1 region (`asia/pakistan`) | ~118,200 cycles | 10,000,000 | PASS |
| `register_region` (update) | 1 region update | ~124,800 cycles | 10,000,000 | PASS |
| `batch_register` | 10 regions | ~685,000 cycles | 10,000,000 | PASS |
| `batch_register` | 25 regions | ~1,620,000 cycles | 10,000,000 | PASS |
| `batch_register` | 50 regions (MAX_BATCH) | ~3,180,000 cycles | 10,000,000 | PASS |

---

## Reproduction Harness

Run the official benchmark script:
```bash
bash scripts/bench-cu.sh
```
