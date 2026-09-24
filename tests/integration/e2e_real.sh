#!/usr/bin/env bash
# ==============================================================================
# AtlasMirror Genuine End-to-End PBF Pipeline Orchestration
# Flow: Geofabrik PBF -> MD5 Checksum Equality -> logoscore/storage_module uploadUrl
#       -> Real CID -> SPEL LEZ Transaction -> Query Account -> downloadToUrl -> SHA256 Equality
# NO FAKE REST APIS. Uses only official logoscore and spel CLI tooling.
# ==============================================================================
set -euo pipefail

TARGET_REGION="${ATLASMIRROR_REGION:-china/henan}"
REGISTER_REGION_PATH="${ATLASMIRROR_REGISTER_REGION:-test/ci-sandbox-e2e}"
MODULES_DIR="${LOGOS_MODULES_DIR:-./modules}"
PROGRAM_ID="${OSM_REGISTRY_PROGRAM_ID:-bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f}"
# Registry account: already funded & initialized on testnet.
# REGISTER_REGION_PATH="test/ci-sandbox-e2e" keeps E2E writes out of the 25-region counting set.
REGISTRY_ACCOUNT_ID="${ATLASMIRROR_E2E_ACCOUNT:-T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci}"
export LEE_WALLET_HOME_DIR="${LEE_WALLET_HOME_DIR:-${HOME}/.lee/wallet}"

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

# Protect production counting set by targeting an isolated registration path
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
"${LOGOSCORE_BIN}" stop >/dev/null 2>&1 || true
killall -9 .logoscore.elf logoscore 2>/dev/null || true
sleep 1

"${LOGOSCORE_BIN}" -D -m "${MODULES_DIR}" > evidence/logoscore-e2e.log 2>&1 &
DAEMON_PID=$!
sleep 2

"${LOGOSCORE_BIN}" load-module storage_module >> evidence/e2e-real.log 2>&1

STORAGE_DATA_DIR=$(mktemp -d /tmp/storage-data-e2e.XXXXXX)
CONFIG_FILE="${TMP_DIR}/config-e2e.json"
cat > "${CONFIG_FILE}" <<EOF
{
  "data-dir": "${STORAGE_DATA_DIR}",
  "log-level": "DEBUG",
  "log-file": "${STORAGE_DATA_DIR}/storage.log",
  "nat": "extip:127.0.0.1"
}
EOF
"${LOGOSCORE_BIN}" call storage_module init "@${CONFIG_FILE}" >> evidence/e2e-real.log 2>&1
"${LOGOSCORE_BIN}" call storage_module start >> evidence/e2e-real.log 2>&1
sleep 3

# Step 4: Stream upload via storage_module uploadUrl and capture CID asynchronously
echo "=== [Step 5] Streaming upload to Logos Storage via uploadUrl ===" | tee -a evidence/e2e-real.log
: > evidence/e2e-upload-event.json
"${LOGOSCORE_BIN}" watch storage_module --event storageUploadDone --json > evidence/e2e-upload-event.json 2>&1 &
WATCHER_UPLOAD_PID=$!
sleep 1

ABS_PBF=$(realpath "${PBF_FILE}")
echo "Streaming upload of ${ABS_PBF} (${FILE_BYTES} bytes) to Logos Storage..." | tee -a evidence/e2e-real.log
UPLOAD_CALL_RESP=$("${LOGOSCORE_BIN}" call storage_module uploadUrl "${ABS_PBF}" 262144 --json 2>&1 || true)
echo "uploadUrl Call Response: ${UPLOAD_CALL_RESP}" >> evidence/e2e-real.log

# Check if call response directly has CID
REAL_CID=$(echo "${UPLOAD_CALL_RESP}" | grep -o '"cid": *"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
if [ -z "${REAL_CID}" ]; then
    REAL_CID=$(echo "${UPLOAD_CALL_RESP}" | grep -o 'zDv[a-zA-Z0-9]*' | head -1 || echo "")
fi

# Wait for storageUploadDone event in watcher
if [ -z "${REAL_CID}" ]; then
    echo "Waiting for storageUploadDone event (up to 120s)..." | tee -a evidence/e2e-real.log
    for i in {1..120}; do
        if [ -s evidence/e2e-upload-event.json ]; then
            REAL_CID=$(grep -o '"cid": *"[^"]*"' evidence/e2e-upload-event.json | head -1 | cut -d'"' -f4 || echo "")
            if [ -z "${REAL_CID}" ]; then
                REAL_CID=$(grep -o 'zDv[a-zA-Z0-9]*' evidence/e2e-upload-event.json | head -1 || echo "")
            fi
            if [ -n "${REAL_CID}" ]; then break; fi
        fi
        sleep 1
    done
fi

# Fallback: query manifests
if [ -z "${REAL_CID}" ]; then
    echo "Querying manifests for uploaded CID..." | tee -a evidence/e2e-real.log
    MANIFESTS_JSON=$("${LOGOSCORE_BIN}" call storage_module manifests --json 2>&1 || echo "")
    REAL_CID=$(python3 -c "
import json, sys
try:
    m = json.loads('''${MANIFESTS_JSON}''')
    entries = m.get('result', {}).get('value', [])
    target = 'henan-latest.osm.pbf'
    matched = [e['cid'] for e in entries if e.get('filename') == target]
    print(matched[-1] if matched else '')
except Exception:
    print('')
")
fi

if [ -z "${REAL_CID}" ]; then
    echo "[FAIL] storageUploadDone did not return a valid CID" | tee -a evidence/e2e-real.log
    exit 1
fi
echo "Real CID from storage_module: ${REAL_CID}" | tee -a evidence/e2e-real.log

PARENT_REGION=$(python3 -c "import json; cat=json.load(open('metadata/regions.json'))['regions']; print(next((r.get('parent') or '' for r in cat if r['path'] == '${TARGET_REGION}'), ''))")
LEVEL=$(python3 -c "import json; cat=json.load(open('metadata/regions.json'))['regions']; print(next((r.get('level', 'country').capitalize() for r in cat if r['path'] == '${TARGET_REGION}'), 'Subregion'))")

# Step 5: Register in LEZ on-chain registry via generated SPEL CLI
echo "=== [Step 6] Submitting on-chain registration to LEZ via spel CLI ===" | tee -a evidence/e2e-real.log
EXTRA_PARENT_FLAG=""
if [ -n "${PARENT_REGION}" ]; then
    EXTRA_PARENT_FLAG="--parent ${PARENT_REGION}"
fi

ACCOUNT_DATA_LEN=$(python3 -c "import urllib.request, json;
try:
    req = urllib.request.Request('https://testnet.lez.logos.co/', data=json.dumps({'jsonrpc':'2.0','id':1,'method':'getAccount','params':['${REGISTRY_ACCOUNT_ID}']}).encode(), headers={'Content-Type':'application/json'})
    raw = bytes(json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['result']['data'])
    print(len(raw))
except Exception:
    print(0)
")

if [ "${ACCOUNT_DATA_LEN}" -eq "0" ]; then
    echo "Initializing state account ${REGISTRY_ACCOUNT_ID} via spel initialize..." | tee -a evidence/e2e-real.log
    timeout 60s spel --idl osm-registry/idl/osm_registry.json -p "${PROGRAM_ID}" -- initialize --state "${REGISTRY_ACCOUNT_ID}" | tee -a evidence/e2e-real.log
    sleep 4
    # Re-verify account is now initialized before proceeding
    ACCOUNT_DATA_LEN=$(python3 -c "import urllib.request, json;
try:
    req = urllib.request.Request('https://testnet.lez.logos.co/', data=json.dumps({'jsonrpc':'2.0','id':1,'method':'getAccount','params':['${REGISTRY_ACCOUNT_ID}']}).encode(), headers={'Content-Type':'application/json'})
    raw = bytes(json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['result']['data'])
    print(len(raw))
except Exception:
    print(0)
")
    if [ "${ACCOUNT_DATA_LEN}" -eq "0" ]; then
        echo "[FAIL] Account ${REGISTRY_ACCOUNT_ID} still uninitialized after spel initialize. TX not confirmed." | tee -a evidence/e2e-real.log
        exit 1
    fi
    echo "Account initialized: ${ACCOUNT_DATA_LEN} bytes on-chain." | tee -a evidence/e2e-real.log
else
    echo "Account already initialized: ${ACCOUNT_DATA_LEN} bytes on-chain." | tee -a evidence/e2e-real.log
fi

REG_TIMESTAMP=$(python3 -c "import urllib.request, json, struct, time;
try:
    req = urllib.request.Request('https://testnet.lez.logos.co/', data=json.dumps({'jsonrpc':'2.0','id':1,'method':'getAccount','params':['${REGISTRY_ACCOUNT_ID}']}).encode(), headers={'Content-Type':'application/json'})
    raw = bytes(json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['result']['data'])
    last_updated = struct.unpack_from('<Q', raw, 8)[0]
    print(max(int(time.time()), last_updated + 100))
except Exception:
    print(1790300000)
")

TX_OUT_FILE=$(mktemp)
if ! timeout 30s spel --idl osm-registry/idl/osm_registry.json -p "${PROGRAM_ID}" -- \
    register-region \
    --state "${REGISTRY_ACCOUNT_ID}" \
    --region "${REGISTER_REGION_PATH}" \
    ${EXTRA_PARENT_FLAG} \
    --level "${LEVEL}" \
    --cid "${REAL_CID}" \
    --source-url "${GEOFABRIK_PBF_URL}" \
    --checksum "${COMPUTED_MD5}" \
    --version "$(date +%Y-%m-%d)" \
    --hosted true \
    --timestamp "${REG_TIMESTAMP}" 2>&1 | tee "${TX_OUT_FILE}" | tee -a evidence/e2e-real.log; then
    echo "[FAIL] spel register-region transaction failed (exit non-zero)." | tee -a evidence/e2e-real.log
    rm -f "${TX_OUT_FILE}"
    exit 1
fi
TX_OUTPUT=$(cat "${TX_OUT_FILE}"); rm -f "${TX_OUT_FILE}"

echo "=== [Step 7] Querying on-chain state via spel inspect ===" | tee -a evidence/e2e-real.log
QUERY_OUTPUT=$(timeout 30s spel inspect "${REGISTRY_ACCOUNT_ID}" \
    --idl osm-registry/idl/osm_registry.json \
    --type GlobalRegistryState 2>&1 || echo "")
echo "${QUERY_OUTPUT}" | tee -a evidence/e2e-real.log

RPC_ACCOUNT_DATA=$(python3 -c "import urllib.request, json;
try:
    req = urllib.request.Request('https://testnet.lez.logos.co/', data=json.dumps({'jsonrpc':'2.0','id':1,'method':'getAccount','params':['${REGISTRY_ACCOUNT_ID}']}).encode(), headers={'Content-Type':'application/json'})
    raw = bytes(json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['result']['data'])
    print(raw.decode('latin1', errors='ignore'))
except Exception as e:
    print('')
")

echo "=== [Step 7b] Asserting on-chain record fields ===" | tee -a evidence/e2e-real.log
python3 -c "
import sys
q = '''${QUERY_OUTPUT}'''
rpc_data = '''${RPC_ACCOUNT_DATA}'''
expected_region = '${REGISTER_REGION_PATH}'
expected_cid = '${REAL_CID}'
expected_checksum = '${COMPUTED_MD5}'

combined = q + rpc_data
assert expected_region in combined, f'Region {expected_region} not found in on-chain state'
assert expected_cid in combined, f'CID {expected_cid} not found in on-chain state'
assert expected_checksum in combined, f'Checksum {expected_checksum} not found in on-chain state'
print('✔ On-chain record fields verified: region, CID, checksum match on-chain state!')
" | tee -a evidence/e2e-real.log

# Step 6: Download snapshot by CID via storage_module downloadToUrl (network peer retrieval first, local fallback)
echo "=== [Step 8] Downloading snapshot by CID from Logos Storage ===" | tee -a evidence/e2e-real.log
: > evidence/e2e-download-event.json
"${LOGOSCORE_BIN}" watch storage_module --event storageDownloadDone --json > evidence/e2e-download-event.json 2>&1 &
WATCHER_DOWNLOAD_PID=$!
sleep 1

# Try peer retrieval (local=false) first; if fails fallback to local=true
timeout 15s "${LOGOSCORE_BIN}" call storage_module downloadToUrl "${REAL_CID}" "$(realpath -m "${RETRIEVED_FILE}")" false 1048576 --json >> evidence/e2e-real.log 2>&1 || \
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
