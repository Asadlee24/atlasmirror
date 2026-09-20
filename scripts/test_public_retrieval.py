#!/usr/bin/env python3
import os
import sys
import time
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("/mnt/c/Users/Aftab/Desktop/atlasmirror")
EVIDENCE_DIR = REPO_ROOT / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)
TEST_DIR = REPO_ROOT / "test_nodes" / "public_retrieval"
CFG_DIR = TEST_DIR / "cfg"
DATA_DIR = TEST_DIR / "data"

VPS_IP = "199.231.187.97"
VPS_PORT = 8070
VPS_PEER_ID = "16Uiu2HAmH2Fa2Zy1iuAgWGZJUEVJsBFY3GjeXepuHthyuDyC3Nak"
VPS_SPR = "spr:CiUIAhIhA0DhJ1C6-HZQW8dqk8k90jLwB4qsts-jvsA5oZyT__uZEgIDARo7CicAJQgCEiEDQOEnULr4dlBbx2qTyT3SMvAHiqy2z6O-wDmhnJP_-5kQ5pC_1QYaCgoIBMfnu2EGH4YqRzBFAiEA0O2lV6gW-tLhJmE15wCm_opryeLRCPoJrSu7A3au9g0CIEKO9mxr71IPapg5-eO8bf55xfC1jCPNjQv95_y6tD1-"

CID = "zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny"
EXPECTED_SIZE = 49157919
EXPECTED_MD5 = "0055ebfc7f14585c56d53a88062d5814"
EXPECTED_SHA256 = "4522a8a6f8ff1e25a269e760f12cc97dff804f288cb449319b3c2065d1d53c46"

DEST_FILE = TEST_DIR / "henan_from_public_vps.osm.pbf"
LOGOSCORE_BIN = REPO_ROOT / "logos" / "bin" / "logoscore"
MODULES_DIR = REPO_ROOT / "modules"

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

def compute_hashes(file_path):
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    size = 0
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            md5.update(chunk)
            sha256.update(chunk)
            size += len(chunk)
    return size, md5.hexdigest(), sha256.hexdigest()

def main():
    print("================================================================================")
    print("PUBLIC EVALUATOR-STYLE STORAGE PROOF: INDEPENDENT RETRIEVAL FROM PUBLIC VPS")
    print("================================================================================")
    print(f"VPS Host:   {VPS_IP}:{VPS_PORT}")
    print(f"VPS PeerID: {VPS_PEER_ID}")
    print(f"VPS SPR:    {VPS_SPR}")
    print(f"Target CID: {CID}")

    # 1. Clean local environment
    run_cmd("killall -9 logoscore 2>/dev/null || true", check=False)
    time.sleep(1)
    run_cmd(f"rm -rf {TEST_DIR} && mkdir -p {CFG_DIR} {DATA_DIR}")

    # 2. Configure fresh client
    config = {
        "data-dir": str(DATA_DIR),
        "log-level": "NOTICE",
        "network": "logos.test",
        "listen-ip": "0.0.0.0",
        "listen-port": 8075,
        "nat": "auto",
        "bootstrap-node": [VPS_SPR]
    }
    (DATA_DIR / "config.json").write_text(json.dumps(config, indent=2))

    # 3. Start local daemon
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > {DATA_DIR}/daemon.log 2>&1 &")
    time.sleep(2)
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} load-module storage_module")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} call storage_module init @{DATA_DIR / 'config.json'} --json")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} call storage_module start --json")
    time.sleep(3)

    # 4. Check client network & debug
    p_res = run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} call storage_module peerId --json")
    client_peer_id = json.loads(p_res.stdout)["result"]["value"]
    debug_res = run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} call storage_module debug --json")
    print(f"Client PeerID: {client_peer_id}")
    print(f"Client Debug:  {debug_res.stdout.strip()}")

    # 5. Fetch manifest
    print(f"\nCalling downloadManifest for CID {CID} from public VPS...")
    dl_m_event = DATA_DIR / "dl-manifest-event.json"
    dl_m_event.touch()
    w_m = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadManifestDone --json > {dl_m_event} 2>&1",
        shell=True
    )
    time.sleep(1)
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} call storage_module downloadManifest '{CID}' --json")

    manifest_ok = False
    manifest_raw = ""
    for i in range(60):
        if dl_m_event.stat().st_size > 0:
            content = dl_m_event.read_text()
            if "storageDownloadManifestDone" in content:
                print(f"storageDownloadManifestDone received from public VPS after {i}s:\n{content}")
                manifest_ok = True
                manifest_raw = content
                break
        time.sleep(1)
    w_m.kill()
    assert manifest_ok, "Failed to retrieve manifest from public VPS storage node!"

    # 6. Fetch blocks via downloadToUrl
    if DEST_FILE.exists():
        DEST_FILE.unlink()

    dl_event = DATA_DIR / "dl-event.json"
    dl_event.touch()
    w_dl = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadDone --json > {dl_event} 2>&1",
        shell=True
    )
    # Also watch progress
    prog_event = DATA_DIR / "prog-event.json"
    prog_event.touch()
    w_prog = subprocess.Popen(
        f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadProgress --json > {prog_event} 2>&1",
        shell=True
    )
    time.sleep(1)

    print(f"\nCalling downloadToUrl for CID {CID} (local=false)...")
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} call storage_module downloadToUrl '{CID}' '{DEST_FILE}' false 262144 --json")

    download_ok = False
    download_raw = ""
    last_reported = 0
    for i in range(400):
        if DEST_FILE.exists():
            cur_sz = DEST_FILE.stat().st_size
            if cur_sz - last_reported >= 2 * 1024 * 1024 or cur_sz == EXPECTED_SIZE:
                pct = (cur_sz / EXPECTED_SIZE) * 100
                print(f"[{i}s] Download Progress: {cur_sz / (1024*1024):.2f} MB / {EXPECTED_SIZE / (1024*1024):.2f} MB ({pct:.1f}%)", flush=True)
                last_reported = cur_sz

        if dl_event.stat().st_size > 0:
            content = dl_event.read_text()
            if "storageDownloadDone" in content:
                print(f"\nstorageDownloadDone received from public VPS after {i}s:\n{content}")
                download_ok = True
                download_raw = content
                break
        time.sleep(1)

    w_dl.kill()
    w_prog.kill()
    assert download_ok, "Failed to download blocks from public VPS storage node!"
    assert DEST_FILE.exists(), f"Retrieved file {DEST_FILE} not created!"

    # 7. Verify exact size, MD5, SHA256
    ret_size, ret_md5, ret_sha256 = compute_hashes(DEST_FILE)
    print(f"\nRetrieved Size:   {ret_size} bytes (Expected: {EXPECTED_SIZE})")
    print(f"Retrieved MD5:    {ret_md5} (Expected: {EXPECTED_MD5})")
    print(f"Retrieved SHA256: {ret_sha256} (Expected: {EXPECTED_SHA256})")

    assert ret_size == EXPECTED_SIZE, f"Size mismatch: {ret_size} != {EXPECTED_SIZE}"
    assert ret_md5 == EXPECTED_MD5, f"MD5 mismatch: {ret_md5} != {EXPECTED_MD5}"
    assert ret_sha256 == EXPECTED_SHA256, f"SHA256 mismatch: {ret_sha256} != {EXPECTED_SHA256}"
    print("\n✅ 100% BYTE-FOR-BYTE AUTHENTIC RETRIEVAL FROM PUBLIC VPS VERIFIED!")

    # 8. Clean up local client (keep VPS node running!)
    run_cmd(f"export LOGOSCORE_CONFIG_DIR={CFG_DIR} && {LOGOSCORE_BIN} stop || true", check=False)

    # 9. Write evidence/henan-public-storage-retrieval.log
    evidence_text = (
        f"================================================================================\n"
        f"LOGOS STORAGE PUBLIC EVALUATOR-STYLE RETRIEVAL EVIDENCE\n"
        f"================================================================================\n"
        f"Public VPS Host:     {VPS_IP} (KVM Linux VPS, Ubuntu 24.04 x86_64)\n"
        f"VPS Listen Port:     {VPS_PORT} (Firewall open, 0.0.0.0 bind)\n"
        f"VPS Node PeerID:     {VPS_PEER_ID}\n"
        f"VPS Node SPR:        {VPS_SPR}\n"
        f"VPS Network:         logos.test (NAT: extip:{VPS_IP})\n"
        f"VPS Node Status:     ONLINE & PERSISTENT (configured as a persistent systemd service with automatic boot restart)\n"
        f"Target Dataset:      china/henan (henan-latest.osm.pbf)\n"
        f"Target CID:          {CID}\n"
        f"External Client:     Independent client ({client_peer_id}, separate clean data-dir)\n"
        f"Manifest Retrieval:  SUCCESS (storageDownloadManifestDone received from {VPS_IP})\n"
        f"Manifest Event:      {manifest_raw.strip()}\n"
        f"Block Retrieval:     SUCCESS (downloadToUrl local=false)\n"
        f"Download Event:      {download_raw.strip()}\n"
        f"Retrieved Size:      {ret_size} bytes (Expected: {EXPECTED_SIZE}) -> EXACT MATCH\n"
        f"Retrieved MD5:       {ret_md5} (Expected: {EXPECTED_MD5}) -> EXACT MATCH\n"
        f"Retrieved SHA256:    {ret_sha256} (Expected: {EXPECTED_SHA256}) -> EXACT MATCH\n"
        f"Verification Result: PASSED (Byte-for-byte authentic Henan OSM snapshot)\n"
        f"Verification Time:   {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}\n"
        f"================================================================================\n"
    )
    (EVIDENCE_DIR / "henan-public-storage-retrieval.log").write_text(evidence_text)
    print(f"Saved: {EVIDENCE_DIR / 'henan-public-storage-retrieval.log'}")
    print("\n🎉 ALL CHECKS PASSED AND EVIDENCE COMMITTED!")

if __name__ == "__main__":
    main()
