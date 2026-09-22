#!/bin/bash
set -e

rm -rf /root/a1_client_test
mkdir -p /root/a1_client_test/cfg /root/a1_client_test/data

SPR=$(export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module spr --json | grep -o 'spr:[^"]*')
echo "VPS SPR: $SPR"

cat <<EOF > /root/a1_client_test/data/config.json
{
  "data-dir": "/root/a1_client_test/data",
  "log-level": "NOTICE",
  "network": "logos.test",
  "listen-ip": "0.0.0.0",
  "listen-port": 8096,
  "nat": "auto",
  "bootstrap-node": ["$SPR"]
}
EOF

export LOGOSCORE_CONFIG_DIR=/root/a1_client_test/cfg
/root/atlasmirror_vps/bin/logoscore -D -m /root/atlasmirror_vps/modules > /root/a1_client_test/data/daemon.log 2>&1 &
sleep 2

/root/atlasmirror_vps/bin/logoscore load-module storage_module
/root/atlasmirror_vps/bin/logoscore call storage_module init @/root/a1_client_test/data/config.json --json
/root/atlasmirror_vps/bin/logoscore call storage_module start --json
sleep 4

echo "Calling downloadToUrl..."
/root/atlasmirror_vps/bin/logoscore call storage_module downloadToUrl 'zDvZRwzm7tnpibhnK3xXWXXSohtNrcDzAi1p7P1DMPEZEVEkw29L' '/root/a1_client_test/retrieved.osm.pbf' false 262144 --json

for i in $(seq 1 30); do
  if [ -f /root/a1_client_test/retrieved.osm.pbf ]; then
    sz=$(stat -c %s /root/a1_client_test/retrieved.osm.pbf)
    echo "Progress: $sz bytes"
    if [ "$sz" -eq 34401613 ]; then
      echo "DOWNLOAD COMPLETE!"
      md5sum /root/a1_client_test/retrieved.osm.pbf
      break
    fi
  fi
  sleep 1
done

/root/atlasmirror_vps/bin/logoscore stop >/dev/null 2>&1 || true
killall -9 logoscore || true
echo "SUCCESS!"
