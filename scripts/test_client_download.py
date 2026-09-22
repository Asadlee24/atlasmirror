#!/usr/bin/env python3
import sys
import time
import json
import hashlib
import subprocess
from pathlib import Path

CID = sys.argv[1]
EXPECTED_SIZE = int(sys.argv[2])
EXPECTED_MD5 = sys.argv[3]

CLIENT_DIR = Path("/root/a1_client")
LOGOSCORE_BIN = "/mnt/c/Users/Aftab/Desktop/atlasmirror/logos/bin/logoscore"
MODULES_DIR = "/mnt/c/Users/Aftab/Desktop/atlasmirror/modules"

# Get VPS SPR via SSH
res = subprocess.run([
    "ssh", "-i", "/root/.ssh/id_ed25519",
    "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
    "root@199.231.187.97",
    "export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module spr --json"
], capture_output=True, text=True)

spr = None
for line in res.stdout.splitlines():
    if '"success":true' in line and "spr:CiU" in line:
        spr = json.loads(line)["result"]["value"]
        break

assert spr, "Failed to get VPS SPR!"
print(f"Got VPS SPR: {spr[:50]}...")

# Clean and create client dir
subprocess.run(["killall", "-9", "logoscore"], capture_output=True)
time.sleep(1)
if CLIENT_DIR.exists():
    subprocess.run(["rm", "-rf", str(CLIENT_DIR)])

cfg_dir = CLIENT_DIR / "cfg"
data_dir = CLIENT_DIR / "data"
cfg_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)

config = {
    "data-dir": str(data_dir),
    "log-level": "NOTICE",
    "network": "logos.test",
    "listen-ip": "0.0.0.0",
    "listen-port": 8095,
    "nat": "auto",
    "bootstrap-node": [spr]
}
(data_dir / "config.json").write_text(json.dumps(config, indent=2))

subprocess.Popen(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > {data_dir}/daemon.log 2>&1", shell=True)
time.sleep(2)

subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {LOGOSCORE_BIN} load-module storage_module", shell=True)
subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {LOGOSCORE_BIN} call storage_module init @{data_dir / 'config.json'} --json", shell=True)
subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {LOGOSCORE_BIN} call storage_module start --json", shell=True)
print("Client storage module started. Waiting 12s for peer bootstrap connection...")
time.sleep(12)

# Fetch manifest with event watcher
manifest_ok = False
for m_retry in range(1, 6):
    print(f"Fetching manifest (attempt {m_retry}/5)...")
    dl_m_event = data_dir / "dl-manifest-event.json"
    if dl_m_event.exists():
        dl_m_event.unlink()
    dl_m_event.touch()

    w_m = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadManifestDone --json > {dl_m_event} 2>&1",
        shell=True
    )
    time.sleep(1)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {LOGOSCORE_BIN} call storage_module downloadManifest '{CID}' --json", shell=True)

    for _ in range(30):
        if dl_m_event.stat().st_size > 0:
            try:
                for line in dl_m_event.read_text().splitlines():
                    ev = json.loads(line)
                    if ev.get("event") == "storageDownloadManifestDone":
                        inner = json.loads(ev["data"]["arg0"])
                        if inner.get("success") is True:
                            manifest_ok = True
                            break
                        elif inner.get("success") is False:
                            print(f"[WARN] Manifest event error: {inner.get('error')}")
                            break
            except Exception:
                pass
            if manifest_ok:
                break
        time.sleep(1)
    w_m.kill()
    if manifest_ok:
        print("✅ Manifest downloaded and ready in local client!")
        break
    time.sleep(5)

assert manifest_ok, "Failed to download manifest via event watcher!"

target_file = data_dir / "retrieved.osm.pbf"
print(f"Calling downloadToUrl for CID {CID} to {target_file}...")
res_dl = subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {LOGOSCORE_BIN} call storage_module downloadToUrl '{CID}' '{target_file}' false 262144 --json", shell=True, capture_output=True, text=True)
print("downloadToUrl response:", res_dl.stdout.strip())

success = False
for i in range(180):
    if target_file.exists():
        cur_sz = target_file.stat().st_size
        if cur_sz == EXPECTED_SIZE:
            print(f"Download complete: {cur_sz}/{EXPECTED_SIZE} bytes ({i}s)!")
            success = True
            break
        elif i % 5 == 0:
            pct = (cur_sz / EXPECTED_SIZE) * 100
            print(f"Progress ({i}s): {cur_sz:,} / {EXPECTED_SIZE:,} bytes ({pct:.1f}%)")
    time.sleep(1)

# Clean up
subprocess.run(["killall", "-9", "logoscore"], capture_output=True)

assert success, f"Download timed out or size mismatch!"
with open(target_file, "rb") as f:
    calc_md5 = hashlib.md5(f.read()).hexdigest()

print(f"Retrieved MD5: {calc_md5}")
print(f"Expected MD5:  {EXPECTED_MD5}")
assert calc_md5 == EXPECTED_MD5, f"MD5 mismatch!"
print("🎉 CRYPTOGRAPHIC PROOF VERIFIED: 100% EXACT BYTE-FOR-BYTE MATCH!")
target_file.unlink()
