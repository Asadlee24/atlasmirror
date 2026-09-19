#!/usr/bin/env bash
# ==============================================================================
# AtlasMirror Real Logos Storage Integration Smoke Test
# Reference: logos-co/logos-storage-module doctests/storage-module-runtime.test.yaml
# Architecture: logoscore daemon -> storage_module -> uploadUrl -> storageUploadDone -> downloadToUrl
# ==============================================================================
set -euo pipefail

mkdir -p evidence

LOG_FILE="evidence/storage-real.log"
: > "${LOG_FILE}"

cleanup() {
    echo "=== Cleaning up storage_module and logoscore daemon ===" | tee -a "${LOG_FILE}"
    if [ -x "./logos/bin/logoscore" ]; then
        ./logos/bin/logoscore call storage_module stop >> "${LOG_FILE}" 2>&1 || true
        ./logos/bin/logoscore call storage_module destroy >> "${LOG_FILE}" 2>&1 || true
        ./logos/bin/logoscore stop >> "${LOG_FILE}" 2>&1 || true
    fi
    if [ -n "${WATCHER_UPLOAD_PID:-}" ]; then
        kill "${WATCHER_UPLOAD_PID}" 2>/dev/null || true
    fi
    if [ -n "${WATCHER_DOWNLOAD_PID:-}" ]; then
        kill "${WATCHER_DOWNLOAD_PID}" 2>/dev/null || true
    fi
    if [ -n "${DAEMON_PID:-}" ]; then
        kill "${DAEMON_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo "=== [1/8] Verifying Nix and build dependencies ===" | tee -a "${LOG_FILE}"
if ! command -v nix >/dev/null 2>&1; then
    echo "[BLOCKED] 'nix' is not installed." | tee -a "${LOG_FILE}"
    echo "Install Nix with flakes enabled in WSL Ubuntu." | tee -a "${LOG_FILE}"
    exit 2
fi

# Step 1: Build logoscore CLI, lgpm, and storage-lgx if not already built
if [ ! -x "./logos/bin/logoscore" ]; then
    echo "Building logoscore CLI via Nix..." | tee -a "${LOG_FILE}"
    nix build 'github:logos-co/logos-logoscore-cli' --out-link ./logos 2>&1 | tee -a "${LOG_FILE}"
fi

if [ ! -x "./lgpm/bin/lgpm" ]; then
    echo "Building lgpm package manager via Nix..." | tee -a "${LOG_FILE}"
    nix build 'github:logos-co/logos-package-manager#cli' -o lgpm 2>&1 | tee -a "${LOG_FILE}"
fi

if [ ! -d "./storage-lgx" ]; then
    echo "Building storage-module lgx via Nix..." | tee -a "${LOG_FILE}"
    nix build 'github:logos-co/logos-storage-module#lgx' -o storage-lgx 2>&1 | tee -a "${LOG_FILE}"
fi

# Step 2: Prepare modules directory and install capability_module & storage_module
mkdir -p modules
chmod -R u+w ./modules 2>/dev/null || true
if [ -d "./logos/modules" ] && [ ! -d "./modules/capability_module" ]; then
    cp -RL ./logos/modules/. ./modules/
    chmod -R u+w ./modules 2>/dev/null || true
fi

if [ ! -d "./modules/storage_module" ]; then
    echo "Installing storage_module into ./modules..." | tee -a "${LOG_FILE}"
    ./lgpm/bin/lgpm --modules-dir ./modules --allow-unsigned install --file storage-lgx/*.lgx 2>&1 | tee -a "${LOG_FILE}"
fi


echo "Verifying installed modules:" | tee -a "${LOG_FILE}"
./lgpm/bin/lgpm --modules-dir ./modules list 2>&1 | tee -a "${LOG_FILE}"
if ! ./lgpm/bin/lgpm --modules-dir ./modules list 2>&1 | grep -q "storage_module"; then
    echo "[FAIL] storage_module is not listed in installed modules" | tee -a "${LOG_FILE}"
    exit 1
fi

# Step 3: Start logoscore daemon
echo "=== [2/8] Starting logoscore daemon in background ===" | tee -a "${LOG_FILE}"
./logos/bin/logoscore -D -m ./modules > evidence/logoscore-storage.log 2>&1 &
DAEMON_PID=$!

echo "Waiting for logoscore daemon to become ready..." | tee -a "${LOG_FILE}"
READY=0
for i in {1..30}; do
    if ./logos/bin/logoscore status >> "${LOG_FILE}" 2>&1; then
        READY=1
        break
    fi
    sleep 1
done

if [ "$READY" -ne 1 ]; then
    echo "[FAIL] logoscore daemon failed to start" | tee -a "${LOG_FILE}"
    cat evidence/logoscore-storage.log | tee -a "${LOG_FILE}"
    exit 1
fi
echo "logoscore daemon is RUNNING (PID: ${DAEMON_PID})" | tee -a "${LOG_FILE}"

# Step 4: Load storage_module
echo "=== [3/8] Loading storage_module ===" | tee -a "${LOG_FILE}"
./logos/bin/logoscore load-module storage_module 2>&1 | tee -a "${LOG_FILE}"

echo "Verifying module-info for storage_module:" | tee -a "${LOG_FILE}"
./logos/bin/logoscore module-info storage_module 2>&1 | tee -a "${LOG_FILE}"

# Step 5: Configure and initialize storage_module
echo "=== [4/8] Initializing storage_module with absolute data-dir ===" | tee -a "${LOG_FILE}"
STORAGE_DATA_DIR="$(pwd)/storage-data"
mkdir -p "${STORAGE_DATA_DIR}"

cat > config.json <<EOF
{
  "data-dir": "${STORAGE_DATA_DIR}",
  "log-level": "DEBUG",
  "log-file": "${STORAGE_DATA_DIR}/storage.log",
  "nat": "extip:127.0.0.1"
}
EOF

INIT_RESP=$(./logos/bin/logoscore call storage_module init @config.json --json 2>&1 | tee -a "${LOG_FILE}")
echo "Init Response: ${INIT_RESP}" | tee -a "${LOG_FILE}"

echo "=== [5/8] Starting storage node ===" | tee -a "${LOG_FILE}"
START_RESP=$(./logos/bin/logoscore call storage_module start --json 2>&1 | tee -a "${LOG_FILE}")
echo "Start Response: ${START_RESP}" | tee -a "${LOG_FILE}"
sleep 3

# Step 6: Stream upload via uploadUrl and capture CID asynchronously
echo "=== [6/8] Uploading real payload via uploadUrl ===" | tee -a "${LOG_FILE}"
TMP_DIR=$(mktemp -d /tmp/atlasmirror-storage-test.XXXXXX)
TEST_FILE="${TMP_DIR}/sample_1mb.bin"
RETRIEVED_FILE="${TMP_DIR}/retrieved_1mb.bin"

# Generate 1MB test payload
dd if=/dev/urandom of="${TEST_FILE}" bs=1048576 count=1 status=none
ORIGINAL_SHA256=$(sha256sum "${TEST_FILE}" | awk '{print $1}')
FILE_BYTES=$(wc -c < "${TEST_FILE}")
echo "Generated ${FILE_BYTES} bytes, SHA256: ${ORIGINAL_SHA256}" | tee -a "${LOG_FILE}"

# Start upload event watcher before calling uploadUrl
: > evidence/upload-event.json
./logos/bin/logoscore watch storage_module --event storageUploadDone --json > evidence/upload-event.json 2>&1 &
WATCHER_UPLOAD_PID=$!
sleep 1

UPLOAD_CALL_RESP=$(./logos/bin/logoscore call storage_module uploadUrl "$(realpath "${TEST_FILE}")" 262144 --json 2>&1 | tee -a "${LOG_FILE}")
echo "uploadUrl Call Response: ${UPLOAD_CALL_RESP}" | tee -a "${LOG_FILE}"

# Wait for storageUploadDone event
echo "Waiting for storageUploadDone event..." | tee -a "${LOG_FILE}"
REAL_CID=""
for i in {1..30}; do
    if [ -s evidence/upload-event.json ]; then
        cat evidence/upload-event.json | tee -a "${LOG_FILE}"
        REAL_CID=$(grep -o '"cid": *"[^"]*"' evidence/upload-event.json | head -1 | cut -d'"' -f4 || echo "")
        if [ -n "${REAL_CID}" ]; then
            break
        fi
    fi
    sleep 1
done

# Fallback: query manifests if watcher was slow
if [ -z "${REAL_CID}" ]; then
    echo "Checking manifests for uploaded CID..." | tee -a "${LOG_FILE}"
    MANIFESTS_JSON=$(./logos/bin/logoscore call storage_module manifests --json 2>&1 | tee -a "${LOG_FILE}")
    REAL_CID=$(echo "${MANIFESTS_JSON}" | grep -o '"cid": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
fi

if [ -z "${REAL_CID}" ]; then
    echo "[FAIL] Could not capture real CID from storageUploadDone or manifests" | tee -a "${LOG_FILE}"
    exit 1
fi
echo "REAL STORAGE CID: ${REAL_CID}" | tee -a "${LOG_FILE}"

# Step 7: Download by CID using downloadToUrl (local=true)
echo "=== [7/8] Downloading by CID via downloadToUrl (local=true) ===" | tee -a "${LOG_FILE}"
: > evidence/download-event.json
./logos/bin/logoscore watch storage_module --event storageDownloadDone --json > evidence/download-event.json 2>&1 &
WATCHER_DOWNLOAD_PID=$!
sleep 1

DOWNLOAD_CALL_RESP=$(./logos/bin/logoscore call storage_module downloadToUrl "${REAL_CID}" "$(realpath -m "${RETRIEVED_FILE}")" true 262144 --json 2>&1 | tee -a "${LOG_FILE}")
echo "downloadToUrl Call Response: ${DOWNLOAD_CALL_RESP}" | tee -a "${LOG_FILE}"

echo "Waiting for storageDownloadDone event..." | tee -a "${LOG_FILE}"
DOWNLOAD_DONE=0
for i in {1..30}; do
    if [ -s evidence/download-event.json ] && grep -q "storageDownloadDone" evidence/download-event.json; then
        DOWNLOAD_DONE=1
        cat evidence/download-event.json | tee -a "${LOG_FILE}"
        break
    fi
    if [ -f "${RETRIEVED_FILE}" ] && [ "$(wc -c < "${RETRIEVED_FILE}")" -ge "${FILE_BYTES}" ]; then
        DOWNLOAD_DONE=1
        break
    fi
    sleep 1
done

if [ "$DOWNLOAD_DONE" -ne 1 ]; then
    echo "[FAIL] storageDownloadDone did not complete within timeout" | tee -a "${LOG_FILE}"
    exit 1
fi

# Step 8: Verify exact byte-for-byte SHA256 equality
echo "=== [8/8] Verifying byte-for-byte SHA256 equality ===" | tee -a "${LOG_FILE}"
RETRIEVED_SHA256=$(sha256sum "${RETRIEVED_FILE}" | awk '{print $1}')
RETRIEVED_BYTES=$(wc -c < "${RETRIEVED_FILE}")

echo "Original  Bytes:  ${FILE_BYTES}, SHA256: ${ORIGINAL_SHA256}" | tee -a "${LOG_FILE}"
echo "Retrieved Bytes:  ${RETRIEVED_BYTES}, SHA256: ${RETRIEVED_SHA256}" | tee -a "${LOG_FILE}"

if [ "${FILE_BYTES}" -ne "${RETRIEVED_BYTES}" ]; then
    echo "[FAIL] Byte count mismatch: ${FILE_BYTES} != ${RETRIEVED_BYTES}" | tee -a "${LOG_FILE}"
    exit 1
fi

if [ "${ORIGINAL_SHA256}" != "${RETRIEVED_SHA256}" ]; then
    echo "[FAIL] SHA256 mismatch!" | tee -a "${LOG_FILE}"
    exit 1
fi

echo "========================================================" | tee -a "${LOG_FILE}"
echo "[PASS] REAL LOGOS STORAGE ROUNDTRIP VERIFIED!" | tee -a "${LOG_FILE}"
echo "========================================================" | tee -a "${LOG_FILE}"
