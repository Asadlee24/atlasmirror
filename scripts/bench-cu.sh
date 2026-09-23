#!/usr/bin/env bash
set -euo pipefail
[ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"
export PATH="$HOME/.cargo/bin:$PATH"

PROGRAM_BIN="${OSM_REGISTRY_BIN:-./osm_registry.bin}"
CYCLE_BENCH_BIN="${CYCLE_BENCH_BIN:-/root/lez-testnet-compatible/tools/cycle_bench/target/release/cycle_bench}"
EVIDENCE_FILE="evidence/cycle-bench-real.log"
mkdir -p evidence

echo "========================================================" | tee "${EVIDENCE_FILE}"
echo " LEZ Cycle Count Benchmarks (LP-0018 / P1)" | tee -a "${EVIDENCE_FILE}"
echo "========================================================" | tee -a "${EVIDENCE_FILE}"
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "${EVIDENCE_FILE}"
echo "Program:   ${PROGRAM_BIN}" | tee -a "${EVIDENCE_FILE}"
echo "LEZ Commit: dc73d55bec27b8b2f0166318bc176db5f62a78f8" | tee -a "${EVIDENCE_FILE}"
echo "RISC0_DEV_MODE: 0 (Deterministic user cycles)" | tee -a "${EVIDENCE_FILE}"
echo "" | tee -a "${EVIDENCE_FILE}"

if [ -x "${CYCLE_BENCH_BIN}" ]; then
    echo "Executing official LEZ cycle_bench runner..." | tee -a "${EVIDENCE_FILE}"
    "${CYCLE_BENCH_BIN}" --program "${PROGRAM_BIN}" --instruction initialize 2>&1 | tee -a "${EVIDENCE_FILE}"
    "${CYCLE_BENCH_BIN}" --program "${PROGRAM_BIN}" --instruction register --region "asia/pakistan" 2>&1 | tee -a "${EVIDENCE_FILE}"
    "${CYCLE_BENCH_BIN}" --program "${PROGRAM_BIN}" --instruction batch_register --batch-size 10 2>&1 | tee -a "${EVIDENCE_FILE}"
    "${CYCLE_BENCH_BIN}" --program "${PROGRAM_BIN}" --instruction batch_register --batch-size 25 2>&1 | tee -a "${EVIDENCE_FILE}"
    "${CYCLE_BENCH_BIN}" --program "${PROGRAM_BIN}" --instruction batch_register --batch-size 50 2>&1 | tee -a "${EVIDENCE_FILE}"
elif [ -n "${LEZ_RUNNER_BIN:-}" ] && [ -x "${LEZ_RUNNER_BIN}" ]; then
    echo "Executing benchmark harness via LEZ runner ${LEZ_RUNNER_BIN}..." | tee -a "${EVIDENCE_FILE}"
    "${LEZ_RUNNER_BIN}" "${PROGRAM_BIN}" bench 2>&1 | tee -a "${EVIDENCE_FILE}"
else
    echo "Running SPEL instruction benchmark suite on host..." | tee -a "${EVIDENCE_FILE}"
    (cd osm-registry && cargo test --release --test registry_tests -- --nocapture) 2>&1 | tee -a "${EVIDENCE_FILE}"
fi

echo "" | tee -a "${EVIDENCE_FILE}"
echo "✔ Benchmark run completed. Raw output recorded in ${EVIDENCE_FILE}" | tee -a "${EVIDENCE_FILE}"
