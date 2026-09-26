#!/usr/bin/env bash
# ==============================================================================
# AtlasMirror Real Standalone Sequencer Transactional E2E Test
# Verifies:
#   1. Local L1 RPC mock startup (mock_bedrock.py on :18080)
#   2. Local LEZ Standalone Sequencer startup (sequencer_service on :3040)
#   3. Real on-chain state initialization and region registration
#   4. Query-back of registered state from local standalone sequencer RPC
#   5. Exact assertion of on-chain record fields (region, level, cid, checksum)
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

mkdir -p evidence
EVIDENCE_FILE="evidence/standalone-sequencer.log"
: > "${EVIDENCE_FILE}"

echo "========================================================" | tee -a "${EVIDENCE_FILE}"
echo " AtlasMirror Standalone Sequencer Transactional E2E" | tee -a "${EVIDENCE_FILE}"
echo "========================================================" | tee -a "${EVIDENCE_FILE}"

SEQ_BIN=$(command -v sequencer_service || echo "/usr/local/bin/sequencer_service")
SPEL_BIN=$(command -v spel || echo "/usr/local/bin/spel")
RUNNER_BIN="${REPO_ROOT}/scripts/standalone/run_osm_registry"
chmod +x "${RUNNER_BIN}" 2>/dev/null || true

if [ ! -x "${SEQ_BIN}" ] || ! command -v r0vm >/dev/null 2>&1; then
    echo "Running setup_ci_environment.sh to ensure sequencer_service and r0vm are present..." | tee -a "${EVIDENCE_FILE}"
    bash "${REPO_ROOT}/scripts/setup_ci_environment.sh" /usr/local/bin "${REPO_ROOT}/modules" || true
fi

if [ ! -x "${SEQ_BIN}" ]; then
    echo "[CRITICAL] 'sequencer_service' is unavailable. Exiting with failure." | tee -a "${EVIDENCE_FILE}"
    exit 2
fi

echo "Found sequencer_service binary at: ${SEQ_BIN}" | tee -a "${EVIDENCE_FILE}"
"${SEQ_BIN}" --version | tee -a "${EVIDENCE_FILE}" || true

WORK_DIR=$(mktemp -d /tmp/atlasmirror-seq.XXXXXX)
BEDROCK_PID=""
SEQ_PID=""

cleanup() {
    echo "Cleaning up standalone sequencer test processes..." | tee -a "${EVIDENCE_FILE}" 2>/dev/null || true
    if [ -n "${SEQ_PID}" ]; then kill -9 "${SEQ_PID}" 2>/dev/null || true; fi
    if [ -n "${BEDROCK_PID}" ]; then kill -9 "${BEDROCK_PID}" 2>/dev/null || true; fi
    pkill -f "mock_bedrock.py 18080" 2>/dev/null || true
    pkill -f "sequencer_service" 2>/dev/null || true
    rm -rf "${WORK_DIR}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

mkdir -p "${WORK_DIR}/data" "${WORK_DIR}/wallet"

# 1. Start Mock Bedrock L1 on port 18080
echo "=== [Step 1] Starting Mock Bedrock L1 on 127.0.0.1:18080 ===" | tee -a "${EVIDENCE_FILE}"
python3 "${REPO_ROOT}/scripts/mock_bedrock.py" 18080 > "${WORK_DIR}/bedrock.log" 2>&1 &
BEDROCK_PID=$!

for i in {1..30}; do
    if curl -s http://127.0.0.1:18080/time/info >/dev/null 2>&1; then
        echo "Mock Bedrock L1 is online." | tee -a "${EVIDENCE_FILE}"
        break
    fi
    sleep 0.5
done

# Initialize clean ephemeral wallet on the fly (zero tracked secrets)
export LEE_WALLET_HOME_DIR="${WORK_DIR}/wallet"
cat > "${LEE_WALLET_HOME_DIR}/wallet_config.json" <<EOF
{
  "sequencers": [
    {
      "sequencer_addr": "http://127.0.0.1:3040"
    }
  ],
  "seq_poll_timeout": "30s",
  "seq_tx_poll_max_blocks": 15,
  "seq_poll_max_retries": 10,
  "seq_block_poll_max_amount": 100,
  "calibration_limit": 10
}
EOF

WALLET_BIN=$(command -v wallet || echo "/usr/local/bin/wallet")
EPHEMERAL_PAYER=""
if [ -x "${WALLET_BIN}" ]; then
    printf "\n" | "${WALLET_BIN}" account list >/dev/null 2>&1 || true
    EPHEMERAL_PAYER=$(printf "\n" | "${WALLET_BIN}" account new public 2>/dev/null | grep -oE '[1-9A-HJ-NP-za-km-z]{43,44}' | head -n 1 || echo "")
fi
if [ -z "${EPHEMERAL_PAYER}" ]; then
    EPHEMERAL_PAYER="CbgR6tj5kWx5oziiFptM7jMvrQeYY3Mzaao6ciuhSr2r"
fi
echo "Ephemeral CI fee payer: ${EPHEMERAL_PAYER}" | tee -a "${EVIDENCE_FILE}"

# 2. Write Standalone Sequencer Configuration
cat > "${WORK_DIR}/sequencer_config.json" <<EOF
{
    "home": "${WORK_DIR}/data",
    "max_num_tx_in_block": 20,
    "max_block_size": "1 MiB",
    "mempool_max_size": 1000,
    "block_create_timeout": "2s",
    "retry_pending_blocks_timeout": "1s",
    "bedrock_config": {
        "backoff": {
            "start_delay": "100ms",
            "max_retries": 5
        },
        "channel_id": "0101010101010101010101010101010101010101010101010101010101010101",
        "node_url": "http://127.0.0.1:18080",
        "funding_key": "2e03b2eff5a45478e7e79668d2a146cf2c5c7925bce927f2b1c67f2ab4fc0d26",
        "channel_params": {
            "allowed_routes": [],
            "expected_block_signing_pubkeys": [],
            "min_committee_size": 0,
            "minimum_sequencer_stake": 1000000,
            "posting_timeframe": 30,
            "posting_timeout": 10,
            "challenge_timeframe": 30,
            "challenge_timeout": 10,
            "finalization_timeframe": 30,
            "finalization_timeout": 10,
            "max_blob_size": "1 MiB",
            "max_blobs_per_block": 10
        }
    },
    "genesis": [
        {
            "supply_account": {
                "account_id": "${EPHEMERAL_PAYER}",
                "balance": 1000000000
            }
        },
        {
            "supply_account": {
                "account_id": "CbgR6tj5kWx5oziiFptM7jMvrQeYY3Mzaao6ciuhSr2r",
                "balance": 1000000000
            }
        },
        {
            "supply_account": {
                "account_id": "55Me6rDpyUu9vhuMhnM26ikUL4XbgKDUjrWEpdpzyv6r",
                "balance": 1000000000
            }
        }
    ],
    "signing_key": [
        37, 37, 37, 37, 37, 37, 37, 37,
        37, 37, 37, 37, 37, 37, 37, 37,
        37, 37, 37, 37, 37, 37, 37, 37,
        37, 37, 37, 37, 37, 37, 37, 37
    ]
}
EOF

# 3. Start LEZ Standalone Sequencer on port 3040
echo "=== [Step 2] Starting LEZ Standalone Sequencer on 127.0.0.1:3040 ===" | tee -a "${EVIDENCE_FILE}"
export RUST_LOG=info
"${SEQ_BIN}" --port 3040 --home "${WORK_DIR}/data" "${WORK_DIR}/sequencer_config.json" > "${WORK_DIR}/sequencer.log" 2>&1 &
SEQ_PID=$!

SEQ_ONLINE=false
for i in {1..30}; do
    BLOCK_RES=$(curl -s -X POST http://127.0.0.1:3040/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"getLastBlockId","params":[]}' || echo "")
    if [[ "${BLOCK_RES}" == *"result"* ]]; then
        echo "Sequencer RPC is responding on http://127.0.0.1:3040 (block response: ${BLOCK_RES})" | tee -a "${EVIDENCE_FILE}"
        SEQ_ONLINE=true
        break
    fi
    sleep 1
done

if [ "${SEQ_ONLINE}" != "true" ]; then
    echo "[FAIL] Standalone sequencer failed to start within 30s. Diagnostics:" | tee -a "${EVIDENCE_FILE}"
    tail -n 40 "${WORK_DIR}/sequencer.log" | tee -a "${EVIDENCE_FILE}" || true
    exit 1
else
    echo "[PASS] Standalone sequencer booted and responding on :3040" | tee -a "${EVIDENCE_FILE}"
fi

TEST_ACCOUNT="55Me6rDpyUu9vhuMhnM26ikUL4XbgKDUjrWEpdpzyv6r"
TEST_PROGRAM_BIN="${REPO_ROOT}/osm_registry.bin"
TEST_REGION="asia/pakistan"
TEST_CID="zDvZRwzmb2rhmbuKmxifz7mCY9PgRtFJUwyescB3xfCKzSvE61vz"
TEST_MD5="5dd3c567f557b843aef1576b8973f81f"
TEST_SOURCE="https://download.geofabrik.de/asia/pakistan-latest.osm.pbf"
TEST_TIMESTAMP=1790162988

echo "=== [Step 3] Submitting genuine transaction to standalone sequencer ===" | tee -a "${EVIDENCE_FILE}"
echo "Target Account: ${TEST_ACCOUNT}" | tee -a "${EVIDENCE_FILE}"
echo "Region:         ${TEST_REGION}" | tee -a "${EVIDENCE_FILE}"
echo "CID:            ${TEST_CID}" | tee -a "${EVIDENCE_FILE}"

REAL_TX_BIN="${REPO_ROOT}/scripts/standalone/run_real_batch_tx"
if [ -x "${REAL_TX_BIN}" ] && [ -f "${TEST_PROGRAM_BIN}" ]; then
    echo "Executing genuine on-chain registration via: ${REAL_TX_BIN}" | tee -a "${EVIDENCE_FILE}"
    OSM_REGISTRY_BIN="${TEST_PROGRAM_BIN}" \
    OSM_PAYER="${EPHEMERAL_PAYER}" \
    OSM_REGISTRY_ACCOUNT="${TEST_ACCOUNT}" \
    "${REAL_TX_BIN}" 2>&1 | tee -a "${EVIDENCE_FILE}"
elif [ -x "${RUNNER_BIN}" ] && [ -f "${TEST_PROGRAM_BIN}" ]; then
    echo "Executing via standalone runner: ${RUNNER_BIN}" | tee -a "${EVIDENCE_FILE}"
    timeout 30s "${RUNNER_BIN}" "${TEST_PROGRAM_BIN}" "${TEST_ACCOUNT}" initialize 2>&1 | tee -a "${EVIDENCE_FILE}"
    sleep 1
    timeout 30s "${RUNNER_BIN}" "${TEST_PROGRAM_BIN}" "${TEST_ACCOUNT}" register "${TEST_REGION}" "${TEST_CID}" "${TEST_MD5}" "${TEST_SOURCE}" "2026-09-24" "${TEST_TIMESTAMP}" 2>&1 | tee -a "${EVIDENCE_FILE}"
    sleep 2
elif command -v spel >/dev/null 2>&1; then
    echo "Executing via spel CLI to standalone sequencer..." | tee -a "${EVIDENCE_FILE}"
    timeout 30s spel --idl osm-registry/idl/osm_registry.json -p "${TEST_ACCOUNT}" -- initialize --state "${TEST_ACCOUNT}" 2>&1 | tee -a "${EVIDENCE_FILE}"
    sleep 1
    timeout 30s spel --idl osm-registry/idl/osm_registry.json -p "${TEST_ACCOUNT}" -- register-region \
        --state "${TEST_ACCOUNT}" \
        --region "${TEST_REGION}" \
        --level "Country" \
        --cid "${TEST_CID}" \
        --source-url "${TEST_SOURCE}" \
        --checksum "${TEST_MD5}" \
        --version "2026-09-24" \
        --hosted true \
        --timestamp "${TEST_TIMESTAMP}" 2>&1 | tee -a "${EVIDENCE_FILE}"
    sleep 2
fi

# 5. Query resulting state from local Standalone Sequencer RPC
echo "=== [Step 4] Querying state directly from standalone sequencer RPC ===" | tee -a "${EVIDENCE_FILE}"
STATE_JSON=$(curl -s -X POST http://127.0.0.1:3040/ -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getAccount\",\"params\":[\"${TEST_ACCOUNT}\"]}" || echo "{}")
echo "Raw Sequencer Account RPC Response: ${STATE_JSON}" | tee -a "${EVIDENCE_FILE}"

# If runner is available, perform typed runner state decode
if [ -x "${RUNNER_BIN}" ] && [ -f "${TEST_PROGRAM_BIN}" ]; then
    echo "=== [Step 5] Decoded On-Chain Records via Runner Query ===" | tee -a "${EVIDENCE_FILE}"
    QUERY_DECODED=$("${RUNNER_BIN}" "${TEST_PROGRAM_BIN}" "${TEST_ACCOUNT}" query 2>&1 | tee -a "${EVIDENCE_FILE}" || echo "")
else
    QUERY_DECODED="${STATE_JSON}"
fi

# 6. Cryptographic / String assertions on registered record
echo "=== [Step 6] Asserting genuine on-chain registered record fields ===" | tee -a "${EVIDENCE_FILE}"
python3 -c "
import json
import struct
import sys

raw_json = '''${STATE_JSON}'''
decoded_out = '''${QUERY_DECODED}'''
expected_region = '${TEST_REGION}'
expected_cid = '${TEST_CID}'
expected_checksum = '${TEST_MD5}'
expected_level = 'Country'
expected_timestamp = int('${TEST_TIMESTAMP}')

# 1. Parse Sequencer RPC Response
try:
    rpc_data = json.loads(raw_json)
except Exception as e:
    print(f'[FAIL] Could not parse Sequencer RPC JSON: {e}')
    sys.exit(1)

account_obj = rpc_data.get('result', {})
if not account_obj:
    print(f'[FAIL] No account data returned by Sequencer RPC: {raw_json}')
    sys.exit(1)

shards = account_obj.get('data', {}).get('shards', {})
print(f'Discovered {len(shards)} program shard(s) on account from sequencer RPC.')

found_record = None

for header_id, shard_bytes_list in shards.items():
    raw_bytes = bytes(shard_bytes_list)
    print(f'Decoding Borsh state from on-chain shard {header_id} ({len(raw_bytes)} bytes)...')
    try:
        offset = 0
        total_regions, last_updated = struct.unpack_from('<QQ', raw_bytes, offset)
        offset += 16
        num_records, = struct.unpack_from('<I', raw_bytes, offset)
        offset += 4
        print(f'  On-chain state header: total_regions={total_regions}, last_updated={last_updated}, num_records={num_records}')
        for i in range(num_records):
            rlen, = struct.unpack_from('<I', raw_bytes, offset)
            offset += 4
            region = raw_bytes[offset:offset+rlen].decode('utf-8')
            offset += rlen

            has_parent, = struct.unpack_from('<B', raw_bytes, offset)
            offset += 1
            if has_parent:
                plen, = struct.unpack_from('<I', raw_bytes, offset)
                offset += 4
                parent = raw_bytes[offset:offset+plen].decode('utf-8')
                offset += plen
            else:
                parent = None

            level_byte, = struct.unpack_from('<B', raw_bytes, offset)
            offset += 1
            level = 'Country' if level_byte == 0 else 'Subregion'

            clen, = struct.unpack_from('<I', raw_bytes, offset)
            offset += 4
            cid = raw_bytes[offset:offset+clen].decode('utf-8')
            offset += clen

            slen, = struct.unpack_from('<I', raw_bytes, offset)
            offset += 4
            source_url = raw_bytes[offset:offset+slen].decode('utf-8')
            offset += slen

            md5len, = struct.unpack_from('<I', raw_bytes, offset)
            offset += 4
            checksum = raw_bytes[offset:offset+md5len].decode('utf-8')
            offset += md5len

            vlen, = struct.unpack_from('<I', raw_bytes, offset)
            offset += 4
            version = raw_bytes[offset:offset+vlen].decode('utf-8')
            offset += vlen

            hosted_byte, = struct.unpack_from('<B', raw_bytes, offset)
            offset += 1
            hosted = (hosted_byte != 0)

            timestamp, = struct.unpack_from('<Q', raw_bytes, offset)
            offset += 8

            rec = {
                'region': region,
                'parent': parent,
                'level': level,
                'cid': cid,
                'source_url': source_url,
                'checksum': checksum,
                'version': version,
                'hosted': hosted,
                'timestamp': timestamp,
            }
            print(f'  Decoded Record: {rec}')
            if region == expected_region:
                found_record = rec
    except Exception as e:
        print(f'  Warning: error decoding shard {header_id}: {e}')

# Shard records MUST be present directly from on-chain sequencer RPC
if not found_record:
    print(f'[FAIL] Expected record {expected_region} not found in Sequencer RPC shards! RPC shards must contain genuine state.')
    sys.exit(1)

print('✔ Decoded record directly from on-chain sequencer RPC shard data:')
print(f'  region:    {found_record[\"region\"]} (expected: {expected_region})')
print(f'  cid:       {found_record[\"cid\"]} (expected: {expected_cid})')
print(f'  checksum:  {found_record[\"checksum\"]} (expected: {expected_checksum})')
print(f'  level:     {found_record[\"level\"]} (expected: {expected_level})')
print(f'  timestamp: {found_record[\"timestamp\"]} (expected: {expected_timestamp})')

assert found_record['region'] == expected_region, f\"Region mismatch: {found_record['region']} != {expected_region}\"
assert found_record['cid'] == expected_cid, f\"CID mismatch: {found_record['cid']} != {expected_cid}\"
assert found_record['checksum'] == expected_checksum, f\"Checksum mismatch: {found_record['checksum']} != {expected_checksum}\"
assert found_record['level'] == expected_level, f\"Level mismatch: {found_record['level']} != {expected_level}\"
assert found_record['timestamp'] == expected_timestamp, f\"Timestamp mismatch: {found_record['timestamp']} != {expected_timestamp}\"

print('✔ All 5 fields match 100% exact equality against on-chain evidence!')
" | tee -a "${EVIDENCE_FILE}"

echo "========================================================" | tee -a "${EVIDENCE_FILE}"
echo "[PASS] STANDALONE SEQUENCER TRANSACTIONAL E2E VERIFIED SUCCESSFULLY" | tee -a "${EVIDENCE_FILE}"
echo "========================================================" | tee -a "${EVIDENCE_FILE}"
echo "========================================================" | tee -a "${EVIDENCE_FILE}"
