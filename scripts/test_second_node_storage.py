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

CID = "zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny"
EXPECTED_SIZE = 49157919
EXPECTED_MD5 = "0055ebfc7f14585c56d53a88062d5814"
EXPECTED_SHA256 = "4522a8a6f8ff1e25a269e760f12cc97dff804f288cb449319b3c2065d1d53c46"

NODE2_DATA_DIR = Path("/tmp/storage-node2-data")
NODE2_DEST_FILE = Path("/tmp/henan_node2_retrieved.osm.pbf")
EVIDENCE_FILE = REPO_ROOT / "evidence" / "henan-storage-second-node.log"

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

def main():
    print("=== PROVING STORAGE NETWORK RETRIEVABILITY WITH FRESH SECOND NODE ===", flush=True)
    
    # 1. Clean up any existing logoscore instances
    run_cmd(f"{LOGOSCORE_BIN} call storage_module stop >/dev/null 2>&1 || true", check=False)
    run_cmd(f"{LOGOSCORE_BIN} call storage_module destroy >/dev/null 2>&1 || true", check=False)
    run_cmd(f"{LOGOSCORE_BIN} stop >/dev/null 2>&1 || true", check=False)
    run_cmd("killall -9 logoscore 2>/dev/null || true", check=False)
    time.sleep(2)

    # 2. Prepare completely fresh, empty data-dir
    run_cmd(f"rm -rf {NODE2_DATA_DIR} && mkdir -p {NODE2_DATA_DIR}")
    if NODE2_DEST_FILE.exists():
        NODE2_DEST_FILE.unlink()

    # 3. Configure fresh node with official logos.test network
    config_file = NODE2_DATA_DIR / "config.json"
    config_file.write_text(json.dumps({
        "data-dir": str(NODE2_DATA_DIR),
        "log-level": "DEBUG",
        "log-file": str(NODE2_DATA_DIR / "storage.log"),
        "network": "logos.test",
        "nat": "auto"
    }))

    # 4. Start logoscore daemon on node 2
    daemon_cmd = f"{LOGOSCORE_BIN} -D -m {MODULES_DIR} > /tmp/logoscore-node2.log 2>&1 &"
    run_cmd(daemon_cmd)
    time.sleep(2)

    # Wait for ready
    for _ in range(15):
        res = run_cmd(f"{LOGOSCORE_BIN} status", check=False)
        if res.returncode == 0:
            break
        time.sleep(1)

    # Load and init module
    run_cmd(f"{LOGOSCORE_BIN} load-module storage_module")
    run_cmd(f"{LOGOSCORE_BIN} call storage_module init @{config_file} --json")
    run_cmd(f"{LOGOSCORE_BIN} call storage_module start --json")
    time.sleep(3)

    # Check peer info
    peer_info = run_cmd(f"{LOGOSCORE_BIN} call storage_module peerId --json", check=False)
    print("Node 2 Peer ID:", peer_info.stdout)

    # 5. Set up download watcher
    download_event_file = NODE2_DATA_DIR / "download-event.json"
    download_event_file.touch()

    watcher = subprocess.Popen(
        f"{LOGOSCORE_BIN} watch storage_module --event storageDownloadDone --json > {download_event_file} 2>&1",
        shell=True
    )
    time.sleep(1)

    # 6. Call downloadToUrl with local=false (fetch from network)
    print(f"Calling downloadToUrl for CID {CID} with local=false (network fetch)...", flush=True)
    dl_call = run_cmd(
        f"{LOGOSCORE_BIN} call storage_module downloadToUrl '{CID}' '{NODE2_DEST_FILE}' false 262144 --json"
    )

    # Wait for completion
    download_done = False
    for i in range(90):
        if download_event_file.stat().st_size > 0:
            content = download_event_file.read_text()
            if "storageDownloadDone" in content:
                print(f"storageDownloadDone event observed after {i}s:\n{content}", flush=True)
                download_done = True
                break
        time.sleep(1)

    watcher.kill()

    if not download_done or not NODE2_DEST_FILE.exists():
        print(f"[FAIL] Download from network failed or timed out. Event file content: {download_event_file.read_text()}", flush=True)
        sys.exit(1)

    # 7. Compute hashes of retrieved file
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    size = 0
    with open(NODE2_DEST_FILE, "rb") as f:
        while chunk := f.read(1024 * 1024):
            md5.update(chunk)
            sha256.update(chunk)
            size += len(chunk)
    ret_md5 = md5.hexdigest()
    ret_sha256 = sha256.hexdigest()

    print(f"Retrieved Size:   {size} (Expected: {EXPECTED_SIZE})", flush=True)
    print(f"Retrieved MD5:    {ret_md5} (Expected: {EXPECTED_MD5})", flush=True)
    print(f"Retrieved SHA256: {ret_sha256} (Expected: {EXPECTED_SHA256})", flush=True)

    assert size == EXPECTED_SIZE, f"Size mismatch! Got {size}, expected {EXPECTED_SIZE}"
    assert ret_md5 == EXPECTED_MD5, f"MD5 mismatch! Got {ret_md5}, expected {EXPECTED_MD5}"
    assert ret_sha256 == EXPECTED_SHA256, f"SHA256 mismatch! Got {ret_sha256}, expected {EXPECTED_SHA256}"
    print("✅ 100% BYTE-FOR-BYTE EQUALITY ON FRESH SECOND NODE CONFIRMED!", flush=True)

    evidence_log = (
        f"================================================================================\n"
        f"LOGOS STORAGE SECOND NODE NETWORK RETRIEVABILITY EVIDENCE\n"
        f"================================================================================\n"
        f"Node Configuration: Fresh second node with separate data-dir ({NODE2_DATA_DIR})\n"
        f"Network:            logos.test\n"
        f"Local Cache:        NONE (empty fresh directory, no local manifests)\n"
        f"Target CID:         {CID}\n"
        f"Download Call:      downloadToUrl(local=false)\n"
        f"Download Result:    SUCCESS\n"
        f"Retrieved Size:     {size} bytes (exact match: {EXPECTED_SIZE})\n"
        f"Retrieved MD5:      {ret_md5} (exact match: {EXPECTED_MD5})\n"
        f"Retrieved SHA256:   {ret_sha256} (exact match: {EXPECTED_SHA256})\n"
        f"Integrity Proof:    EXACT 100% BYTE-FOR-BYTE EQUALITY CONFIRMED\n"
        f"Timestamp:          {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}\n"
        f"================================================================================\n"
    )
    EVIDENCE_FILE.write_text(evidence_log)
    print(f"Saved evidence to {EVIDENCE_FILE}", flush=True)

    # Clean up
    run_cmd(f"{LOGOSCORE_BIN} call storage_module stop >/dev/null 2>&1 || true", check=False)
    run_cmd(f"{LOGOSCORE_BIN} call storage_module destroy >/dev/null 2>&1 || true", check=False)
    run_cmd(f"{LOGOSCORE_BIN} stop >/dev/null 2>&1 || true", check=False)

if __name__ == "__main__":
    main()
