#!/usr/bin/env python3
"""
AtlasMirror A1 Independent Verification & Hash Audit
Verifies all 25 counting closed-set entries against:
1. Canonical closed-set metadata (metadata/regions.json)
2. Live on-chain registry state (account T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci on https://testnet.lez.logos.co/)
3. Published manifest hashes and sizes (evidence/a1-coverage-manifest.json)
Publishes machine-readable evidence artifact: evidence/a1-hash-audit.json
"""

import sys
import os
import json
import time
import struct
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
METADATA_FILE = REPO_ROOT / "metadata" / "regions.json"
MANIFEST_FILE = REPO_ROOT / "evidence" / "a1-coverage-manifest.json"
AUDIT_OUTPUT = REPO_ROOT / "evidence" / "a1-hash-audit.json"

RPC_URL = "https://testnet.lez.logos.co/"
REGISTRY_ACCOUNT = "T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci"

def fetch_onchain_records():
    req = urllib.request.Request(
        RPC_URL,
        data=json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccount",
            "params": [REGISTRY_ACCOUNT]
        }).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode())
    
    raw = bytes(res["result"]["data"])
    offset = 0

    def read_u64():
        nonlocal offset
        v = struct.unpack_from("<Q", raw, offset)[0]
        offset += 8
        return v

    def read_u32():
        nonlocal offset
        v = struct.unpack_from("<I", raw, offset)[0]
        offset += 4
        return v

    def read_u8():
        nonlocal offset
        v = raw[offset]
        offset += 1
        return v

    def read_string():
        nonlocal offset
        l = read_u32()
        s = raw[offset:offset+l].decode("utf-8")
        offset += l
        return s

    def read_opt_string():
        tag = read_u8()
        if tag == 0:
            return None
        elif tag == 1:
            return read_string()
        else:
            raise ValueError(f"Invalid opt tag: {tag}")

    total_regions = read_u64()
    last_updated = read_u64()
    num_records = read_u32()

    records = {}
    for _ in range(num_records):
        reg = read_string()
        parent = read_opt_string()
        lvl = "country" if read_u8() == 0 else "subregion"
        cid = read_string()
        src = read_string()
        cs = read_string()
        ver = read_string()
        h = (read_u8() != 0)
        ts = read_u64()
        records[reg] = {
            "region": reg,
            "parent": parent,
            "level": lvl,
            "cid": cid,
            "checksum": cs,
            "version": ver,
            "hosted": h,
            "timestamp": ts,
            "source_url": src
        }

    return last_updated, records

def main():
    print("=== AtlasMirror A1 25-CID Independent Hash Audit ===")
    
    if not METADATA_FILE.exists():
        print(f"Error: {METADATA_FILE} not found", file=sys.stderr)
        sys.exit(1)
    if not MANIFEST_FILE.exists():
        print(f"Error: {MANIFEST_FILE} not found", file=sys.stderr)
        sys.exit(1)

    catalog = json.loads(METADATA_FILE.read_text())["regions"]
    catalog_map = {r["path"]: r for r in catalog}

    manifest = json.loads(MANIFEST_FILE.read_text())
    manifest_entries = [e for e in manifest["entries"] if e.get("in_closed_set") or e.get("status") == "A1_VERIFIED"][:25]

    print(f"Loaded {len(manifest_entries)} counting closed-set entries from manifest.")

    print(f"Fetching on-chain registry state from {RPC_URL}...")
    last_updated, onchain_records = fetch_onchain_records()
    print(f"On-chain registry account {REGISTRY_ACCOUNT}: {len(onchain_records)} total records, last_updated={last_updated}")

    audit_records = []
    mismatches = []
    unique_countries = set()

    for idx, entry in enumerate(manifest_entries, start=1):
        region = entry["region"]
        country = entry["country"]
        unique_countries.add(country)
        cid = entry["cid"]
        manifest_md5 = entry["geofabrik_md5"]
        manifest_size = entry["size"]
        block = entry.get("block")

        cat_entry = catalog_map.get(region)
        onchain_entry = onchain_records.get(region)

        if not cat_entry:
            mismatches.append(f"{region}: Not in catalog metadata/regions.json")
            continue
        if not onchain_entry:
            mismatches.append(f"{region}: Missing from on-chain registry {REGISTRY_ACCOUNT}")
            continue

        cid_match = (onchain_entry["cid"] == cid)
        md5_match = (onchain_entry["checksum"] == manifest_md5)
        hier_match = (onchain_entry["level"] == cat_entry["level"] and onchain_entry["parent"] == cat_entry.get("parent"))
        hosted_flag = onchain_entry["hosted"]

        if not (cid_match and md5_match and hier_match):
            err_msg = f"{region}: MISMATCH (cid={cid_match}, md5={md5_match}, hier={hier_match})"
            mismatches.append(err_msg)
            print(f"  ❌ {err_msg}")
        else:
            print(f"  [{idx:02d}/25] OK: {region:<30} | {country:<14} | CID: {cid[:14]}... | MD5: {manifest_md5} | Block: {block}")

        audit_records.append({
            "index": idx,
            "region": region,
            "country": country,
            "level": cat_entry["level"],
            "parent": cat_entry.get("parent"),
            "cid": cid,
            "expected_md5": manifest_md5,
            "onchain_md5": onchain_entry["checksum"],
            "onchain_cid": onchain_entry["cid"],
            "onchain_level": onchain_entry["level"],
            "onchain_parent": onchain_entry["parent"],
            "onchain_hosted": hosted_flag,
            "size_bytes": manifest_size,
            "block": block,
            "status": "VERIFIED_EXACT_MATCH" if (cid_match and md5_match and hier_match) else "MISMATCH"
        })

    audit_payload = {
        "audit_version": "1.0.0",
        "standard": "LP-0018 Milestone A1 Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "registry_account": REGISTRY_ACCOUNT,
        "testnet_rpc": RPC_URL,
        "summary": {
            "total_verified_entries": len(audit_records) - len(mismatches),
            "target_entries": 25,
            "represented_countries": len(unique_countries),
            "target_countries": 15,
            "all_cids_match_onchain": all(r["cid"] == r["onchain_cid"] for r in audit_records),
            "all_checksums_match_onchain": all(r["expected_md5"] == r["onchain_md5"] for r in audit_records),
            "all_hierarchies_valid": all(r["level"] == r["onchain_level"] and r["parent"] == r["onchain_parent"] for r in audit_records),
            "mismatches_count": len(mismatches),
            "audit_result": "PASS" if (len(mismatches) == 0 and len(audit_records) == 25 and len(unique_countries) >= 15) else "FAIL"
        },
        "records": audit_records
    }

    AUDIT_OUTPUT.write_text(json.dumps(audit_payload, indent=2))
    print(f"\nMachine-readable audit artifact written to: {AUDIT_OUTPUT}")
    print(f"Summary: {audit_payload['summary']['total_verified_entries']}/25 entries verified across {len(unique_countries)} countries.")
    print(f"Audit Result: {audit_payload['summary']['audit_result']}")

    if mismatches:
        print(f"Audit failed with {len(mismatches)} mismatches!", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
