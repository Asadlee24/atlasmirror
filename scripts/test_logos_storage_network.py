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
HENAN_PBF = Path("/tmp/henan_e2e/henan-latest.osm.pbf")

NODE1_DIR = Path("/tmp/storage-node1-network")
NODE2_DIR = Path("/tmp/storage-node2-network")

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
    run_cmd(f"{LOGOSCORE_BIN} call storage_module stop >/dev/null 2>&1 || true", check=False)
    run_cmd(f"{LOGOSCORE_BIN} call storage_module destroy >/dev/null 2>&1 || true", check=False)
    run_cmd(f"{LOGOSCORE_BIN} stop >/dev/null 2>&1 || true", check=False)
    run_cmd("killall -9 logoscore 2>/dev/null || true", check=False)
    time.sleep(2)

def start_node(data_dir, log_file, port=0):
    cleanup()
    data_dir.mkdir(parents=True, exist_ok=True)
    cfg = {
        "data-dir": str(data_dir),
        "log-level": "DEBUG",
        "log-file": str(log_file),
        "network": "logos.test",
        "nat": "auto"
    }
    if port != 0:
        cfg["listen-port"] = port
    cfg_path = data_dir / "config.json"
    cfg_path.write_text(json.dumps(cfg))

    run_cmd(f"{LOGOSCORE_BIN} -D -m {MODULES_DIR} > /tmp/logoscore-debug.log 2>&1 &")
    time.sleep(2)
    for _ in range(15):
        if run_cmd(f"{LOGOSCORE_BIN} status", check=False).returncode == 0:
            break
        time.sleep(1)

    run_cmd(f"{LOGOSCORE_BIN} load-module storage_module")
    run_cmd(f"{LOGOSCORE_BIN} call storage_module init @{cfg_path} --json")
    run_cmd(f"{LOGOSCORE_BIN} call storage_module start --json")
    time.sleep(3)
    peer = run_cmd(f"{LOGOSCORE_BIN} call storage_module peerId --json", check=False)
    print("Node Peer ID:", peer.stdout)
    return cfg_path

def main():
    print("=== TESTING STORAGE ON LOGOS.TEST ===")
    HENAN_PBF.parent.mkdir(parents=True, exist_ok=True)
    if not HENAN_PBF.exists() or HENAN_PBF.stat().st_size != 49157919:
        print(f"Downloading Henan PBF from Geofabrik...")
        import urllib.request
        urllib.request.urlretrieve("https://download.geofabrik.de/asia/china/henan-latest.osm.pbf", HENAN_PBF)
        print("Download complete.")
    
    # Verify MD5
    md5 = hashlib.md5(HENAN_PBF.read_bytes()).hexdigest()
    print(f"Henan PBF MD5: {md5} (size: {HENAN_PBF.stat().st_size})")
    assert md5 == "0055ebfc7f14585c56d53a88062d5814", f"MD5 mismatch! Got {md5}"

    # 1. Start Node 1 on logos.test
    print("\n--- Starting Node 1 on logos.test ---")
    run_cmd(f"rm -rf {NODE1_DIR}")
    start_node(NODE1_DIR, NODE1_DIR / "storage.log")

    # 2. Upload Henan PBF
    upload_event = NODE1_DIR / "upload-event.json"
    upload_event.touch()
    watcher = subprocess.Popen(
        f"{LOGOSCORE_BIN} watch storage_module --event storageUploadDone --json > {upload_event} 2>&1",
        shell=True
    )
    time.sleep(1)

    print("Uploading Henan to logos.test...")
    upload_res = run_cmd(f"{LOGOSCORE_BIN} call storage_module uploadUrl '{HENAN_PBF}' 262144 --json")

    cid = None
    for i in range(120):
        if upload_event.stat().st_size > 0:
            content = upload_event.read_text()
            for line in content.splitlines():
                try:
                    ev = json.loads(line)
                    arg0 = json.loads(ev.get("data", {}).get("arg0", "{}"))
                    if "cid" in arg0:
                        cid = arg0["cid"]
                        break
                except Exception:
                    pass
            if cid:
                print(f"Uploaded CID: {cid} after {i}s")
                break
        time.sleep(1)
    watcher.kill()

    assert cid, "Upload failed to produce CID!"
    print(f"Verified Uploaded CID: {cid}")

    # Give DHT / network time to announce
    print("Waiting 15 seconds for DHT announcements...")
    time.sleep(15)

    # User requirement:
    # "Stop/destroy the original Storage node after upload."
    print("\n--- Stopping and destroying Node 1 (as requested by user) ---")
    cleanup()

    # Now Start completely fresh Node 2
    print("\n--- Starting completely fresh Node 2 on logos.test ---")
    run_cmd(f"rm -rf {NODE2_DIR}")
    start_node(NODE2_DIR, NODE2_DIR / "storage.log")

    # Step A: downloadManifest
    dl_manifest_event = NODE2_DIR / "dl-manifest-event.json"
    dl_manifest_event.touch()
    watcher_m = subprocess.Popen(
        f"{LOGOSCORE_BIN} watch storage_module --event storageDownloadManifestDone --json > {dl_manifest_event} 2>&1",
        shell=True
    )
    time.sleep(1)

    print(f"Calling downloadManifest for {cid} on fresh Node 2...")
    dm_res = run_cmd(f"{LOGOSCORE_BIN} call storage_module downloadManifest '{cid}' --json")
    print("downloadManifest response:", dm_res.stdout)

    manifest_found = False
    for i in range(45):
        if dl_manifest_event.stat().st_size > 0:
            content = dl_manifest_event.read_text()
            if "storageDownloadManifestDone" in content:
                print(f"storageDownloadManifestDone event after {i}s:\n{content}")
                manifest_found = True
                break
        time.sleep(1)
    watcher_m.kill()

    # Step B: downloadToUrl
    dest_file = Path("/tmp/henan_downloaded_from_network.osm.pbf")
    if dest_file.exists():
        dest_file.unlink()

    dl_event = NODE2_DIR / "dl-event.json"
    dl_event.touch()
    watcher_dl = subprocess.Popen(
        f"{LOGOSCORE_BIN} watch storage_module --event storageDownloadDone --json > {dl_event} 2>&1",
        shell=True
    )
    time.sleep(1)

    print(f"Calling downloadToUrl for {cid} with local=false on fresh Node 2...")
    dl_res = run_cmd(f"{LOGOSCORE_BIN} call storage_module downloadToUrl '{cid}' '{dest_file}' false 262144 --json", check=False)
    print("downloadToUrl response:", dl_res.stdout)

    for i in range(60):
        if dl_event.stat().st_size > 0:
            content = dl_event.read_text()
            if "storageDownloadDone" in content:
                print(f"storageDownloadDone event after {i}s:\n{content}")
                break
        time.sleep(1)
    watcher_dl.kill()

    if dest_file.exists():
        print(f"SUCCESS: Downloaded file size = {dest_file.stat().st_size}")
    else:
        print("FAILED: File was not retrieved on Node 2 after Node 1 was stopped!")

if __name__ == "__main__":
    main()
