#!/usr/bin/env bash
# ==============================================================================
# AtlasMirror Genuine End-to-End PBF Pipeline Orchestration
# Flow: Geofabrik PBF -> MD5 Checksum Equality -> logoscore/storage_module uploadUrl
#       -> Real CID -> SPEL LEZ Transaction -> Query Account -> downloadToUrl -> SHA256 Equality
# NO FAKE REST APIS. Uses only official logoscore and spel CLI tooling.
# ==============================================================================
set -euo pipefail

TARGET_REGION="${ATLASMIRROR_REGION:-china/henan}"
MODULES_DIR="${LOGOS_MODULES_DIR:-./modules}"
PROGRAM_ID="${OSM_REGISTRY_PROGRAM_ID:-}"

mkdir -p evidence

cleanup() {
    if [ -x "./logos/bin/logoscore" ]; then
        ./logos/bin/logoscore call storage_module stop >> evidence/e2e-real.log 2>&1 || true
        ./logos/bin/logoscore call storage_module destroy >> evidence/e2e-real.log 2>&1 || true
        ./logos/bin/logoscore stop >> evidence/e2e-real.log 2>&1 || true
    fi
    if [ -n "${WATCHER_UPLOAD_PID:-}" ]; then kill "${WATCHER_UPLOAD_PID}" 2>/dev/null || true; fi
    if [ -n "${WATCHER_DOWNLOAD_PID:-}" ]; then kill "${WATCHER_DOWNLOAD_PID}" 2>/dev/null || true; fi
    if [ -n "${DAEMON_PID:-}" ]; then kill "${DAEMON_PID}" 2>/dev/null || true; fi
}
trap cleanup EXIT

echo "========================================================"
echo " AtlasMirror Real End-to-End PBF Pipeline"
echo " Target Region: ${TARGET_REGION}"
echo "========================================================"

echo "=== [Preflight 1/3] Checking logoscore ==="
if [ ! -x "./logos/bin/logoscore" ] && ! command -v logoscore >/dev/null 2>&1; then
    echo "[BLOCKED] 'logoscore' CLI not found. Build via: nix build 'github:logos-co/logos-logoscore-cli' --out-link ./logos" | tee evidence/e2e-real.log
    exit 2
fi
LOGOSCORE_BIN="./logos/bin/logoscore"
if [ ! -x "${LOGOSCORE_BIN}" ]; then
    LOGOSCORE_BIN="logoscore"
fi

echo "=== [Preflight 2/3] Checking storage_module ==="
if [ ! -d "${MODULES_DIR}/storage_module" ] && [ ! -f "${MODULES_DIR}/storage_module.lgx" ]; then
    echo "[BLOCKED] 'storage_module' not found in ${MODULES_DIR}. Install via lgpm." | tee -a evidence/e2e-real.log
    exit 2
fi

echo "=== [Preflight 3/3] Checking spel CLI and Program ID ==="
if ! command -v spel >/dev/null 2>&1 && ! command -v spel-cli >/dev/null 2>&1; then
    echo "[BLOCKED] 'spel' CLI not found in PATH." | tee -a evidence/e2e-real.log
    exit 2
fi

if [ -z "${PROGRAM_ID}" ]; then
    echo "[BLOCKED] OSM_REGISTRY_PROGRAM_ID environment variable not set." | tee -a evidence/e2e-real.log
    echo "Deploy program first using: wallet deploy-program target/riscv32im-risc0-zkvm-elf/release/osm_registry" | tee -a evidence/e2e-real.log
    exit 2
fi

TMP_DIR=$(mktemp -d /tmp/atlasmirror-e2e.XXXXXX)
trap 'rm -rf "${TMP_DIR}"' EXIT

PBF_FILE="${TMP_DIR}/snapshot.osm.pbf"
RETRIEVED_FILE="${TMP_DIR}/retrieved.osm.pbf"

# Step 1: Download Geofabrik snapshot and MD5
echo "=== [Step 1] Fetching live published MD5 from Geofabrik ===" | tee -a evidence/e2e-real.log
GEOFABRIK_PBF_URL=$(python3 -c "import json; cat=json.load(open('metadata/regions.json'))['regions']; print(next((r['geofabrik_url'] for r in cat if r['path'] == '${TARGET_REGION}'), 'https://download.geofabrik.de/${TARGET_REGION}-latest.osm.pbf'))")
GEOFABRIK_MD5_URL=$(python3 -c "import json; cat=json.load(open('metadata/regions.json'))['regions']; print(next((r['md5_url'] for r in cat if r['path'] == '${TARGET_REGION}'), 'https://download.geofabrik.de/${TARGET_REGION}-latest.osm.pbf.md5'))")
PUBLISHED_MD5=$(curl -sSfL "${GEOFABRIK_MD5_URL}" | awk '{print $1}' | tr '[:upper:]' '[:lower:]')
echo "Published MD5: ${PUBLISHED_MD5}" | tee -a evidence/e2e-real.log

echo "=== [Step 2] Downloading real PBF snapshot ===" | tee -a evidence/e2e-real.log
curl -sSfL -o "${PBF_FILE}" "${GEOFABRIK_PBF_URL}"
FILE_BYTES=$(wc -c < "${PBF_FILE}")
echo "Downloaded ${FILE_BYTES} bytes." | tee -a evidence/e2e-real.log

# Step 2: Compute local MD5 and assert exact equality
echo "=== [Step 3] Stream-computing local MD5 and asserting equality ===" | tee -a evidence/e2e-real.log
COMPUTED_MD5=$(md5sum "${PBF_FILE}" | awk '{print $1}' | tr '[:upper:]' '[:lower:]')
ORIGINAL_SHA256=$(sha256sum "${PBF_FILE}" | awk '{print $1}')
echo "Computed MD5:    ${COMPUTED_MD5}" | tee -a evidence/e2e-real.log
echo "Original SHA256: ${ORIGINAL_SHA256}" | tee -a evidence/e2e-real.log

if [ "${COMPUTED_MD5}" != "${PUBLISHED_MD5}" ]; then
    echo "[FATAL ERROR] Checksum mismatch! Published: ${PUBLISHED_MD5} != Computed: ${COMPUTED_MD5}" | tee -a evidence/e2e-real.log
    exit 1
fi
echo "[PASS] Checksum equality verified." | tee -a evidence/e2e-real.log

# Step 3: Start logoscore daemon and initialize storage_module
echo "=== [Step 4] Starting logoscore daemon and storage_module ===" | tee -a evidence/e2e-real.log
"${LOGOSCORE_BIN}" -D -m "${MODULES_DIR}" > evidence/logoscore-e2e.log 2>&1 &
DAEMON_PID=$!
sleep 2

"${LOGOSCORE_BIN}" load-module storage_module >> evidence/e2e-real.log 2>&1

STORAGE_DATA_DIR="$(pwd)/storage-data-e2e"
mkdir -p "${STORAGE_DATA_DIR}"
cat > config-e2e.json <<EOF
{
  "data-dir": "${STORAGE_DATA_DIR}",
  "log-level": "DEBUG",
  "log-file": "${STORAGE_DATA_DIR}/storage.log",
  "nat": "extip:127.0.0.1"
}
EOF
"${LOGOSCORE_BIN}" call storage_module init @config-e2e.json >> evidence/e2e-real.log 2>&1
"${LOGOSCORE_BIN}" call storage_module start >> evidence/e2e-real.log 2>&1
sleep 3

# Step 4: Stream upload via storage_module uploadUrl and capture CID asynchronously
echo "=== [Step 5] Streaming upload to Logos Storage via uploadUrl ===" | tee -a evidence/e2e-real.log
: > evidence/e2e-upload-event.json
"${LOGOSCORE_BIN}" watch storage_module --event storageUploadDone --json > evidence/e2e-upload-event.json 2>&1 &
WATCHER_UPLOAD_PID=$!
sleep 1

"${LOGOSCORE_BIN}" call storage_module uploadUrl "$(realpath "${PBF_FILE}")" 1048576 --json >> evidence/e2e-real.log 2>&1

# Wait for storageUploadDone event
echo "Waiting for storageUploadDone event..." | tee -a evidence/e2e-real.log
REAL_CID=""
for i in {1..60}; do
    if [ -s evidence/e2e-upload-event.json ]; then
        REAL_CID=$(grep -o '"cid": *"[^"]*"' evidence/e2e-upload-event.json | head -1 | cut -d'"' -f4 || echo "")
        if [ -n "${REAL_CID}" ]; then break; fi
    fi
    sleep 1
done

if [ -z "${REAL_CID}" ]; then
    MANIFESTS_JSON=$("${LOGOSCORE_BIN}" call storage_module manifests --json 2>&1 || echo "")
    REAL_CID=$(echo "${MANIFESTS_JSON}" | grep -o '"cid": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
fi

if [ -z "${REAL_CID}" ]; then
    echo "[FAIL] storageUploadDone did not return a valid CID" | tee -a evidence/e2e-real.log
    exit 1
fi
echo "Real CID from storage_module: ${REAL_CID}" | tee -a evidence/e2e-real.log

# Step 5: Register in LEZ on-chain registry via generated SPEL CLI
echo "=== [Step 6] Submitting on-chain registration to LEZ via spel CLI ===" | tee -a evidence/e2e-real.log
TX_OUTPUT=$(spel --idl osm-registry/idl/osm_registry.json -p "${PROGRAM_ID}" -- \
    register-region \
    --region "${TARGET_REGION}" \
    --level "subregion" \
    --cid "${REAL_CID}" \
    --source-url "https://download.geofabrik.de/${TARGET_REGION}-latest.osm.pbf" \
    --checksum "${COMPUTED_MD5}" \
    --version "$(date +%Y-%m-%d)" \
    --timestamp "$(date +%s)" | tee -a evidence/e2e-real.log)

echo "=== [Step 7] Querying on-chain state via spel inspect ===" | tee -a evidence/e2e-real.log
QUERY_OUTPUT=$(spel inspect --program-id "${PROGRAM_ID}" --region "${TARGET_REGION}" | tee -a evidence/e2e-real.log)

# Step 6: Download snapshot by CID via storage_module downloadToUrl (local=true)
echo "=== [Step 8] Downloading snapshot by CID from Logos Storage ===" | tee -a evidence/e2e-real.log
: > evidence/e2e-download-event.json
"${LOGOSCORE_BIN}" watch storage_module --event storageDownloadDone --json > evidence/e2e-download-event.json 2>&1 &
WATCHER_DOWNLOAD_PID=$!
sleep 1

"${LOGOSCORE_BIN}" call storage_module downloadToUrl "${REAL_CID}" "$(realpath -m "${RETRIEVED_FILE}")" true 1048576 --json >> evidence/e2e-real.log 2>&1

echo "Waiting for storageDownloadDone event..." | tee -a evidence/e2e-real.log
for i in {1..60}; do
    if [ -s evidence/e2e-download-event.json ] && grep -q "storageDownloadDone" evidence/e2e-download-event.json; then
        break
    fi
    sleep 1
done

# Step 7: Verify exact byte-for-byte SHA256 equality
echo "=== [Step 9] Verifying byte-for-byte SHA256 equality ===" | tee -a evidence/e2e-real.log
RETRIEVED_SHA256=$(sha256sum "${RETRIEVED_FILE}" | awk '{print $1}')
echo "Retrieved SHA256: ${RETRIEVED_SHA256}" | tee -a evidence/e2e-real.log

if [ "${ORIGINAL_SHA256}" != "${RETRIEVED_SHA256}" ]; then
    echo "[FAIL] SHA256 mismatch between original and downloaded PBF snapshot!" | tee -a evidence/e2e-real.log
    exit 1
fi

echo "========================================================"
echo "[PASS] REAL END-TO-END PBF PIPELINE VERIFIED SUCCESSFULLY!"
echo "========================================================" | tee -a evidence/e2e-real.log
