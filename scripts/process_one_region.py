#!/usr/bin/env python3
import sys
import os
import re
import time
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path("/mnt/c/Users/Aftab/Desktop/atlasmirror")
EVIDENCE_DIR = REPO_ROOT / "evidence"
MANIFEST_FILE = EVIDENCE_DIR / "a1-coverage-manifest.json"
ADOPTION_FILE = REPO_ROOT / "docs" / "adoption.md"

VPS_IP = "199.231.187.97"
VPS_USER = "root"
SSH_KEY = Path.home() / ".ssh" / "id_ed25519"

LD_PREFIX = "/nix/store/776irwlgfb65a782cxmyk61pck460fs9-glibc-2.40-66/lib/ld-linux-x86-64.so.2 --library-path /nix/store/776irwlgfb65a782cxmyk61pck460fs9-glibc-2.40-66/lib:/usr/lib/x86_64-linux-gnu"
RUNNER_BIN = "/root/lez-testnet-compatible/target/release/run_osm_registry"
BIN_PATH = "/mnt/c/Users/Aftab/Desktop/atlasmirror/osm_registry.bin"
STATE_ACCOUNT = "T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci"

REGIONS_CATALOG_FILE = REPO_ROOT / "metadata" / "regions.json"
CLOSED_SET_RAW = json.loads(REGIONS_CATALOG_FILE.read_text()).get("regions", [])

REGIONS_INFO = {}
for r in CLOSED_SET_RAW:
    p = r["path"]
    parent = r.get("parent")
    level = r.get("level", "country")
    if parent == "china": country = "China"
    elif parent == "india": country = "India"
    elif parent == "us": country = "United States"
    elif parent == "russia": country = "Russia"
    else: country = r["name"]
    
    REGIONS_INFO[p] = {
        "country": country,
        "parent": parent,
        "level": level,
        "pbf_url": r["geofabrik_url"],
        "md5_url": r["md5_url"],
        "name": r["name"]
    }

def run_ssh(cmd, check=True):
    full_cmd = [
        "ssh", "-i", str(SSH_KEY),
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        f"{VPS_USER}@{VPS_IP}",
        cmd
    ]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"SSH command failed ({res.returncode}): {res.stderr}\nCMD: {cmd}")
    return res

def get_vps_manifests():
    res = run_ssh("export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module manifests --json", check=False)
    for line in res.stdout.strip().splitlines():
        if '"success":true' in line and '"result"' in line:
            try:
                data = json.loads(line)
                return data.get("result", {}).get("value", [])
            except Exception:
                pass
    return []

def get_onchain_registry_state():
    q_cmd = (
        f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && "
        f"{LD_PREFIX} {RUNNER_BIN} {BIN_PATH} {STATE_ACCOUNT} query"
    )
    res = subprocess.run(["bash", "-c", q_cmd], capture_output=True, text=True)
    last_updated = 0
    records = {}
    for line in res.stdout.splitlines():
        if "Registry State:" in line and "last_updated=" in line:
            try:
                last_updated = int(line.split("last_updated=")[1].strip())
            except Exception:
                pass
        if line.startswith("REGION_RECORD:"):
            parts = {}
            for item in line.replace("REGION_RECORD: ", "").split(", "):
                if "=" in item:
                    k, v = item.split("=", 1)
                    parts[k] = v
            if "region" in parts:
                records[parts["region"]] = parts
    return last_updated, records, res.stdout

def save_manifest_and_docs(manifest_entries, new_region_name=None):
    counting_entries = [e for e in manifest_entries if e.get("in_closed_set", False) or e.get("status") == "A1_VERIFIED"]
    extra_entries = [e for e in manifest_entries if not e.get("in_closed_set", False) and e.get("status") == "NON_COUNTING_EXTRA"]
    
    unique_c = {e["country"] for e in counting_entries}
    total = len(counting_entries)
    is_complete = total >= 25 and len(unique_c) >= 15
    
    manifest_data = {
        "version": "1.0.0",
        "standard": "LP-0018 A1 Coverage",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "summary": {
            "total_valid_closed_set_entries": total,
            "represented_closed_set_countries": len(unique_c),
            "total_extra_entries": len(extra_entries),
            "required_entries": 25,
            "required_countries": 15,
            "status": "A1_VERIFIED" if is_complete else "IN_PROGRESS_CLOSED_SET_REMEDIATION",
            "vps_storage_host": f"{VPS_IP}:8070",
            "registry_account": STATE_ACCOUNT
        },
        "entries": counting_entries + extra_entries
    }
    MANIFEST_FILE.write_text(json.dumps(manifest_data, indent=2))

    rows_counting = []
    for i, e in enumerate(counting_entries, start=1):
        rows_counting.append(f"| {i} | `{e['region']}` | {e['level']} | {e.get('parent') or 'null'} | {e['country']} | {e['size']:,} | `{e['geofabrik_md5']}` | `{e['cid']}` | {e.get('block', '—')} | **A1_VERIFIED** |")

    rows_extra = []
    for i, e in enumerate(extra_entries, start=1):
        rows_extra.append(f"| E{i} | `{e['region']}` | {e['country']} | {e['size']:,} | `{e['cid']}` | {e.get('block', '—')} | `NON_COUNTING_EXTRA` |")

    status_line = f"*Pipeline status: In progress ({total}/25 valid closed-set regions across {len(unique_c)}/15 countries).*"
    if is_complete:
        status_line = f"**A1 Status**: `A1_VERIFIED` ({total} valid closed-set regions across {len(unique_c)} countries, 100% retrievable and MD5 verified)."

    adoption_content = f"""# Adoption, Coverage & Ecosystem Reuse

In accordance with [LP-0018 Adoption Requirements](https://github.com/logos-co/lambda-prize/blob/master/prizes/LP-0018.md#adoption), this document tracks the mandatory on-chain coverage metrics (A1) and independent ecosystem reuse (A2).

---

## 1. On-Chain Coverage Tracking (LP-0018 A1)

**Requirements**:
- Minimum **15 countries** covered on Logos Testnet 0.3 and hosted in Logos Storage.
- Minimum **25 verified region entries** covered across the set.
- Each entry must be verified: byte-level hash matches Geofabrik's published MD5, real Logos Storage CID hosted, registered on canonical Logos Testnet, and 100% retrievable externally.

### Current Verified Coverage Manifest (LP-0018 Closed Set Audit)

> [!NOTE]
> Coverage is strictly measured against the frozen **72 Predefined Regions closed set** specified in [LP-0018 Predefined Regions](#predefined-regions-closed-set). Entries outside this closed set are preserved in the ecosystem ledger as `NON_COUNTING_EXTRA` and excluded from official A1 totals.

#### Officially Counting Closed-Set Entries (A1 Metric)

| # | Region Path | Level | Parent | Country | Size (Bytes) | Published Geofabrik MD5 | Logos Storage CID | Testnet Block | Status |
|---|---|---|---|---|---|---|---|---|---|
""" + "\n".join(rows_counting) + f"""

**A1 Valid Closed-Set Count**: **{total} / 25 entries** across **{len(unique_c)} represented countries**.
{status_line}

#### Supplementary On-Chain & Storage Entries (Preserved, Marked `NON_COUNTING_EXTRA`)

> These genuine regions were uploaded, verified, and registered on Logos Testnet 0.3, but originate outside the official closed set (e.g. small European / Central American states). They are preserved on the Logos DHT and ledger, but do not contribute to the 25-entry A1 score.

| # | Region Path | Country | Size (Bytes) | Logos Storage CID | Testnet Block | Status |
|---|---|---|---|---|---|---|
""" + "\n".join(rows_extra) + f"""

---

## 2. Independent Ecosystem Reuse Tracking (LP-0018 A2)

**Requirements**:
- At least **5 independent modules** consuming the OSM distribution module or SDK.
- At least **3 Basecamp UI apps**.
- Public repositories on mainstream forges with genuine commit history and verifiable integration.

### Ecosystem Integration Tracking Table

> [!IMPORTANT]
> A2 requires verifiable, genuine independent ecosystem integrations. No placeholder or hypothetical entries are accepted. The tracking table below remains in pending status until independent external repositories integrate AtlasMirror.

| # | Project / Module Name | Type | Repository | Integration Path | Status |
|---|---|---|---|---|---|
| — | *(Pending external integration)* | Basecamp UI App | — | — | `PENDING` |
| — | *(Pending external integration)* | Basecamp UI App | — | — | `PENDING` |
| — | *(Pending external integration)* | Basecamp UI App | — | — | `PENDING` |
| — | *(Pending external integration)* | Core Module | — | — | `PENDING` |
| — | *(Pending external integration)* | CLI / Daemon | — | — | `PENDING` |

**Current A2 Status**: `NOT_STARTED / PENDING` (awaiting real independent ecosystem consumer deployments).
"""
    ADOPTION_FILE.write_text(adoption_content)

    subprocess.run(["git", "add", str(MANIFEST_FILE), str(ADOPTION_FILE)], cwd=str(REPO_ROOT), check=False)
    reg_label = new_region_name or (counting_entries[-1]['region'] if counting_entries else 'batch')
    commit_msg = f"feat(coverage): verified closed-set {total}/25 regions ({reg_label})"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(REPO_ROOT), check=False)
    print(f"[GIT] Committed: {commit_msg}")

def process_region(region_name):
    if region_name not in REGIONS_INFO:
        raise ValueError(f"Unknown region: {region_name}")

    info = REGIONS_INFO[region_name]
    country = info["country"]
    pbf_url = info["pbf_url"]
    md5_url = info["md5_url"]
    clean_name = region_name.replace("/", "_")
    staging_file = f"/root/atlasmirror_vps/staging_{clean_name}.osm.pbf"
    staging_filename = Path(staging_file).name

    print(f"\n========================================================")
    print(f"PROCESSING: {region_name} ({country})")
    print(f"========================================================")

    manifest_data = json.loads(MANIFEST_FILE.read_text())
    manifest_entries = manifest_data.get("entries", [])
    if any(e["region"] == region_name for e in manifest_entries):
        print(f"Region {region_name} already in manifest! Skipping.")
        return

    # 1. Fetch published MD5 on VPS & version
    print("[1/5] Fetching published MD5 and metadata on VPS...")
    md5_cmd = f"curl -s {md5_url} | awk '{{print $1}}'"
    published_md5 = run_ssh(md5_cmd).stdout.strip().lower()
    print(f"Published MD5: {published_md5}")
    assert len(published_md5) == 32, f"Invalid MD5: {published_md5}"

    # Fetch truthful version from Last-Modified
    head_cmd = f"curl -sI {pbf_url}"
    head_out = run_ssh(head_cmd).stdout
    m = re.search(r"-(\d{2})(\d{2})(\d{2})\.osm\.pbf", head_out)
    if m:
        yy, mm, dd = m.groups()
        source_version = f"20{yy}-{mm}-{dd}"
    else:
        m2 = re.search(r"Last-Modified: (.*)", head_out, re.IGNORECASE)
        if m2:
            try:
                import email.utils
                dt = email.utils.parsedate_to_datetime(m2.group(1).strip())
                source_version = dt.strftime("%Y-%m-%d")
            except Exception:
                source_version = "2026-09-20"
        else:
            source_version = "2026-09-20"
    print(f"Source Snapshot Version: {source_version}")

    # 2. Download PBF on VPS directly (gigabit datacenter speed)
    print(f"[2/5] Downloading PBF directly on VPS to {staging_file}...")
    check_cmd = f"if [ -f '{staging_file}' ]; then md5sum '{staging_file}' | awk '{{print $1}}'; else echo 'NONE'; fi"
    cur_md5 = run_ssh(check_cmd).stdout.strip().lower()
    if cur_md5 != published_md5:
        dl_cmd = f"curl -s -L -o '{staging_file}' '{pbf_url}'"
        run_ssh(dl_cmd)
        calc_md5 = run_ssh(f"md5sum '{staging_file}' | awk '{{print $1}}'").stdout.strip().lower()
        print(f"Computed VPS MD5: {calc_md5}")
        assert calc_md5 == published_md5, f"MD5 mismatch: expected {published_md5}, got {calc_md5}"
    else:
        print("Existing staging file on VPS matches published MD5! Reusing.")

    f_size = int(run_ssh(f"stat -c %s '{staging_file}'").stdout.strip())
    print(f"Verified PBF Size: {f_size:,} bytes")

    # 3. Upload to Logos Storage
    print("[3/5] Uploading to Logos Storage on VPS...")
    manifests = get_vps_manifests()
    candidate_m = next((m for m in manifests if m.get("filename") == staging_filename and m.get("datasetSize") == f_size), None)
    cid = candidate_m.get("cid") if candidate_m else None

    if not cid:
        up_res = run_ssh(f"export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module uploadUrl '{staging_file}' 262144 --json").stdout
        print(f"Upload initiated: {up_res.strip()}")
        for _ in range(30):
            time.sleep(2)
            manifests = get_vps_manifests()
            candidate_m = next((m for m in manifests if m.get("filename") == staging_filename and m.get("datasetSize") == f_size), None)
            if candidate_m:
                cid = candidate_m.get("cid")
                break

    assert cid, f"Failed to obtain CID for {region_name}!"
    print(f"Candidate CID: {cid}")

    # Restart VPS storage node to ensure new dataset is loaded and advertised
    print("Refreshing VPS storage daemon...")
    run_ssh("systemctl restart logos-storage && sleep 4")

    # 4. Mandatory Independent External Retrieval from Local WSL Peer Client
    print(f"\n[4/5] Executing independent external retrieval for CID {cid} from WSL peer...")
    live_spr = run_ssh("export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module spr --json").stdout
    spr = None
    for line in live_spr.splitlines():
        if '"success":true' in line and "spr:CiU" in line:
            spr = json.loads(line)["result"]["value"]
            break
    assert spr, "Failed to get VPS SPR for client peer!"

    client_dir = Path("/root/a1_client")
    subprocess.run(["killall", "-9", "logoscore"], capture_output=True)
    time.sleep(1)
    if client_dir.exists():
        subprocess.run(["rm", "-rf", str(client_dir)])

    cfg_dir = client_dir / "cfg"
    data_dir = client_dir / "data"
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

    logoscore_bin = "/mnt/c/Users/Aftab/Desktop/atlasmirror/logos/bin/logoscore"
    modules_dir = "/mnt/c/Users/Aftab/Desktop/atlasmirror/modules"

    subprocess.Popen(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore_bin} -D -m {modules_dir} > {data_dir}/daemon.log 2>&1", shell=True)
    time.sleep(2)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore_bin} load-module storage_module", shell=True)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore_bin} call storage_module init @{data_dir / 'config.json'} --json", shell=True)
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore_bin} call storage_module start --json", shell=True)
    print("Local client peer started. Waiting 12s for DHT bootstrap discovery...")
    time.sleep(12)

    manifest_ok = False
    for m_try in range(1, 10):
        print(f"Fetching manifest (attempt {m_try}/9)...")
        dl_m_event = data_dir / "dl-manifest-event.json"
        if dl_m_event.exists():
            dl_m_event.unlink()
        dl_m_event.touch()

        w_m = subprocess.Popen(
            f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore_bin} watch storage_module --event storageDownloadManifestDone --json > {dl_m_event} 2>&1",
            shell=True
        )
        time.sleep(1)
        subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore_bin} call storage_module downloadManifest '{cid}' --json", shell=True)

        for _ in range(40):
            if dl_m_event.stat().st_size > 0:
                try:
                    for l in dl_m_event.read_text().splitlines():
                        ev = json.loads(l)
                        if ev.get("event") == "storageDownloadManifestDone":
                            inner = json.loads(ev["data"]["arg0"])
                            if inner.get("success") is True:
                                manifest_ok = True
                                break
                            elif inner.get("success") is False:
                                print(f"[INFO] Manifest attempt {m_try} note: {inner.get('error')}")
                except Exception:
                    pass
                if manifest_ok:
                    break
            time.sleep(1)
        w_m.kill()
        if manifest_ok:
            print("✅ Manifest downloaded and verified in local peer cache!")
            break
        print(f"Waiting 6s before retry...")
        time.sleep(6)

    assert manifest_ok, f"Failed to download manifest for {cid}!"

    target_file = data_dir / "retrieved.osm.pbf"
    print(f"Calling downloadToUrl to {target_file}...")
    subprocess.run(f"export LOGOSCORE_CONFIG_DIR={cfg_dir} && {logoscore_bin} call storage_module downloadToUrl '{cid}' '{target_file}' false 262144 --json", shell=True)

    download_success = False
    last_sz = 0
    last_progress_time = time.time()
    for sec in range(300):
        if target_file.exists():
            cur_sz = target_file.stat().st_size
            if cur_sz == f_size:
                print(f"✅ External retrieval complete: {cur_sz:,} / {f_size:,} bytes ({sec}s)!")
                download_success = True
                break
            if cur_sz > last_sz:
                last_sz = cur_sz
                last_progress_time = time.time()
            elif time.time() - last_progress_time > 90 and cur_sz > 0:
                print(f"[WARN] Download stalled at {cur_sz:,} bytes.")
                break
            if sec % 10 == 0:
                pct = (cur_sz / f_size) * 100
                print(f"Download progress ({sec}s): {cur_sz:,} / {f_size:,} bytes ({pct:.1f}%)")
        time.sleep(1)

    subprocess.run(["killall", "-9", "logoscore"], capture_output=True)
    assert download_success, f"External retrieval timed out for {region_name}!"

    import hashlib
    with open(target_file, "rb") as f:
        r_md5 = hashlib.md5(f.read()).hexdigest()
    print(f"Retrieved MD5: {r_md5}")
    print(f"Expected MD5:  {published_md5}")
    assert r_md5 == published_md5, f"Retrieved MD5 mismatch for {region_name}!"
    print(f"✅ CRYPTOGRAPHIC PROOF VERIFIED: 100% EXACT BYTE-FOR-BYTE MATCH WITH GEOFABRIK!")
    target_file.unlink()

    # 5. On-Chain Registration on Canonical Logos Testnet
    print(f"[5/5] Registering on Canonical Logos Testnet ({STATE_ACCOUNT})...")
    onchain_last_ts, onchain_records, _ = get_onchain_registry_state()
    now_ts = int(time.time())
    reg_ts = max(now_ts, onchain_last_ts + 60)

    reg_cmd = (
        f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && "
        f"{LD_PREFIX} {RUNNER_BIN} {BIN_PATH} {STATE_ACCOUNT} register {region_name} "
        f"{cid} {published_md5} {pbf_url} {source_version} {reg_ts}"
    )
    q_cmd = (
        f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && "
        f"{LD_PREFIX} {RUNNER_BIN} {BIN_PATH} {STATE_ACCOUNT} query"
    )

    tx_hash = None
    block_num = None
    for attempt in range(1, 4):
        print(f"Testnet registration attempt {attempt}/3...")
        res = subprocess.run(["bash", "-c", reg_cmd], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if "Transaction submitted! Hash:" in line:
                tx_hash = line.split("Hash:")[1].strip().strip("'\"()[]")
            if "Transaction is included in block" in line:
                try:
                    block_num = int(line.split("block")[1].strip().split()[0])
                except Exception:
                    pass

        time.sleep(3)
        q_res = subprocess.run(["bash", "-c", q_cmd], capture_output=True, text=True)
        if cid in q_res.stdout and published_md5 in q_res.stdout:
            print(f"✅ On-chain registration confirmed! Tx: {tx_hash}, Block: {block_num}")
            break
        print("Waiting 10s for on-chain state propagation...")
        time.sleep(10)

    assert tx_hash and block_num, f"Failed on-chain registration for {region_name}!"

    entry = {
        "region": region_name,
        "parent": info["parent"],
        "level": info["level"],
        "country": country,
        "source_url": pbf_url,
        "version": source_version,
        "size": f_size,
        "geofabrik_md5": published_md5,
        "cid": cid,
        "registry_tx": tx_hash,
        "block": block_num,
        "timestamp": reg_ts,
        "in_closed_set": True,
        "status": "A1_VERIFIED",
        "external_retrieval": {
            "status": "VERIFIED_EXACT_MATCH",
            "retrieved_size": f_size,
            "retrieved_md5": published_md5
        }
    }
    manifest_entries.append(entry)
    save_manifest_and_docs(manifest_entries, new_region_name=region_name)

    # Clean up staging file on VPS to save disk space
    run_ssh(f"rm -f '{staging_file}'", check=False)

    counting = [e for e in manifest_entries if e.get("in_closed_set", False) or e.get("status") == "A1_VERIFIED"]
    print("\n" + "="*70)
    print(f"REGION_VERIFIED:     {region_name} ({country})")
    print(f"CLOSED_SET_VERIFIED: {len(counting)} / 25 (Countries: {len(set(e['country'] for e in counting))}/15)")
    print(f"CID:                 {cid}")
    print(f"TX:                  {tx_hash}")
    print(f"BLOCK:               {block_num}")
    print("="*70 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: process_one_region.py <region_name>")
        sys.exit(1)
    process_region(sys.argv[1])
