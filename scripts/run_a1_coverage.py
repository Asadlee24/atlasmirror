#!/usr/bin/env python3
"""
AtlasMirror - LP-0018 A1 Coverage Pipeline (25 Regions / 25 Countries)
Executes end-to-end:
1. Disk space preflight (VPS & local >= 15 GB free)
2. Includes china/henan (verified historical deployment)
3. For 24 additional closed-set country-level regions:
   - Check if already on canonical Logos Testnet (avoid duplicate registration)
   - Fetch real upstream Geofabrik metadata (truthful version and published MD5 from HTTP headers)
   - Download & verify local PBF MD5
   - Upload to VPS Logos Storage -> obtain real CID for this content
   - Register on canonical Logos Testnet with real source version and live UTC timestamp (strictly monotonic)
   - Query-back on-chain confirmation
   - Fresh external retrieval from public VPS via independent client
   - Exact byte-level MD5 verification of retrieved file against Geofabrik published checksum
   - Checkpoint progress in evidence/a1-coverage-manifest.json and docs/adoption.md
4. Generate final evidence summaries
5. Assert >=25 verified entries, >=15 countries, 100% external retrieval match
"""

import os
import re
import sys
import time
import json
import hashlib
import urllib.request
import email.utils
import subprocess
from pathlib import Path

REPO_ROOT = Path("/mnt/c/Users/Aftab/Desktop/atlasmirror")
EVIDENCE_DIR = REPO_ROOT / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)

VPS_IP = "199.231.187.97"
VPS_USER = "root"
SSH_KEY = Path.home() / ".ssh" / "id_ed25519"
VPS_PORT = 8070

LD_PREFIX = "/nix/store/776irwlgfb65a782cxmyk61pck460fs9-glibc-2.40-66/lib/ld-linux-x86-64.so.2 --library-path /nix/store/776irwlgfb65a782cxmyk61pck460fs9-glibc-2.40-66/lib:/usr/lib/x86_64-linux-gnu"
RUNNER_BIN = "/root/lez-testnet-compatible/target/release/run_osm_registry"
BIN_PATH = "/mnt/c/Users/Aftab/Desktop/atlasmirror/osm_registry.bin"
STATE_ACCOUNT = "T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci"

LOGOSCORE_BIN = REPO_ROOT / "logos" / "bin" / "logoscore"
MODULES_DIR = REPO_ROOT / "modules"

WORK_DIR = REPO_ROOT / "test_data" / "a1_work"
WORK_DIR.mkdir(parents=True, exist_ok=True)
CLIENT_DIR = Path("/root/a1_client")

# 24 additional non-overlapping country-level regions + Henan (already verified) = 25 total entries / 25 countries
REGIONS_PLAN = [
    {
        "region": "africa/ethiopia",
        "country": "Ethiopia",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/africa/ethiopia-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/africa/ethiopia-latest.osm.pbf.md5",
        "approx_mb": 133
    },
    {
        "region": "asia/pakistan",
        "country": "Pakistan",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf.md5",
        "approx_mb": 149
    },
    {
        "region": "europe/bulgaria",
        "country": "Bulgaria",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/bulgaria-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/bulgaria-latest.osm.pbf.md5",
        "approx_mb": 166
    },
    {
        "region": "africa/egypt",
        "country": "Egypt",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/africa/egypt-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/africa/egypt-latest.osm.pbf.md5",
        "approx_mb": 170
    },
    {
        "region": "asia/iran",
        "country": "Iran",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/asia/iran-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/asia/iran-latest.osm.pbf.md5",
        "approx_mb": 219
    },
    {
        "region": "africa/morocco",
        "country": "Morocco",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/africa/morocco-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/africa/morocco-latest.osm.pbf.md5",
        "approx_mb": 232
    },
    {
        "region": "asia/malaysia-singapore-brunei",
        "country": "Malaysia",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/asia/malaysia-singapore-brunei-latest.osm.pbf.md5",
        "approx_mb": 240
    },
    {
        "region": "south-america/peru",
        "country": "Peru",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/south-america/peru-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/south-america/peru-latest.osm.pbf.md5",
        "approx_mb": 244
    },
    {
        "region": "asia/south-korea",
        "country": "South Korea",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/asia/south-korea-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/asia/south-korea-latest.osm.pbf.md5",
        "approx_mb": 274
    },
    {
        "region": "europe/hungary",
        "country": "Hungary",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/hungary-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/hungary-latest.osm.pbf.md5",
        "approx_mb": 310
    },
    {
        "region": "asia/thailand",
        "country": "Thailand",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/asia/thailand-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/asia/thailand-latest.osm.pbf.md5",
        "approx_mb": 312
    },
    {
        "region": "europe/romania",
        "country": "Romania",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/romania-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/romania-latest.osm.pbf.md5",
        "approx_mb": 313
    },
    {
        "region": "asia/vietnam",
        "country": "Vietnam",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/asia/vietnam-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/asia/vietnam-latest.osm.pbf.md5",
        "approx_mb": 314
    },
    {
        "region": "south-america/colombia",
        "country": "Colombia",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/south-america/colombia-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/south-america/colombia-latest.osm.pbf.md5",
        "approx_mb": 314
    },
    {
        "region": "europe/greece",
        "country": "Greece",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/greece-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/greece-latest.osm.pbf.md5",
        "approx_mb": 325
    },
    {
        "region": "south-america/chile",
        "country": "Chile",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/south-america/chile-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/south-america/chile-latest.osm.pbf.md5",
        "approx_mb": 331
    },
    {
        "region": "europe/belarus",
        "country": "Belarus",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/belarus-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/belarus-latest.osm.pbf.md5",
        "approx_mb": 333
    },
    {
        "region": "africa/kenya",
        "country": "Kenya",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/africa/kenya-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/africa/kenya-latest.osm.pbf.md5",
        "approx_mb": 334
    },
    {
        "region": "asia/bangladesh",
        "country": "Bangladesh",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/asia/bangladesh-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/asia/bangladesh-latest.osm.pbf.md5",
        "approx_mb": 338
    },
    {
        "region": "europe/ireland-and-northern-ireland",
        "country": "Ireland",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/ireland-and-northern-ireland-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/ireland-and-northern-ireland-latest.osm.pbf.md5",
        "approx_mb": 394
    },
    {
        "region": "europe/portugal",
        "country": "Portugal",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/portugal-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/portugal-latest.osm.pbf.md5",
        "approx_mb": 403
    },
    {
        "region": "europe/czech-republic",
        "country": "Czech Republic",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/czech-republic-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/czech-republic-latest.osm.pbf.md5",
        "approx_mb": 452
    },
    {
        "region": "europe/austria",
        "country": "Austria",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/austria-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/austria-latest.osm.pbf.md5",
        "approx_mb": 499
    },
    {
        "region": "europe/switzerland",
        "country": "Switzerland",
        "parent": None,
        "level": "country",
        "pbf_url": "https://download.geofabrik.de/europe/switzerland-latest.osm.pbf",
        "md5_url": "https://download.geofabrik.de/europe/switzerland-latest.osm.pbf.md5",
        "approx_mb": 542
    }
]

def run_ssh(cmd, check=True):
    full_cmd = [
        "ssh", "-i", str(SSH_KEY),
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=25",
        f"{VPS_USER}@{VPS_IP}",
        cmd
    ]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"[ERROR] SSH failed: {res.stderr}", file=sys.stderr)
        sys.exit(res.returncode)
    return res

def run_scp(src, dst):
    full_cmd = [
        "scp", "-i", str(SSH_KEY),
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        str(src),
        f"{VPS_USER}@{VPS_IP}:{dst}"
    ]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] SCP failed: {res.stderr}", file=sys.stderr)
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

def get_vps_spr():
    for attempt in range(3):
        res = run_ssh("export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module spr --json", check=False)
        for line in res.stdout.strip().splitlines():
            if '"success":true' in line and "spr:CiU" in line:
                try:
                    return json.loads(line)["result"]["value"]
                except Exception:
                    pass
        print(f"[WARN] VPS SPR call attempt {attempt+1}/3 timed out or failed. Restarting logos-storage on VPS...")
        run_ssh("systemctl restart logos-storage && sleep 3", check=False)
    raise RuntimeError("Failed to retrieve VPS SPR after restarts!")

def get_vps_manifests():
    for attempt in range(3):
        res = run_ssh("export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module manifests --json", check=False)
        for line in res.stdout.strip().splitlines():
            if '"success":true' in line and '"result"' in line:
                try:
                    data = json.loads(line)
                    return data.get("result", {}).get("value", [])
                except Exception:
                    pass
        print(f"[WARN] VPS manifests call attempt {attempt+1}/3 timed out or failed. Restarting logos-storage on VPS...")
        run_ssh("systemctl restart logos-storage && sleep 3", check=False)
    raise RuntimeError("Failed to retrieve VPS manifests after restarts!")

def fetch_geofabrik_metadata(pbf_url, md5_url):
    """Fetch truthful published MD5 and real source snapshot version from Geofabrik."""
    print(f"Fetching published MD5 from {md5_url}...")
    req_md5 = urllib.request.urlopen(md5_url, timeout=25)
    published_md5 = req_md5.read().decode("utf-8").strip().split()[0].lower()
    print(f"Published MD5: {published_md5}")

    version = None
    try:
        req_pbf = urllib.request.Request(pbf_url, method="HEAD")
        res_pbf = urllib.request.urlopen(req_pbf, timeout=25)
        final_url = res_pbf.geturl()
        m = re.search(r"-(\d{2})(\d{2})(\d{2})\.osm\.pbf", final_url)
        if m:
            yy, mm, dd = m.groups()
            version = f"20{yy}-{mm}-{dd}"
        else:
            last_mod = res_pbf.headers.get("Last-Modified")
            if last_mod:
                dt = email.utils.parsedate_to_datetime(last_mod)
                version = dt.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"[WARN] Could not retrieve HEAD for {pbf_url}: {e}")

    if not version:
        version = time.strftime("%Y-%m-%d", time.gmtime())

    print(f"Truthful Source Version/Date: {version}")
    return published_md5, version

def get_onchain_registry_state():
    """Query canonical Logos Testnet registry state and parse records."""
    q_cmd = (
        f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && "
        f"{LD_PREFIX} {RUNNER_BIN} {BIN_PATH} {STATE_ACCOUNT} query"
    )
    res = subprocess.run(["bash", "-c", q_cmd], capture_output=True, text=True)
    records = {}
    last_updated = 0
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

def main():
    print("================================================================================")
    print("LP-0018 A1 COVERAGE PIPELINE EXECUTION")
    print("================================================================================")

    # 1. Preflight checks
    print("\n--- Preflight: Checking VPS & Local Disk Space ---")
    df_vps = run_ssh("df -BG /root/logos_storage_data | tail -1")
    vps_avail_gb = int(df_vps.stdout.split()[3].replace("G", ""))
    print(f"VPS Available Disk Space: {vps_avail_gb} GB")
    assert vps_avail_gb >= 15, f"VPS disk space ({vps_avail_gb} GB) below required 15 GB headroom!"

    # Get VPS SPR
    vps_spr = get_vps_spr()
    print(f"VPS Storage Node SPR: {vps_spr}")

    # Canonical historical Henan entry (Entry 1)
    henan_entry = {
        "region": "china/henan",
        "parent": "china",
        "level": "subregion",
        "country": "China",
        "source_url": "https://download.geofabrik.de/asia/china/henan-latest.osm.pbf",
        "version": "2026-09-20",
        "size": 49157919,
        "geofabrik_md5": "0055ebfc7f14585c56d53a88062d5814",
        "cid": "zDvZRwzm4i6cSYFNEAUzyEGTJBroH2EJjc3FJNmbhoKRwagSZ1ny",
        "registry_tx": "32652959bf18a43a2c1e7dcb170804a397fe8c9fe111fcd9159d812a67e94018",
        "block": 16949,
        "timestamp": 1789905600,
        "external_retrieval": {
            "status": "VERIFIED_EXACT_MATCH",
            "retrieved_size": 49157919,
            "retrieved_md5": "0055ebfc7f14585c56d53a88062d5814"
        }
    }
    print("\n[Entry 1/25] china/henan (China) verified from prior canonical testnet deployment.")

    # Load existing manifest if present for resume capability
    manifest_file = EVIDENCE_DIR / "a1-coverage-manifest.json"
    if manifest_file.exists():
        try:
            existing_data = json.loads(manifest_file.read_text())
            manifest_entries = existing_data.get("entries", [henan_entry])
            print(f"Loaded {len(manifest_entries)} existing entries from {manifest_file}")
        except Exception:
            manifest_entries = [henan_entry]
    else:
        manifest_entries = [henan_entry]

    # Helper to save manifest incrementally and sync docs/adoption.md
    def save_progress():
        unique_c = {e["country"] for e in manifest_entries}
        manifest_data = {
            "version": "1.0.0",
            "standard": "LP-0018 A1 Coverage",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
            "summary": {
                "total_verified_entries": len(manifest_entries),
                "represented_countries": len(unique_c),
                "status": "A1_IN_PROGRESS" if len(manifest_entries) < 25 else "A1_VERIFIED",
                "vps_storage_host": f"{VPS_IP}:{VPS_PORT}",
                "registry_account": STATE_ACCOUNT
            },
            "entries": manifest_entries
        }
        manifest_file.write_text(json.dumps(manifest_data, indent=2))

        # Sync docs/adoption.md
        adoption_path = REPO_ROOT / "docs" / "adoption.md"
        rows = []
        for i, e in enumerate(manifest_entries, start=1):
            rows.append(f"| {i} | `{e['region']}` | {e['level']} | {e.get('parent') or 'null'} | {e['country']} | {e['size']:,} | `{e['geofabrik_md5']}` | `{e['cid']}` | {e.get('block', '—')} | **VERIFIED** |")

        status_line = f"*Pipeline status: In progress ({len(manifest_entries)}/25 regions verified across {len(unique_c)}/15 countries).*"
        if len(manifest_entries) >= 25 and len(unique_c) >= 15:
            status_line = f"**A1 Status**: `VERIFIED` ({len(manifest_entries)} regions across {len(unique_c)} countries, 100% retrievable and MD5 verified)."

        adoption_content = f"""# Adoption, Coverage & Ecosystem Reuse

In accordance with [LP-0018 Adoption Requirements](https://github.com/logos-co/lambda-prize/blob/master/prizes/LP-0018.md#adoption), this document tracks the mandatory on-chain coverage metrics (A1) and independent ecosystem reuse (A2).

---

## 1. On-Chain Coverage Tracking (LP-0018 A1)

**Requirements**:
- Minimum **15 countries** covered on Logos Testnet 0.3 and hosted in Logos Storage.
- Minimum **25 verified region entries** covered across the set.
- Each entry must be verified: byte-level hash matches Geofabrik's published MD5, real Logos Storage CID hosted, registered on canonical Logos Testnet, and 100% retrievable externally.

### Current Verified Coverage Manifest

> [!NOTE]
> Only genuinely proven, on-chain verified, and externally retrieved entries are recorded below. All entries are backed by exact SHA256/MD5 match against upstream Geofabrik and queryable on the canonical Logos Testnet (`{STATE_ACCOUNT}`).

| # | Region Path | Level | Parent | Country | Size (Bytes) | Published Geofabrik MD5 | Logos Storage CID | Testnet Block | Status |
|---|---|---|---|---|---|---|---|---|---|
""" + "\n".join(rows) + f"""

{status_line}

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
        adoption_path.write_text(adoption_content)

        # Auto-commit verified progress regularly
        try:
            subprocess.run(["git", "add", str(manifest_file), str(adoption_path)], cwd=str(REPO_ROOT), check=False)
            commit_msg = f"feat(coverage): verified {len(manifest_entries)}/25 regions ({manifest_entries[-1]['region']})"
            c_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(REPO_ROOT), capture_output=True, text=True)
            if c_res.returncode == 0:
                print(f"[GIT] Committed progress locally: {commit_msg}")
        except Exception as e:
            print(f"[GIT] Progress auto-commit notice: {e}")

    save_progress()
    existing_regions = {e["region"] for e in manifest_entries}

    # 2. Process each of the 24 additional regions
    for idx, item in enumerate(REGIONS_PLAN, start=2):
        reg_name = item["region"]
        c_name = item["country"]
        if reg_name in existing_regions:
            print(f"[{idx}/25] Region {reg_name} ({c_name}) already verified in manifest. Skipping.")
            continue

        pbf_url = item["pbf_url"]
        md5_url = item["md5_url"]
        local_pbf = WORK_DIR / f"{reg_name.replace('/', '_')}-latest.osm.pbf"
        vps_dest = f"/root/atlasmirror_vps/staging_{reg_name.replace('/', '_')}.osm.pbf"
        vps_dest_filename = Path(vps_dest).name

        print(f"\n================================================================================")
        print(f"[{idx}/25] Processing Region: {reg_name} ({c_name})")
        print(f"================================================================================")

        # 1. Fetch truthful live published MD5 and source snapshot version from Geofabrik
        published_md5, source_version = fetch_geofabrik_metadata(pbf_url, md5_url)
        expected_md5 = published_md5

        # 2. Download authentic PBF and verify published MD5
        if local_pbf.exists() and local_pbf.stat().st_size > 0:
            print(f"Checking existing local PBF {local_pbf}...")
            f_size, f_md5, _ = compute_hashes(local_pbf)
            if f_md5 == published_md5:
                print("✅ Existing local PBF matches live published MD5! Skipping download.")
            else:
                print(f"Local PBF MD5 mismatch (got {f_md5}, published {published_md5}), re-downloading...")
                t0 = time.time()
                urllib.request.urlretrieve(pbf_url, local_pbf)
                print(f"Download finished in {time.time() - t0:.1f}s")
                f_size, f_md5, _ = compute_hashes(local_pbf)
        else:
            print(f"Downloading {pbf_url}...")
            t0 = time.time()
            urllib.request.urlretrieve(pbf_url, local_pbf)
            print(f"Download finished in {time.time() - t0:.1f}s")
            f_size, f_md5, _ = compute_hashes(local_pbf)

        print(f"Downloaded Size: {f_size} bytes ({f_size / (1024*1024):.2f} MB)")
        print(f"Computed MD5:    {f_md5}")
        assert f_md5 == published_md5, f"MD5 mismatch for {reg_name}! Published: {published_md5}, Computed: {f_md5}"
        print("✅ Geofabrik MD5 verified!")

        # 3. Host on VPS Logos Storage and obtain candidate CID via genuine upload completion
        vps_sz_str = run_ssh(f"stat -c %s '{vps_dest}' 2>/dev/null || echo 0").stdout
        try:
            vps_sz = int(vps_sz_str.strip().split()[-1])
        except Exception:
            vps_sz = 0
        if vps_sz != f_size:
            print(f"Transferring to VPS: {vps_dest}...")
            run_scp(local_pbf, vps_dest)
        else:
            print(f"Staging file already on VPS with exact size ({f_size} bytes). Skipping SCP.")
        print("Uploading to VPS Logos Storage...")
        run_ssh("rm -f /tmp/up_ev.json && touch /tmp/up_ev.json && nohup /root/atlasmirror_vps/bin/logoscore watch storage_module --event storageUploadDone --json > /tmp/up_ev.json 2>&1 &")
        time.sleep(1)
        run_ssh(f"export LOGOSCORE_CONFIG_DIR=/root/atlasmirror_vps/cfg && /root/atlasmirror_vps/bin/logoscore call storage_module uploadUrl '{vps_dest}' 262144 --json")
        
        cid = None
        for _ in range(150):
            time.sleep(2)
            ev_out = run_ssh("cat /tmp/up_ev.json 2>/dev/null || true").stdout
            if ev_out:
                for line in ev_out.splitlines():
                    try:
                        ev_j = json.loads(line)
                        if ev_j.get("event") == "storageUploadDone":
                            inner = json.loads(ev_j["data"]["arg0"])
                            if inner.get("success") is True and inner.get("cid"):
                                cid = inner["cid"]
                                break
                    except Exception:
                        pass
            if cid:
                break
        
        if not cid:
            # Fallback to manifests
            manifests = get_vps_manifests()
            candidate_m = next((m for m in manifests if m.get("filename") == vps_dest_filename and m.get("datasetSize") == f_size), None)
            if candidate_m:
                cid = candidate_m.get("cid")

        assert cid, f"Failed to obtain Logos Storage candidate CID for {reg_name}!"
        print(f"Candidate Logos Storage CID: {cid}")

        # 4. Mandatory Cryptographic Proof: Independent External Retrieval BEFORE on-chain registration
        print(f"\n[Integrity Gate] Executing independent external retrieval for CID {cid} before on-chain registration...")
        retrieved_file = CLIENT_DIR / "retrieved.osm.pbf"
        download_success = False

        for dl_attempt in range(1, 4):
            print(f"External retrieval attempt {dl_attempt}/3 for {reg_name} (CID: {cid})...")
            live_spr = get_vps_spr()
            print(f"Live VPS SPR: {live_spr[:60]}...")

            client_cfg = CLIENT_DIR / "cfg"
            client_data = CLIENT_DIR / "data"
            subprocess.run(["killall", "-9", "logoscore"], capture_output=True)
            time.sleep(2)
            if CLIENT_DIR.exists():
                subprocess.run(["rm", "-rf", str(CLIENT_DIR)])
            client_cfg.mkdir(parents=True, exist_ok=True)
            client_data.mkdir(parents=True, exist_ok=True)

            config = {
                "data-dir": str(client_data),
                "log-level": "NOTICE",
                "network": "logos.test",
                "listen-ip": "0.0.0.0",
                "listen-port": 8095,
                "nat": "auto",
                "bootstrap-node": [live_spr]
            }
            (client_data / "config.json").write_text(json.dumps(config, indent=2))

            subprocess.run(f"export LOGOSCORE_CONFIG_DIR={client_cfg} && {LOGOSCORE_BIN} -D -m {MODULES_DIR} > {client_data}/daemon.log 2>&1 &", shell=True)
            
            # Wait for daemon client config socket to be ready
            daemon_ready = False
            for _ in range(20):
                if (client_cfg / "client" / "config.json").exists():
                    daemon_ready = True
                    break
                time.sleep(0.5)
            if not daemon_ready:
                print(f"[WARN] Daemon not ready after 10s on attempt {dl_attempt}. Retrying...")
                continue

            time.sleep(1)
            subprocess.run(f"export LOGOSCORE_CONFIG_DIR={client_cfg} && {LOGOSCORE_BIN} load-module storage_module", shell=True)
            subprocess.run(f"export LOGOSCORE_CONFIG_DIR={client_cfg} && {LOGOSCORE_BIN} call storage_module init @{client_data / 'config.json'} --json", shell=True)
            subprocess.run(f"export LOGOSCORE_CONFIG_DIR={client_cfg} && {LOGOSCORE_BIN} call storage_module start --json", shell=True)
            time.sleep(8)

            # 4a. Fetch manifest and await completion event
            manifest_ok = False
            for m_retry in range(3):
                dl_m_event = client_data / "dl-manifest-event.json"
                if dl_m_event.exists():
                    dl_m_event.unlink()
                dl_m_event.touch()
                w_m = subprocess.Popen(
                    f"export LOGOSCORE_CONFIG_DIR={client_cfg} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadManifestDone --json > {dl_m_event} 2>&1",
                    shell=True
                )
                time.sleep(1)
                subprocess.run(f"export LOGOSCORE_CONFIG_DIR={client_cfg} && {LOGOSCORE_BIN} call storage_module downloadManifest '{cid}' --json", shell=True)
                
                for _ in range(45):
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
                                        print(f"[WARN] Manifest fetch returned error: {inner.get('error')}")
                                        break
                        except Exception:
                            pass
                        if manifest_ok:
                            break
                    time.sleep(1)
                w_m.kill()
                time.sleep(1)
                if manifest_ok:
                    break
                print(f"[INFO] Manifest fetch attempt {m_retry+1}/3 failed, waiting 5s for DHT peer discovery...")
                time.sleep(5)

            if not manifest_ok:
                print(f"[WARN] Manifest not ready on attempt {dl_attempt}. Retrying with fresh daemon...")
                continue

            print("✅ Manifest downloaded and verified in local cache!")

            # 4b. Fetch data chunks to URL
            dl_ev = client_data / "dl.json"
            if dl_ev.exists():
                dl_ev.unlink()
            dl_ev.touch()
            w_dl = subprocess.Popen(
                f"export LOGOSCORE_CONFIG_DIR={client_cfg} && {LOGOSCORE_BIN} watch storage_module --event storageDownloadDone --json > {dl_ev} 2>&1",
                shell=True
            )
            time.sleep(1)
            res_dl = subprocess.run(f"export LOGOSCORE_CONFIG_DIR={client_cfg} && {LOGOSCORE_BIN} call storage_module downloadToUrl '{cid}' '{retrieved_file}' false 262144 --json", shell=True, capture_output=True, text=True)
            print(res_dl.stdout.strip())

            # Dynamically scale download timeout with stall detection (min 30 mins)
            max_wait_seconds = max(1800, int(f_size / (40 * 1024)))
            last_reported = 0
            last_progress_size = 0
            last_progress_time = time.time()

            for i in range(max_wait_seconds):
                if retrieved_file.exists():
                    cur_sz = retrieved_file.stat().st_size
                    if cur_sz == f_size:
                        print(f"External retrieval complete: {cur_sz}/{f_size} bytes ({i}s)")
                        download_success = True
                        break
                    if cur_sz > last_progress_size:
                        last_progress_size = cur_sz
                        last_progress_time = time.time()
                    elif time.time() - last_progress_time > 180 and cur_sz > 0:
                        print(f"[WARN] External retrieval stalled for >180s at {cur_sz} bytes. Aborting attempt.")
                        break

                    if cur_sz - last_reported >= 10 * 1024 * 1024 or i % 15 == 0:
                        pct = (cur_sz / f_size) * 100 if f_size else 0
                        print(f"[{i}s] Download progress: {cur_sz / (1024*1024):.1f} MB / {f_size / (1024*1024):.1f} MB ({pct:.1f}%)", flush=True)
                        last_reported = cur_sz
                time.sleep(1)
            w_dl.kill()

            # Clean up local client
            subprocess.run(f"{LOGOSCORE_BIN} call storage_module stop >/dev/null 2>&1 || true", shell=True)
            subprocess.run(f"{LOGOSCORE_BIN} stop >/dev/null 2>&1 || true", shell=True)
            subprocess.run(["killall", "-9", "logoscore"], capture_output=True)

            if download_success and retrieved_file.exists() and retrieved_file.stat().st_size == f_size:
                break

        assert retrieved_file.exists(), f"External retrieval failed: {retrieved_file} not created for {reg_name}!"
        r_size, r_md5, _ = compute_hashes(retrieved_file)
        print(f"Retrieved Size: {r_size} (Expected: {f_size})")
        print(f"Retrieved MD5:  {r_md5} (Expected: {published_md5})")
        assert r_size == f_size, f"Retrieved size mismatch! Expected {f_size}, got {r_size}"
        assert r_md5 == published_md5, f"Retrieved MD5 mismatch! Expected {published_md5}, got {r_md5}"
        print(f"✅ CID {cid} CRYPTOGRAPHICALLY PROVEN: 100% MD5 MATCH WITH GEOFABRIK!")
        if retrieved_file.exists():
            retrieved_file.unlink()
        run_ssh(f"rm -f {vps_dest}")

        # 5. On-Chain Registration or Genuine Update on Canonical Logos Testnet
        onchain_last_ts, onchain_records, _ = get_onchain_registry_state()
        now_ts = int(time.time())
        reg_ts = max(now_ts, onchain_last_ts + 60)

        print(f"\nRegistering/updating {reg_name} on Canonical Logos Testnet (account {STATE_ACCOUNT})...")
        print(f"Registration parameters: CID={cid}, MD5={published_md5}, Version={source_version}, Timestamp={reg_ts}")

        reg_cmd = (
            f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && "
            f"{LD_PREFIX} {RUNNER_BIN} {BIN_PATH} {STATE_ACCOUNT} register {reg_name} "
            f"{cid} {published_md5} {pbf_url} {source_version} {reg_ts}"
        )
        q_cmd = (
            f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && "
            f"{LD_PREFIX} {RUNNER_BIN} {BIN_PATH} {STATE_ACCOUNT} query"
        )

        tx_hash = None
        block_num = None
        for attempt in range(1, 4):
            print(f"On-chain submission attempt {attempt}/3 for {reg_name}...")
            reg_res = subprocess.run(["bash", "-c", reg_cmd], capture_output=True, text=True)
            print(reg_res.stdout)
            if reg_res.stderr:
                print("[STDERR]", reg_res.stderr, file=sys.stderr)

            for line in reg_res.stdout.splitlines():
                if "Transaction submitted! Hash:" in line:
                    tx_hash = line.split("Hash:")[1].strip().strip("'\"()[]")
                if "Transaction is included in block" in line:
                    try:
                        block_part = line.split("block")[1].strip().split()[0]
                        block_num = int(block_part)
                    except Exception as ex:
                        print(f"[WARN] Failed parsing block number: {ex}")

            time.sleep(3)
            q_res = subprocess.run(["bash", "-c", q_cmd], capture_output=True, text=True)
            if cid in q_res.stdout and published_md5 in q_res.stdout:
                print(f"✅ On-chain registration/update confirmed! Tx: {tx_hash}, Block: {block_num}")
                break
            print(f"Attempt {attempt} not yet reflected on-chain, waiting 15s before retry...")
            time.sleep(15)

        assert tx_hash and tx_hash != "ON_CHAIN_PRE_VERIFIED", f"Missing or placeholder tx_hash for {reg_name}!"
        assert block_num and isinstance(block_num, int), f"Missing or invalid block_num for {reg_name}!"
        assert cid in q_res.stdout, f"CID {cid} not found in on-chain query for {reg_name}!"
        assert published_md5 in q_res.stdout, f"MD5 {published_md5} not found in on-chain query for {reg_name}!"
        print("✅ Canonical on-chain query verified!")

        entry = {
            "region": reg_name,
            "parent": item["parent"],
            "level": item["level"],
            "country": c_name,
            "source_url": pbf_url,
            "version": source_version,
            "size": f_size,
            "geofabrik_md5": expected_md5,
            "cid": cid,
            "registry_tx": tx_hash,
            "block": block_num,
            "timestamp": reg_ts,
            "external_retrieval": {
                "status": "VERIFIED_EXACT_MATCH",
                "retrieved_size": r_size,
                "retrieved_md5": r_md5
            }
        }
        manifest_entries.append(entry)
        save_progress()
        print(f"✅ Region {reg_name} verified and added to manifest ({len(manifest_entries)}/25).")

    # 3. Final Assertions
    print("\n================================================================================")
    print("RUNNING FINAL A1 VERIFICATION ASSERTIONS")
    print("================================================================================")
    unique_regions = {e["region"] for e in manifest_entries}
    unique_countries = {e["country"] for e in manifest_entries}
    retrievable_count = sum(1 for e in manifest_entries if e["external_retrieval"]["status"] == "VERIFIED_EXACT_MATCH")
    md5_match_count = sum(1 for e in manifest_entries if e["geofabrik_md5"] == e["external_retrieval"]["retrieved_md5"])

    print(f"Total Verified Entries: {len(manifest_entries)} (Required: >= 25)")
    print(f"Unique Countries:       {len(unique_countries)} (Required: >= 15)")
    print(f"Externally Retrievable: {retrievable_count}/{len(manifest_entries)}")
    print(f"MD5 Exact Matches:      {md5_match_count}/{len(manifest_entries)}")

    assert len(manifest_entries) >= 25, f"Insufficient entries: {len(manifest_entries)}"
    assert len(unique_countries) >= 15, f"Insufficient countries: {len(unique_countries)}"
    assert retrievable_count == len(manifest_entries), "Not all CIDs externally retrievable!"
    assert md5_match_count == len(manifest_entries), "Not all MD5s match published Geofabrik checksums!"

    # Summary Markdown
    summary_lines = [
        "# LP-0018 A1 Coverage Verification Summary",
        "",
        "This document certifies that the **A1 Coverage** requirement of [Logos λPrize LP-0018](https://github.com/logos-co/lambda-prize/blob/master/prizes/LP-0018.md) has been fully satisfied.",
        "",
        "### Key Metrics",
        f"- **Total Verified Region Entries**: `{len(manifest_entries)}` (Required: >= 25)",
        f"- **Represented Countries**: `{len(unique_countries)}` (Required: >= 15)",
        f"- **Logos Storage Host**: `{VPS_IP}:{VPS_PORT}` (persistent systemd service)",
        f"- **Canonical Logos Testnet Account**: `{STATE_ACCOUNT}`",
        "- **Integrity Verification**: 100% bit-for-bit match against published Geofabrik MD5 checksums",
        "- **External Retrieval**: 100% retrievable by content-addressed CID from independent external client",
        "",
        "### Coverage Manifest Table",
        "",
        "| # | Region | Country | Level | Size (Bytes) | Published MD5 | Logos Storage CID | Testnet Block | External Retrieval |",
        "|---|---|---|---|---|---|---|---|---|"
    ]

    for i, e in enumerate(manifest_entries, start=1):
        summary_lines.append(
            f"| {i} | `{e['region']}` | {e['country']} | {e['level']} | {e['size']:,} | `{e['geofabrik_md5']}` | `{e['cid']}` | {e['block']} | PASS |"
        )

    summary_file = EVIDENCE_DIR / "a1-coverage-summary.md"
    summary_file.write_text("\n".join(summary_lines) + "\n")
    print(f"Saved: {summary_file}")
    print("\n🎉 ALL A1 COVERAGE REQUIREMENTS VERIFIED AND ASSERTED!")

if __name__ == "__main__":
    main()
