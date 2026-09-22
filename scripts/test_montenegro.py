import subprocess
import time
import json
import sys
from pathlib import Path

SSH_KEY = Path.home() / ".ssh" / "id_ed25519"

def run_ssh(cmd):
    full_cmd = ["ssh", "-i", str(SSH_KEY), "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", "root@199.231.187.97", cmd]
    return subprocess.run(full_cmd, capture_output=True, text=True)

# 1. Get SPR
res = run_ssh("export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module spr --json")
spr = None
for line in res.stdout.splitlines():
    if '"success":true' in line and "spr:CiU" in line:
        spr = json.loads(line)["result"]["value"]
        break

print("Got SPR:", spr[:50] + "...")

# 2. Setup client dir
client_dir = Path("/root/a1_client")
subprocess.run(["killall", "-9", "logoscore"], capture_output=True)
time.sleep(1)
subprocess.run(["rm", "-rf", str(client_dir)])
cfg_dir = client_dir / "cfg"
data_dir = client_dir / "data"
cfg_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)

cfg = {
    "data-dir": str(data_dir),
    "log-level": "NOTICE",
    "network": "logos.test",
    "listen-ip": "0.0.0.0",
    "listen-port": 8095,
    "nat": "auto",
    "bootstrap-node": [spr]
}
(data_dir / "config.json").write_text(json.dumps(cfg, indent=2))

logoscore = "/mnt/c/Users/Aftab/Desktop/atlasmirror/logos/bin/logoscore"
modules = "/mnt/c/Users/Aftab/Desktop/atlasmirror/modules"

subprocess.Popen(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore} -D -m {modules} > {data_dir}/daemon.log 2>&1", shell=True)
time.sleep(2)
subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore} load-module storage_module", shell=True)
subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore} call storage_module init @{data_dir / 'config.json'} --json", shell=True)
subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore} call storage_module start --json", shell=True)
print("Storage client started. Waiting 10s for peer connection...")
time.sleep(10)

cid = "zDvZRwzm7tnpibhnK3xXWXXSohtNrcDzAi1p7P1DMPEZEVEkw29L"
print(f"Calling downloadManifest for {cid}...")
dl_res = subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore} call storage_module downloadManifest '{cid}' --json", shell=True, capture_output=True, text=True)
print("downloadManifest call result:", dl_res.stdout.strip())

time.sleep(3)
daemon_log = (data_dir / "daemon.log").read_text()
for line in daemon_log.splitlines()[-10:]:
    print("[DAEMON]", line)
