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
TEST_NODES_DIR = REPO_ROOT / "test_nodes"

HENAN_PBF = REPO_ROOT / "test_data" / "henan-latest.osm.pbf"
CID = "zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny"
EXPECTED_SIZE = 49157919
EXPECTED_MD5 = "0055ebfc7f14585c56d53a88062d5814"

N1_CFG = TEST_NODES_DIR / "n1_cfg"
N1_DATA = TEST_NODES_DIR / "n1_data"
N2_CFG = TEST_NODES_DIR / "n2_cfg"
N2_DATA = TEST_NODES_DIR / "n2_data"

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
    time.sleep(1)

def main():
    print("=== INVESTIGATING P2P REACHABILITY & REPLICATION ===")
    cleanup()
    run_cmd(f"rm -rf {TEST_NODES_DIR} && mkdir -p {N1_CFG} {N1_DATA} {N2_CFG} {N2_DATA}")

    # 1. Start Node 1 on port 8071 with extip:127.0.0.1
    c1 = {
        "data-dir": str(N1_DATA),
        "log-level": "DEBUG",
        "log-file": str(N1_DATA / "storage.log"),
        "listen-ip": "0.0.0.0",
        "listen-port": 8071,
        "nat": "extip:127.0.0.1"
    }
    (N1_DATA / "config.json").write_text(json.dumps(c1))

    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > {N1_DATA}/daemon.log 2>&1 &")
    time.sleep(2)
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} load-module storage_module")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} call storage_module init @{N1_DATA / 'config.json'} --json")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} call storage_module start --json")
    time.sleep(2)

    p1_res = run_cmd(f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} call storage_module peerId --json")
    p1 = json.loads(p1_res.stdout)["result"]["value"]
    spr1_res = run_cmd(f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} call storage_module spr --json")
    spr1 = json.loads(spr1_res.stdout)["result"]["value"]
    debug1_res = run_cmd(f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} call storage_module debug --json")
    print("Node 1 Peer:", p1)
    print("Node 1 SPR:", spr1)
    print("Node 1 Debug:", debug1_res.stdout)

    # Upload Henan to Node 1
    upload_event = N1_DATA / "upload-event.json"
    upload_event.touch()
    w_up = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} watch storage_module --event storageUploadDone --json > {upload_event} 2>&1",
        shell=True
    )
    time.sleep(1)
    print(f"Uploading {HENAN_PBF} to Node 1...")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N1_CFG} && {LOGOSCORE_BIN} call storage_module uploadUrl '{HENAN_PBF}' 262144 --json")

    uploaded_cid = None
    for _ in range(60):
        if upload_event.stat().st_size > 0:
            content = upload_event.read_text()
            for line in content.splitlines():
                try:
                    ev = json.loads(line)
                    arg0 = json.loads(ev.get("data", {}).get("arg0", "{}"))
                    if "cid" in arg0:
                        uploaded_cid = arg0["cid"]
                        break
                except Exception:
                    pass
            if uploaded_cid:
                break
        time.sleep(1)
    w_up.kill()
    print(f"Node 1 Uploaded CID: {uploaded_cid}")
    assert uploaded_cid == CID, f"CID mismatch! {uploaded_cid} != {CID}"

    # 2. Start Node 2 on port 8072 with Node 1's SPR as bootstrap-node!
    c2 = {
        "data-dir": str(N2_DATA),
        "log-level": "DEBUG",
        "log-file": str(N2_DATA / "storage.log"),
        "listen-ip": "0.0.0.0",
        "listen-port": 8072,
        "nat": "extip:127.0.0.1",
        "bootstrap-node": [spr1]
    }
    (N2_DATA / "config.json").write_text(json.dumps(c2))

    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > {N2_DATA}/daemon.log 2>&1 &")
    time.sleep(2)
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} load-module storage_module")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} call storage_module init @{N2_DATA / 'config.json'} --json")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} call storage_module start --json")
    time.sleep(3)

    debug2_res = run_cmd(f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} call storage_module debug --json")
    print("Node 2 Debug (showing routing table):", debug2_res.stdout)

    # 3. Test downloadManifest on Node 2
    dl_manifest_event = N2_DATA / "dl-manifest-event.json"
    dl_manifest_event.touch()
    w_m = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadManifestDone --json > {dl_manifest_event} 2>&1",
        shell=True
    )
    time.sleep(1)

    print(f"Calling downloadManifest on Node 2 for {CID}...")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} call storage_module downloadManifest '{CID}' --json")

    manifest_ok = False
    for i in range(30):
        if dl_manifest_event.stat().st_size > 0:
            content = dl_manifest_event.read_text()
            if "storageDownloadManifestDone" in content:
                print(f"storageDownloadManifestDone received on Node 2 after {i}s:\n{content}")
                manifest_ok = True
                break
        time.sleep(1)
    w_m.kill()

    # 4. Test downloadToUrl on Node 2
    dest = TEST_NODES_DIR / "retrieved_node2.osm.pbf"
    if dest.exists():
        dest.unlink()

    dl_event = N2_DATA / "dl-event.json"
    dl_event.touch()
    w_dl = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadDone --json > {dl_event} 2>&1",
        shell=True
    )
    time.sleep(1)

    print(f"Calling downloadToUrl on Node 2 for {CID} (local=false)...")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={N2_CFG} && {LOGOSCORE_BIN} call storage_module downloadToUrl '{CID}' '{dest}' false 262144 --json")

    download_ok = False
    for i in range(60):
        if dl_event.stat().st_size > 0:
            content = dl_event.read_text()
            if "storageDownloadDone" in content:
                print(f"storageDownloadDone received on Node 2 after {i}s:\n{content}")
                download_ok = True
                break
        time.sleep(1)
    w_dl.kill()

    if dest.exists():
        size = dest.stat().st_size
        md5 = hashlib.md5(dest.read_bytes()).hexdigest()
        print(f"SUCCESS! Retrieved Size: {size}, MD5: {md5}")
    else:
        print("FAILED: File was not retrieved on Node 2.")

if __name__ == "__main__":
    main()
