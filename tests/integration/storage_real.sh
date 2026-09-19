#!/usr/bin/env bash
# ==============================================================================
# AtlasMirror Real Logos Storage Integration Smoke Test
# Reference: logos-co/logos-storage-module doctests/storage-module-runtime.test.yaml
# Architecture: logoscore daemon -> storage_module -> uploadUrl -> storageUploadDone -> downloadToUrl
# ==============================================================================
set -euo pipefail

mkdir -p evidence

echo "=== [1/6] Checking for logoscore and storage_module ==="
if ! command -v logoscore >/dev/null 2>&1; then
    echo "[BLOCKED] 'logoscore' executable not found in PATH." | tee evidence/storage-real.log
    echo "To run this test:" | tee -a evidence/storage-real.log
    echo "  1. Install/build logoscore" | tee -a evidence/storage-real.log
    echo "  2. Build and package storage_module from https://github.com/logos-co/logos-storage-module" | tee -a evidence/storage-real.log
    echo "  3. Ensure 'logoscore' is in PATH" | tee -a evidence/storage-real.log
    exit 2
fi

LOGOSCORE_VERSION=$(logoscore --version 2>&1 || echo "unknown")
echo "logoscore version: ${LOGOSCORE_VERSION}" | tee evidence/storage-real.log

MODULES_DIR="${LOGOS_MODULES_DIR:-./modules}"
if [ ! -d "${MODULES_DIR}/storage_module" ] && [ ! -f "${MODULES_DIR}/storage_module.lgx" ]; then
    echo "[BLOCKED] 'storage_module' not found in ${MODULES_DIR}." | tee -a evidence/storage-real.log
    echo "Please build storage_module and place it in ${MODULES_DIR}." | tee -a evidence/storage-real.log
    exit 2
fi

TMP_DIR=$(mktemp -d /tmp/atlasmirror-storage-test.XXXXXX)
trap 'rm -rf "${TMP_DIR}"' EXIT

TEST_FILE="${TMP_DIR}/test_payload.bin"
RETRIEVED_FILE="${TMP_DIR}/retrieved_payload.bin"

# Generate real test binary payload (1MB)
dd if=/dev/urandom of="${TEST_FILE}" bs=1048576 count=1 status=none
ORIGINAL_SHA256=$(sha256sum "${TEST_FILE}" | awk '{print $1}')
FILE_BYTES=$(wc -c < "${TEST_FILE}")

echo "=== [2/6] Initializing storage_module in logoscore ===" | tee -a evidence/storage-real.log
logoscore call storage_module init '{"data_dir":"'"${TMP_DIR}"'/data"}' --json | tee -a evidence/storage-real.log

echo "=== [3/6] Starting storage node ===" | tee -a evidence/storage-real.log
logoscore call storage_module start --json | tee -a evidence/storage-real.log

echo "=== [4/6] Streaming uploadUrl (${FILE_BYTES} bytes, 256KB chunks) ===" | tee -a evidence/storage-real.log
UPLOAD_RESP=$(logoscore call storage_module uploadUrl "${TEST_FILE}" 262144 --json | tee -a evidence/storage-real.log)

# Extract CID and session from storageUploadDone event
REAL_CID=$(echo "${UPLOAD_RESP}" | grep -o '"cid": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
if [ -z "${REAL_CID}" ]; then
    echo "[FAIL] storageUploadDone did not return a valid CID" | tee -a evidence/storage-real.log
    exit 1
fi
echo "Real CID returned by storage_module: ${REAL_CID}" | tee -a evidence/storage-real.log

echo "=== [5/6] Downloading by CID via downloadToUrl ===" | tee -a evidence/storage-real.log
logoscore call storage_module downloadToUrl "${REAL_CID}" "${RETRIEVED_FILE}" false 262144 --json | tee -a evidence/storage-real.log

echo "=== [6/6] Verifying byte-for-byte SHA256 equality ===" | tee -a evidence/storage-real.log
RETRIEVED_SHA256=$(sha256sum "${RETRIEVED_FILE}" | awk '{print $1}')

echo "Original  SHA256: ${ORIGINAL_SHA256}" | tee -a evidence/storage-real.log
echo "Retrieved SHA256: ${RETRIEVED_SHA256}" | tee -a evidence/storage-real.log

if [ "${ORIGINAL_SHA256}" != "${RETRIEVED_SHA256}" ]; then
    echo "[FAIL] SHA256 mismatch between original and retrieved payload!" | tee -a evidence/storage-real.log
    exit 1
fi

echo "[PASS] Exact SHA256 equality verified across real Logos Storage roundtrip!" | tee -a evidence/storage-real.log
