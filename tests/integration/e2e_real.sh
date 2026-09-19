#!/usr/bin/env bash
# ==============================================================================
# AtlasMirror Genuine End-to-End Pipeline Orchestration
# Flow: Geofabrik PBF -> MD5 Checksum Equality -> logoscore/storage_module uploadUrl
#       -> Real CID -> SPEL LEZ Transaction -> Query Account -> downloadToUrl -> SHA256 Equality
# NO FAKE REST APIS. Uses only official logoscore and spel CLI tooling.
# ==============================================================================
set -euo pipefail

TARGET_REGION="${ATLASMIRROR_REGION:-china/henan}"
MODULES_DIR="${LOGOS_MODULES_DIR:-./modules}"
PROGRAM_ID="${OSM_REGISTRY_PROGRAM_ID:-}"

mkdir -p evidence

echo "========================================================"
echo " AtlasMirror Real End-to-End PBF Pipeline"
echo " Target Region: ${TARGET_REGION}"
echo "========================================================"

echo "=== [Preflight 1/3] Checking logoscore ==="
if ! command -v logoscore >/dev/null 2>&1; then
    echo "[BLOCKED] 'logoscore' CLI not found in PATH." | tee evidence/e2e-real.log
    echo "Requires running logoscore daemon with storage_module." | tee -a evidence/e2e-real.log
    exit 2
fi

echo "=== [Preflight 2/3] Checking storage_module ==="
if [ ! -d "${MODULES_DIR}/storage_module" ] && [ ! -f "${MODULES_DIR}/storage_module.lgx" ]; then
    echo "[BLOCKED] 'storage_module' not found in ${MODULES_DIR}." | tee -a evidence/e2e-real.log
    exit 2
fi

echo "=== [Preflight 3/3] Checking spel CLI ==="
if ! command -v spel >/dev/null 2>&1 && ! command -v spel-cli >/dev/null 2>&1; then
    echo "[BLOCKED] 'spel' CLI not found in PATH." | tee -a evidence/e2e-real.log
    echo "Requires SPEL framework and active LEZ standalone sequencer." | tee -a evidence/e2e-real.log
    exit 2
fi

if [ -z "${PROGRAM_ID}" ]; then
    echo "[BLOCKED] OSM_REGISTRY_PROGRAM_ID environment variable not set." | tee -a evidence/e2e-real.log
    echo "Deploy program first using: make -C osm-registry deploy" | tee -a evidence/e2e-real.log
    exit 2
fi

TMP_DIR=$(mktemp -d /tmp/atlasmirror-e2e.XXXXXX)
trap 'rm -rf "${TMP_DIR}"' EXIT

PBF_FILE="${TMP_DIR}/snapshot.osm.pbf"
RETRIEVED_FILE="${TMP_DIR}/retrieved.osm.pbf"

# Step 1: Download Geofabrik snapshot and MD5
echo "=== [Step 1] Fetching live published MD5 from Geofabrik ===" | tee -a evidence/e2e-real.log
PUBLISHED_MD5=$(curl -sSf "https://download.geofabrik.de/${TARGET_REGION}-latest.osm.pbf.md5" | awk '{print $1}' | tr '[:upper:]' '[:lower:]')
echo "Published MD5: ${PUBLISHED_MD5}" | tee -a evidence/e2e-real.log

echo "=== [Step 2] Downloading real PBF snapshot ===" | tee -a evidence/e2e-real.log
curl -sSf -o "${PBF_FILE}" "https://download.geofabrik.de/${TARGET_REGION}-latest.osm.pbf"
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

# Step 3: Stream upload via storage_module uploadUrl (Logos Storage streams directly from path)
echo "=== [Step 4] Streaming upload to Logos Storage via uploadUrl ===" | tee -a evidence/e2e-real.log
UPLOAD_RESP=$(logoscore call storage_module uploadUrl "${PBF_FILE}" 1048576 --json | tee -a evidence/e2e-real.log)
REAL_CID=$(echo "${UPLOAD_RESP}" | grep -o '"cid": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")

if [ -z "${REAL_CID}" ]; then
    echo "[FAIL] storageUploadDone did not return a valid CID" | tee -a evidence/e2e-real.log
    exit 1
fi
echo "Real CID from storage_module: ${REAL_CID}" | tee -a evidence/e2e-real.log

# Step 4: Register in LEZ on-chain registry via generated SPEL CLI
echo "=== [Step 5] Submitting on-chain registration to LEZ via spel CLI ===" | tee -a evidence/e2e-real.log
TX_OUTPUT=$(spel --idl osm-registry/idl/osm_registry.json -p "${PROGRAM_ID}" -- \
    register-region \
    --region "${TARGET_REGION}" \
    --level "subregion" \
    --cid "${REAL_CID}" \
    --source-url "https://download.geofabrik.de/${TARGET_REGION}-latest.osm.pbf" \
    --checksum "${COMPUTED_MD5}" \
    --version "$(date +%Y-%m-%d)" \
    --timestamp "$(date +%s)" | tee -a evidence/e2e-real.log)

echo "=== [Step 6] Querying on-chain state via spel inspect ===" | tee -a evidence/e2e-real.log
QUERY_OUTPUT=$(spel inspect --program-id "${PROGRAM_ID}" --region "${TARGET_REGION}" | tee -a evidence/e2e-real.log)

# Step 5: Download snapshot by CID via storage_module downloadToUrl
echo "=== [Step 7] Downloading snapshot by CID from Logos Storage ===" | tee -a evidence/e2e-real.log
logoscore call storage_module downloadToUrl "${REAL_CID}" "${RETRIEVED_FILE}" false 1048576 --json | tee -a evidence/e2e-real.log

# Step 6: Verify exact byte-for-byte SHA256 equality
echo "=== [Step 8] Verifying byte-for-byte SHA256 equality ===" | tee -a evidence/e2e-real.log
RETRIEVED_SHA256=$(sha256sum "${RETRIEVED_FILE}" | awk '{print $1}')
echo "Retrieved SHA256: ${RETRIEVED_SHA256}" | tee -a evidence/e2e-real.log

if [ "${ORIGINAL_SHA256}" != "${RETRIEVED_SHA256}" ]; then
    echo "[FAIL] SHA256 mismatch between original and downloaded PBF snapshot!" | tee -a evidence/e2e-real.log
    exit 1
fi

echo "========================================================"
echo "[PASS] REAL END-TO-END PBF PIPELINE VERIFIED SUCCESSFULLY!"
echo "========================================================" | tee -a evidence/e2e-real.log
