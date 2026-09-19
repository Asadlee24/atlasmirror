#!/usr/bin/env python3
"""
Unit Test: Validate LP-0018 Predefined Regions Catalog
Verifies:
- metadata/regions.json exists and is valid JSON
- Exactly 72 regions defined (48 countries, 24 subregions)
- Non-overlapping geographic tree constraint
"""

import json
import sys
from pathlib import Path

def test_catalog():
    catalog_path = Path("metadata/regions.json")
    if not catalog_path.exists():
        print(f"[FAIL] {catalog_path} not found")
        sys.exit(1)

    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    regions = data.get("regions", [])
    print(f"Validating AtlasMirror {catalog_path}...")
    print(f"Total regions: {len(regions)}")

    if len(regions) != 72:
        print(f"[FAIL] Expected exactly 72 predefined regions, got {len(regions)}")
        sys.exit(1)

    countries = [r for r in regions if r.get("level") == "country"]
    subregions = [r for r in regions if r.get("level") == "subregion"]

    if len(countries) != 48:
        print(f"[FAIL] Expected exactly 48 countries, got {len(countries)}")
        sys.exit(1)

    if len(subregions) != 24:
        print(f"[FAIL] Expected exactly 24 subregions, got {len(subregions)}")
        sys.exit(1)

    # Verify no country overlaps with subregions:
    # If a country is listed, its subregions must not be listed, and vice versa.
    country_paths = {c["path"] for c in countries}
    for sub in subregions:
        parent = sub.get("parent")
        if parent in country_paths:
            print(f"[FAIL] Overlap detected: Parent '{parent}' and subregion '{sub['path']}' are both present!")
            sys.exit(1)

    print(f"[PASS] Successfully validated {len(countries)} countries and {len(subregions)} subregions.")
    print("[PASS] Non-overlapping geographic tree constraint verified!")

if __name__ == "__main__":
    test_catalog()
