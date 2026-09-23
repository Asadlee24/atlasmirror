#!/usr/bin/env bash
set -euo pipefail

export PATH="/root/.cargo/bin:/mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/standalone:$PATH"
export LOGOSCORE_BIN="/mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/standalone/logoscore"
export LEZ_RUNNER_BIN="/mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/standalone/run_osm_registry"
export OSM_REGISTRY_BIN="/mnt/c/Users/Aftab/Desktop/atlasmirror/osm_registry.bin"
export LEZ_ACCOUNT_ID="55Me6rDpyUu9vhuMhnM26ikUL4XbgKDUjrWEpdpzyv6r"

EVIDENCE_FILE="evidence/batch-register-real.log"
mkdir -p evidence

echo "========================================================" | tee "${EVIDENCE_FILE}"
echo " AtlasMirror Genuine Batch Registration (LP-0018 / P1)" | tee -a "${EVIDENCE_FILE}"
echo "========================================================" | tee -a "${EVIDENCE_FILE}"
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "${EVIDENCE_FILE}"
echo "Runner:    ${LEZ_RUNNER_BIN}" | tee -a "${EVIDENCE_FILE}"
echo "Account:   ${LEZ_ACCOUNT_ID}" | tee -a "${EVIDENCE_FILE}"
echo "Regions:   asia/pakistan (level=country, parent=null)" | tee -a "${EVIDENCE_FILE}"
echo "           china/henan   (level=subregion, parent=china)" | tee -a "${EVIDENCE_FILE}"
echo "" | tee -a "${EVIDENCE_FILE}"

echo "=== [Step 1] Executing Batch Host via AtlasMirror CLI ===" | tee -a "${EVIDENCE_FILE}"
cargo run --release --manifest-path atlasmirror-cli/Cargo.toml -- host --batch asia/pakistan china/henan 2>&1 | tee -a "${EVIDENCE_FILE}"

echo "" | tee -a "${EVIDENCE_FILE}"
echo "=== [Step 2] Querying Back On-Chain Record 1: asia/pakistan ===" | tee -a "${EVIDENCE_FILE}"
cargo run --release --manifest-path atlasmirror-cli/Cargo.toml -- lookup region asia/pakistan 2>&1 | tee -a "${EVIDENCE_FILE}"

echo "" | tee -a "${EVIDENCE_FILE}"
echo "=== [Step 3] Querying Back On-Chain Record 2: china/henan ===" | tee -a "${EVIDENCE_FILE}"
cargo run --release --manifest-path atlasmirror-cli/Cargo.toml -- lookup region china/henan 2>&1 | tee -a "${EVIDENCE_FILE}"

echo "" | tee -a "${EVIDENCE_FILE}"
echo "=== [Step 4] Direct LEZ Runner Account Query ===" | tee -a "${EVIDENCE_FILE}"
"${LEZ_RUNNER_BIN}" "${OSM_REGISTRY_BIN}" "${LEZ_ACCOUNT_ID}" query 2>&1 | tee -a "${EVIDENCE_FILE}"

echo "" | tee -a "${EVIDENCE_FILE}"
echo "✔ Batch registration and query verification completed successfully." | tee -a "${EVIDENCE_FILE}"
