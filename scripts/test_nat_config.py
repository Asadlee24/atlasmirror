#!/usr/bin/env python3
import json
import time
import subprocess
from pathlib import Path

REPO_ROOT = Path("/mnt/c/Users/Aftab/Desktop/atlasmirror")
LOGOSCORE_BIN = REPO_ROOT / "logos" / "bin" / "logoscore"
MODULES_DIR = REPO_ROOT / "modules"
TEST_DIR = REPO_ROOT / "test_nodes"

def main():
    subprocess.run("killall -9 logoscore 2>/dev/null || true", shell=True)
    subprocess.run(f"rm -rf {TEST_DIR} && mkdir -p {TEST_DIR}/n1_cfg {TEST_DIR}/n1_data {TEST_DIR}/n2_cfg {TEST_DIR}/n2_data", shell=True)

    c1 = {
        "data-dir": str(TEST_DIR / "n1_data"),
        "network": "logos.test",
        "listen-ip": "0.0.0.0",
        "listen-port": 8071,
        "nat": "extip:127.0.0.1"
    }
    (TEST_DIR / "n1_data/config.json").write_text(json.dumps(c1, indent=2))

    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n1_cfg && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > {TEST_DIR}/n1_data/daemon.log 2>&1 &", shell=True)
    time.sleep(2)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n1_cfg && {LOGOSCORE_BIN} load-module storage_module", shell=True)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n1_cfg && {LOGOSCORE_BIN} call storage_module init @{TEST_DIR}/n1_data/config.json --json", shell=True)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n1_cfg && {LOGOSCORE_BIN} call storage_module start --json", shell=True)
    time.sleep(3)

    spr1_res = subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n1_cfg && {LOGOSCORE_BIN} call storage_module spr --json", shell=True, capture_output=True, text=True)
    spr1 = json.loads(spr1_res.stdout)["result"]["value"]
    print("Node 1 SPR:", spr1)

    c2 = {
        "data-dir": str(TEST_DIR / "n2_data"),
        "network": "logos.test",
        "listen-ip": "0.0.0.0",
        "listen-port": 8072,
        "nat": "extip:127.0.0.1",
        "bootstrap-node": [spr1]
    }
    (TEST_DIR / "n2_data/config.json").write_text(json.dumps(c2, indent=2))

    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n2_cfg && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > {TEST_DIR}/n2_data/daemon.log 2>&1 &", shell=True)
    time.sleep(2)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n2_cfg && {LOGOSCORE_BIN} load-module storage_module", shell=True)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n2_cfg && {LOGOSCORE_BIN} call storage_module init @{TEST_DIR}/n2_data/config.json --json", shell=True)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n2_cfg && {LOGOSCORE_BIN} call storage_module start --json", shell=True)
    time.sleep(3)

    debug2_res = subprocess.run(f"export LOGOSCORE_CONFIG_DIR={TEST_DIR}/n2_cfg && {LOGOSCORE_BIN} call storage_module debug --json", shell=True, capture_output=True, text=True)
    print("Node 2 Debug:\n", debug2_res.stdout)

if __name__ == "__main__":
    main()
