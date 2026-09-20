#!/usr/bin/env python3
import os
import sys
import time
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("/mnt/c/Users/Aftab/Desktop/atlasmirror")
LOGOSCORE_BIN = REPO_ROOT / "logos" / "bin" / "logoscore"
MODULES_DIR = REPO_ROOT / "modules"
HENAN_PBF = Path("/mnt/c/Users/Aftab/Desktop/atlasmirror/test_data/henan-latest.osm.pbf")

NODE1_DATA = Path("/tmp/node1-data")
NODE2_DATA = Path("/tmp/node2-data")
NODE1_CFG_DIR = Path("/tmp/node1-logoscore")
NODE2_CFG_DIR = Path("/tmp/node2-logoscore")

CID = "zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny"
EXPECTED_SIZE = 49157919
EXPECTED_MD5 = "0055ebfc7f14585c56d53a88062d5814"

def run_cmd(cmd, check=True):
    print(f"\n[RUNNING] {cmd}", flush=True)
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(res.stdout, flush=True)
    if res.stderr:
        print("[STDERR]", res.stderr, file=sys.stderr, flush=True)
    if check and res.returncode != 0:
        print(f"[ERROR] Command failed with code {res.returncode}", flush=True)
        sys.exit(res.returncode)
    return res

def cleanup():
    run_cmd("killall -9 logoscore 2>/dev/null || true", check=False)
    time.sleep(2)

def main():
    print("=== TESTING TWO-NODE P2P TRANSFER ON LOGOS.TEST ===")
    cleanup()

    # Prepare directories
    run_cmd(f"rm -rf {NODE1_DATA} {NODE2_DATA} {NODE1_CFG_DIR} {NODE2_CFG_DIR}")
    NODE1_DATA.mkdir(parents=True)
    NODE2_DATA.mkdir(parents=True)
    NODE1_CFG_DIR.mkdir(parents=True)
    NODE2_CFG_DIR.mkdir(parents=True)

    # 1. Configure and start Node 1
    cfg1 = NODE1_DATA / "config.json"
    cfg1.write_text(json.dumps({
        "data-dir": str(NODE1_DATA),
        "log-level": "DEBUG",
        "log-file": str(NODE1_DATA / "storage.log"),
        "network": "logos.test",
        "listen-port": 8071,
        "nat": "auto"
    }))

    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > /tmp/logoscore-node1.log 2>&1 &")
    time.sleep(2)
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} load-module storage_module")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} call storage_module init @{cfg1} --json")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} call storage_module start --json")
    time.sleep(3)

    p1 = run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} call storage_module peerId --json")
    spr1 = run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} call storage_module spr --json")
    debug1 = run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} call storage_module debug --json")
    print("Node 1 Peer:", p1.stdout)
    print("Node 1 SPR:", spr1.stdout)

    # Upload Henan to Node 1
    upload_event = NODE1_DATA / "upload-event.json"
    upload_event.touch()
    w1 = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} watch storage_module --event storageUploadDone --json > {upload_event} 2>&1",
        shell=True
    )
    time.sleep(1)
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE1_CFG_DIR} && {LOGOSCORE_BIN} call storage_module uploadUrl '{HENAN_PBF}' 262144 --json")
    time.sleep(5)
    w1.kill()

    # 2. Configure and start Node 2 with Node 1 as bootstrap peer (or connected)
    cfg2 = NODE2_DATA / "config.json"
    cfg2.write_text(json.dumps({
        "data-dir": str(NODE2_DATA),
        "log-level": "DEBUG",
        "log-file": str(NODE2_DATA / "storage.log"),
        "network": "logos.test",
        "listen-port": 8072,
        "nat": "auto"
    }))

    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > /tmp/logoscore-node2.log 2>&1 &")
    time.sleep(2)
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} load-module storage_module")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} call storage_module init @{cfg2} --json")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} call storage_module start --json")
    time.sleep(3)

    # Connect Node 2 directly to Node 1
    try:
        p1_id = json.loads(p1.stdout)["result"]["value"]
        d1_json = json.loads(debug1.stdout)
        addrs1 = d1_json.get("result", {}).get("value", {}).get("addrs", [])
        print(f"Connecting Node 2 to Node 1 ({p1_id}) at {addrs1}...")
        addrs_arg = json.dumps(addrs1)
        run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} call storage_module connect '{p1_id}' '{addrs_arg}' --json", check=False)
    except Exception as e:
        print("Failed to parse Node 1 debug info:", e)

    # Try downloadManifest on Node 2
    dl_manifest_event = NODE2_DATA / "dl-manifest-event.json"
    dl_manifest_event.touch()
    w_m = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadManifestDone --json > {dl_manifest_event} 2>&1",
        shell=True
    )
    time.sleep(1)

    print(f"Calling downloadManifest on Node 2...")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} call storage_module downloadManifest '{CID}' --json")
    time.sleep(10)
    w_m.kill()
    print("Manifest event:", dl_manifest_event.read_text())

    # Try downloadToUrl on Node 2
    dest = Path("/tmp/henan_node2_p2p.osm.pbf")
    if dest.exists():
        dest.unlink()

    dl_event = NODE2_DATA / "dl-event.json"
    dl_event.touch()
    w_dl = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadDone --json > {dl_event} 2>&1",
        shell=True
    )
    time.sleep(1)

    print(f"Calling downloadToUrl on Node 2 (local=false)...")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={NODE2_CFG_DIR} && {LOGOSCORE_BIN} call storage_module downloadToUrl '{CID}' '{dest}' false 262144 --json", check=False)

    for _ in range(60):
        if dl_event.stat().st_size > 0 and "storageDownloadDone" in dl_event.read_text():
            print("Download finished!")
            break
        time.sleep(1)
    w_dl.kill()

    if dest.exists():
        size = dest.stat().st_size
        md5 = hashlib.md5(dest.read_bytes()).hexdigest()
        print(f"Node 2 Retrieved Size: {size}")
        print(f"Node 2 Retrieved MD5:  {md5}")
        if size == EXPECTED_SIZE and md5 == EXPECTED_MD5:
            print("✅ P2P NETWORK RETRIEVAL SUCCEEDED!")
        else:
            print("❌ Mismatch on retrieved file!")
    else:
        print("❌ Destination file not created!")

if __name__ == "__main__":
    main()
