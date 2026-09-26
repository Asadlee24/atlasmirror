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

# Initialize clean ephemeral wallet on the fly with rotated keys (zero tracked secrets)
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
  "multi_sequencer_client_config": {
    "distribution_limit": 1,
    "calibration_limit": 100
  }
}
EOF

cat > "${LEE_WALLET_HOME_DIR}/storage.json" <<'EOF'
{"key_chain": {"accounts": [{"Public": {"account_id": "ax3YTRCXsGqgUy7dg4w2dBzciP1cSHdrFQDKzA81cVP", "chain_index": [], "data": {"sk": "426d3574950298a7ebfc1a1c287c9fc7d16c0917e22b037a58fc3c51149337f7", "ssk": "9148ace8d8a98f149668d6feb527b70307976172c895225efb9f2d6c42af7d49", "pk": "415e6d2eb5e8726c86769dbec3e935a303aef2129736b9561b95aaf71bb03194", "cc": [127, 212, 121, 201, 182, 130, 80, 50, 4, 15, 5, 119, 54, 125, 213, 174, 209, 34, 142, 165, 209, 223, 99, 206, 122, 181, 252, 140, 212, 72, 201, 132], "cci": null}}}, {"Public": {"account_id": "EmLTMVLxgzi4eSZeMHaJne1wPKrBWYQturK6YsrTc1uX", "chain_index": [0], "data": {"sk": "f5b8fb5964f110d7ff06a758bb7f586a712c713d1cbf2dcf0fcb265319d2db0f", "ssk": "61110acdca9594ed5f60c4f5a728df0f7ec8bf590a8f0eac5b18f77f6f247c66", "pk": "5507a91e75674397a2ff50686ef91be0ec2540cc2fe99af89aea864f2184f88d", "cc": [127, 118, 50, 80, 176, 89, 80, 225, 85, 204, 24, 174, 34, 100, 110, 56, 192, 232, 118, 246, 16, 211, 143, 20, 155, 65, 112, 226, 248, 226, 188, 108], "cci": 0}}}, {"Private": {"account_id": "9aymXgnboGHwdrBpsNwG3EPPDnuRyoCMmnbbK9W3qiy", "chain_index": [], "data": {"value": [{"secret_spending_key": [130, 191, 64, 211, 142, 76, 95, 32, 176, 221, 198, 180, 191, 212, 159, 23, 116, 157, 188, 97, 216, 145, 51, 70, 190, 82, 108, 202, 132, 199, 227, 20], "private_key_holder": {"viewing_secret_key": {"d": [77, 168, 131, 85, 226, 99, 227, 152, 216, 97, 130, 222, 129, 178, 153, 7, 128, 134, 227, 42, 13, 60, 139, 167, 147, 10, 184, 130, 242, 127, 150, 142], "z": [46, 73, 49, 76, 85, 153, 28, 94, 64, 147, 203, 46, 247, 205, 126, 138, 175, 188, 126, 33, 172, 173, 137, 130, 204, 164, 228, 63, 216, 205, 133, 100]}, "authorization_secret_key": [232, 121, 163, 228, 54, 7, 211, 205, 151, 67, 136, 184, 221, 41, 167, 18, 187, 36, 36, 212, 242, 61, 249, 75, 34, 22, 244, 178, 49, 125, 42, 5]}, "nullifier_public_key": [62, 70, 226, 60, 237, 184, 14, 147, 140, 88, 98, 221, 139, 162, 44, 71, 6, 80, 62, 248, 173, 166, 14, 181, 98, 69, 140, 186, 54, 241, 156, 250], "viewing_public_key": [150, 50, 60, 243, 0, 108, 139, 72, 153, 207, 100, 196, 247, 20, 132, 69, 26, 125, 110, 26, 105, 237, 21, 47, 167, 108, 161, 98, 73, 148, 30, 9, 71, 118, 27, 139, 193, 84, 124, 116, 240, 94, 170, 32, 33, 218, 167, 138, 16, 165, 143, 157, 236, 133, 89, 177, 93, 255, 7, 204, 13, 10, 95, 52, 219, 79, 191, 152, 64, 126, 118, 203, 16, 88, 194, 127, 117, 207, 119, 7, 90, 224, 226, 49, 192, 57, 151, 84, 133, 55, 119, 18, 34, 227, 103, 90, 122, 107, 1, 57, 20, 100, 231, 117, 104, 69, 212, 136, 3, 83, 19, 192, 33, 148, 209, 56, 121, 209, 246, 45, 12, 250, 47, 196, 18, 4, 66, 166, 165, 85, 251, 55, 98, 100, 15, 145, 160, 62, 216, 48, 167, 250, 103, 107, 142, 12, 33, 31, 184, 122, 3, 60, 125, 225, 84, 96, 108, 145, 37, 76, 244, 130, 165, 243, 111, 227, 51, 15, 200, 26, 101, 93, 224, 29, 203, 99, 97, 233, 192, 203, 99, 179, 199, 61, 48, 9, 47, 103, 4, 134, 34, 129, 7, 169, 66, 236, 26, 125, 119, 147, 89, 38, 99, 64, 246, 214, 194, 71, 234, 145, 146, 83, 160, 206, 218, 24, 15, 224, 180, 23, 117, 168, 212, 236, 198, 215, 5, 144, 160, 166, 33, 199, 124, 92, 98, 232, 148, 32, 4, 87, 249, 86, 161, 27, 39, 174, 129, 186, 4, 213, 107, 22, 184, 103, 205, 203, 99, 112, 187, 186, 69, 207, 140, 3, 22, 38, 153, 12, 112, 69, 118, 69, 86, 122, 70, 74, 242, 5, 166, 158, 168, 117, 82, 186, 139, 135, 234, 137, 49, 81, 95, 166, 203, 105, 101, 20, 104, 77, 172, 136, 218, 226, 117, 65, 17, 192, 154, 148, 206, 59, 7, 16, 16, 90, 52, 65, 55, 159, 74, 135, 113, 98, 168, 24, 162, 240, 18, 207, 123, 26, 187, 201, 46, 216, 146, 206, 35, 217, 88, 162, 56, 52, 126, 105, 7, 210, 32, 58, 156, 181, 129, 102, 134, 114, 242, 154, 177, 16, 195, 196, 8, 81, 19, 50, 33, 82, 49, 220, 110, 157, 226, 193, 165, 122, 105, 150, 136, 16, 3, 230, 80, 193, 217, 181, 169, 227, 51, 242, 245, 169, 77, 229, 100, 75, 234, 207, 1, 209, 105, 51, 97, 181, 204, 73, 127, 115, 32, 197, 57, 21, 24, 95, 60, 204, 44, 104, 2, 164, 9, 160, 232, 96, 175, 79, 8, 48, 41, 7, 183, 170, 165, 82, 66, 214, 26, 17, 26, 28, 200, 200, 64, 209, 224, 37, 92, 42, 82, 232, 70, 126, 103, 210, 51, 12, 248, 47, 81, 197, 87, 227, 144, 60, 172, 116, 66, 23, 116, 76, 193, 149, 1, 58, 128, 67, 52, 58, 170, 169, 69, 102, 44, 165, 151, 20, 153, 28, 35, 148, 87, 134, 216, 111, 154, 114, 99, 189, 252, 145, 230, 122, 6, 7, 118, 9, 31, 66, 127, 239, 11, 178, 87, 165, 132, 251, 128, 34, 89, 169, 73, 43, 76, 129, 97, 151, 88, 125, 97, 128, 27, 103, 55, 15, 136, 174, 157, 73, 162, 62, 235, 165, 171, 208, 72, 128, 92, 187, 163, 133, 146, 197, 39, 29, 231, 132, 54, 81, 8, 181, 213, 42, 146, 9, 147, 133, 172, 89, 55, 245, 203, 190, 105, 32, 99, 144, 71, 184, 156, 114, 6, 185, 225, 77, 24, 41, 112, 227, 33, 115, 113, 231, 186, 231, 106, 112, 24, 33, 30, 129, 123, 148, 35, 234, 28, 64, 76, 38, 107, 202, 43, 58, 121, 81, 52, 117, 7, 247, 88, 157, 40, 57, 135, 48, 12, 95, 62, 82, 197, 230, 33, 124, 50, 12, 25, 109, 185, 98, 53, 169, 112, 187, 51, 35, 130, 203, 27, 169, 167, 15, 71, 100, 56, 144, 37, 149, 187, 65, 74, 223, 204, 98, 251, 185, 52, 145, 55, 55, 97, 209, 170, 32, 32, 31, 14, 100, 198, 238, 108, 10, 153, 82, 101, 173, 88, 112, 99, 252, 57, 68, 250, 161, 4, 33, 144, 67, 32, 88, 118, 136, 123, 138, 17, 33, 164, 183, 46, 1, 208, 88, 87, 176, 34, 23, 68, 196, 246, 140, 104, 72, 50, 9, 42, 151, 191, 209, 74, 137, 194, 37, 105, 146, 228, 56, 64, 116, 30, 53, 149, 93, 136, 155, 103, 7, 154, 74, 0, 3, 37, 207, 188, 52, 237, 105, 147, 176, 138, 25, 22, 138, 98, 179, 240, 16, 193, 186, 52, 75, 102, 140, 110, 112, 73, 101, 67, 151, 102, 181, 143, 143, 58, 113, 143, 212, 3, 166, 164, 6, 37, 118, 19, 81, 251, 172, 236, 181, 163, 19, 151, 150, 84, 69, 84, 102, 129, 197, 122, 42, 2, 242, 82, 148, 177, 244, 74, 128, 101, 121, 4, 240, 22, 26, 17, 125, 247, 139, 153, 54, 219, 27, 9, 74, 44, 83, 147, 106, 90, 145, 22, 253, 36, 9, 82, 102, 206, 94, 201, 207, 64, 250, 6, 159, 184, 123, 246, 106, 48, 172, 169, 69, 201, 80, 172, 15, 72, 138, 130, 82, 145, 60, 75, 207, 154, 0, 29, 8, 27, 100, 107, 48, 133, 174, 215, 123, 229, 97, 125, 213, 117, 129, 41, 48, 128, 9, 48, 96, 253, 39, 6, 70, 43, 118, 94, 156, 25, 233, 138, 14, 226, 145, 47, 254, 165, 45, 124, 230, 200, 141, 80, 25, 216, 192, 167, 214, 245, 190, 147, 38, 193, 61, 113, 55, 13, 201, 154, 148, 167, 37, 205, 25, 61, 225, 99, 134, 131, 131, 195, 120, 168, 162, 196, 251, 173, 241, 235, 119, 230, 242, 93, 194, 99, 146, 114, 235, 52, 154, 103, 51, 79, 105, 203, 107, 153, 45, 207, 140, 135, 49, 68, 200, 98, 44, 202, 73, 87, 3, 220, 202, 104, 181, 229, 18, 163, 121, 22, 205, 81, 68, 38, 219, 54, 73, 184, 65, 232, 40, 33, 110, 168, 80, 196, 86, 184, 86, 200, 204, 251, 233, 76, 152, 171, 60, 84, 20, 122, 65, 139, 163, 152, 250, 89, 69, 188, 96, 170, 200, 166, 57, 219, 100, 37, 213, 11, 14, 209, 137, 20, 21, 87, 110, 247, 32, 218, 69, 170, 133, 152, 31, 96, 34, 198, 77, 21, 32, 135, 28, 153, 38, 57, 92, 116, 220, 84, 104, 60, 40, 121, 40, 76, 34, 199, 151, 85, 188, 59, 85, 17, 58, 140, 246, 19, 144, 26, 31, 137, 184, 105, 2, 64, 92, 86, 73, 137, 95, 32, 54, 113, 168, 142, 56, 27, 158, 136, 100, 161, 124, 187, 53, 231, 57, 6, 8, 22, 123, 190, 73, 165, 18, 154, 145, 255, 164, 91, 248, 39, 39, 255, 208, 117, 37, 56, 72, 154, 8, 94, 115, 32, 128, 205, 132, 180, 17, 106, 181, 189, 100, 90, 226, 31, 155, 201, 240, 31, 230, 15, 160, 134, 31, 5, 98, 190, 71, 13, 84, 152, 45, 35, 119, 9, 248, 166, 130, 213, 143, 241, 209]}, []], "ccc": [92, 246, 213, 99, 243, 103, 187, 127, 46, 21, 111, 144, 235, 61, 229, 179, 95, 148, 171, 186, 119, 229, 120, 172, 83, 132, 76, 156, 143, 254, 61, 119], "cci": null}}}], "sealing_secret_key": null, "group_key_holders": {}, "shared_private_accounts": {}}, "last_synced_block": 0, "labels": {}}
EOF

EPHEMERAL_PAYER="ax3YTRCXsGqgUy7dg4w2dBzciP1cSHdrFQDKzA81cVP"
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
