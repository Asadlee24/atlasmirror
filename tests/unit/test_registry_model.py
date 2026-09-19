#!/usr/bin/env python3
"""
Unit Test: SPEL OSM Registry State Model
NOTE: This is a local in-memory MODEL and UNIT TEST for validating registry business logic:
- Unique region paths
- Region hierarchy (country vs subregion)
- Monotonic timestamp ordering (rejecting timestamp regression)
- Single and batch record ingestion logic
THIS IS NOT LEZ AND DOES NOT CONSTITUTE BLOCKCHAIN TRANSACTION EVIDENCE.
Real LEZ sequencer integration is tested separately in tests/integration/test_lez_registry_real.py.
"""

import json
import time
from typing import Dict, List, Optional, Any

class SpelRegistryModel:
    """In-memory model of the SPEL OSM registry contract logic for unit testing."""
    def __init__(self):
        self.records: Dict[str, Dict[str, Any]] = {}
        self.cid_index: Dict[str, str] = {}
        self.parent_index: Dict[str, List[str]] = {}

    def register(self, region: str, parent: Optional[str], level: str, cid: str,
                 source_url: str, checksum: str, version: str, timestamp: int) -> Dict[str, Any]:
        if not region or not cid or not checksum or not version:
            raise ValueError("Missing required fields")

        if region in self.records:
            existing = self.records[region]
            if timestamp < existing["timestamp"]:
                raise ValueError(f"TimestampRegression: {timestamp} < {existing['timestamp']}")
            if existing.get("cid") in self.cid_index:
                del self.cid_index[existing["cid"]]

        record = {
            "region": region,
            "parent": parent,
            "level": level,
            "cid": cid,
            "source_url": source_url,
            "checksum": checksum,
            "version": version,
            "hosted": True,
            "timestamp": timestamp,
        }
        self.records[region] = record
        self.cid_index[cid] = region
        if parent:
            self.parent_index.setdefault(parent, [])
            if region not in self.parent_index[parent]:
                self.parent_index[parent].append(region)
        return {"status": "SUCCESS", "region": region}

    def batch_register(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(records) > 25:
            raise ValueError("Batch exceeds max limit of 25")
        for rec in records:
            self.register(
                rec["region"], rec.get("parent"), rec["level"], rec["cid"],
                rec["source_url"], rec["checksum"], rec["version"], rec["timestamp"]
            )
        return {"status": "SUCCESS", "count": len(records)}

    def lookup_region(self, region: str) -> Optional[Dict[str, Any]]:
        return self.records.get(region)

    def lookup_cid(self, cid: str) -> Optional[Dict[str, Any]]:
        region = self.cid_index.get(cid)
        return self.records.get(region) if region else None

    def lookup_parent(self, parent: str) -> List[Dict[str, Any]]:
        children = self.parent_index.get(parent, [])
        return [self.records[c] for c in children if c in self.records]

def test_registry_model():
    print("Running Milestone 4: SPEL Registry Model Unit Tests (In-Memory)...")
    model = SpelRegistryModel()

    print("[1/4] Testing single region registration model...")
    res = model.register(
        region="asia/pakistan",
        parent=None,
        level="country",
        cid="model_cid_pakistan",
        source_url="https://download.geofabrik.de/asia/pakistan-latest.osm.pbf",
        checksum="59227227dab323be9d50da2fbdef2c64",
        version="2026-09-18",
        timestamp=1726700000,
    )
    assert res["status"] == "SUCCESS"
    assert model.lookup_region("asia/pakistan") is not None
    assert model.lookup_cid("model_cid_pakistan") is not None
    print("  Single registration & lookups: [PASS]")

    print("[2/4] Testing parent index lookup model...")
    model.register("us/california", "us", "subregion", "model_cid_cal", "url", "hash", "v1", 1726700001)
    model.register("us/texas", "us", "subregion", "model_cid_tex", "url", "hash", "v1", 1726700002)
    children = model.lookup_parent("us")
    assert len(children) == 2
    assert {c["region"] for c in children} == {"us/california", "us/texas"}
    print("  Parent index lookup: [PASS]")

    print("[3/4] Testing monotonic timestamp ordering (regression rejection)...")
    try:
        model.register(
            region="asia/pakistan",
            parent=None,
            level="country",
            cid="model_cid_pakistan_old",
            source_url="https://download.geofabrik.de/asia/pakistan-latest.osm.pbf",
            checksum="old_hash",
            version="2026-09-01",
            timestamp=1726600000, # older than 1726700000
        )
        assert False, "CRITICAL: Timestamp regression was not rejected!"
    except ValueError as e:
        assert "TimestampRegression" in str(e)
        print("  Timestamp regression rejection: [PASS]")

    print("[4/4] Testing batch registration model...")
    batch = [
        {
            "region": f"region/test_{i}",
            "parent": None,
            "level": "country",
            "cid": f"model_cid_test_{i}",
            "source_url": f"https://example.com/test_{i}",
            "checksum": f"checksum_{i}",
            "version": "2026-09-19",
            "timestamp": 1726700000 + i,
        }
        for i in range(10)
    ]
    batch_res = model.batch_register(batch)
    assert batch_res["status"] == "SUCCESS"
    assert batch_res["count"] == 10
    print("  Batch registration model: [PASS]")

    print("\n[PASS] Registry model unit tests = VERIFIED UNIT TEST")
    print("  (Note: Real LEZ sequencer integration = NOT VERIFIED)")

if __name__ == "__main__":
    test_registry_model()
