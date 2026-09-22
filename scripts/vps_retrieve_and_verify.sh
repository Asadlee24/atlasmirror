#!/bin/bash
set -e

CID="$1"
EXPECTED_SIZE="$2"

if [ -z "$CID" ] || [ -z "$EXPECTED_SIZE" ]; then
  echo "Usage: $0 <cid> <expected_size>"
  exit 1
fi

rm -rf /root/a1_client_retrieval
mkdir -p /root/a1_client_retrieval/cfg /root/a1_client_retrieval/data

SPR=$(export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module spr --json | grep -o 'spr:[^"]*')
if [ -z "$SPR" ]; then
  echo "ERROR: Failed to obtain VPS SPR"
  exit 1
fi

cat <<EOF > /root/a1_client_retrieval/data/config.json
{
  "data-dir": "/root/a1_client_retrieval/data",
  "log-level": "NOTICE",
  "network": "logos.test",
  "listen-ip": "0.0.0.0",
  "listen-port": 8097,
  "nat": "auto",
  "bootstrap-node": ["$SPR"]
}
EOF

export LOGOSCORE_CONFIG_DIR=/root/a1_client_retrieval/cfg
/root/atlasmirror_vps/bin/logoscore -D -m /root/atlasmirror_vps/modules > /root/a1_client_retrieval/data/daemon.log 2>&1 &
CLIENT_PID=$!
sleep 2

/root/atlasmirror_vps/bin/logoscore load-module storage_module >/dev/null 2>&1
/root/atlasmirror_vps/bin/logoscore call storage_module init @/root/a1_client_retrieval/data/config.json --json >/dev/null 2>&1
/root/atlasmirror_vps/bin/logoscore call storage_module start --json >/dev/null 2>&1

# Wait for client storage node to start and connect to bootstrap (max 15s)
for i in $(seq 1 15); do
  if grep -q "Started Storage node" /root/a1_client_retrieval/data/daemon.log 2>/dev/null; then
    break
  fi
  sleep 1
done

# Download manifest first with retry
MANIFEST_OK=0
for attempt in $(seq 1 10); do
  RES=$(/root/atlasmirror_vps/bin/logoscore call storage_module downloadManifest "$CID" --json 2>&1 || true)
  if echo "$RES" | grep -q '"success":true'; then
    MANIFEST_OK=1
    break
  fi
  sleep 2
done

TARGET_FILE="/root/a1_client_retrieval/retrieved.osm.pbf"
/root/atlasmirror_vps/bin/logoscore call storage_module downloadToUrl "$CID" "$TARGET_FILE" false 262144 --json >/dev/null 2>&1

SUCCESS=0
for i in $(seq 1 60); do
  if [ -f "$TARGET_FILE" ]; then
    CUR_SZ=$(stat -c %s "$TARGET_FILE" 2>/dev/null || echo 0)
    if [ "$CUR_SZ" -eq "$EXPECTED_SIZE" ]; then
      SUCCESS=1
      break
    fi
  fi
  sleep 1
done

# Stop only this client process
kill -9 $CLIENT_PID 2>/dev/null || true
pkill -9 -P $CLIENT_PID 2>/dev/null || true

if [ "$SUCCESS" -eq 1 ]; then
  COMPUTED_MD5=$(md5sum "$TARGET_FILE" | awk '{print $1}')
  echo "RETRIEVAL_STATUS: SUCCESS"
  echo "RETRIEVED_SIZE: $EXPECTED_SIZE"
  echo "RETRIEVED_MD5: $COMPUTED_MD5"
  rm -rf /root/a1_client_retrieval
  exit 0
else
  echo "ERROR: Download timed out or size mismatch (got $CUR_SZ, expected $EXPECTED_SIZE)"
  rm -rf /root/a1_client_retrieval
  exit 1
fi
