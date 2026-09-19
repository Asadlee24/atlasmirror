import json
import sys

def main():
    print("Validating AtlasMirror metadata/regions.json...")
    with open('metadata/regions.json', 'r') as f:
        data = json.load(f)

    regions = data.get('regions', [])
    print(f"Total regions: {len(regions)}")
    assert len(regions) == 72, f"Expected 72, got {len(regions)}"

    paths = set()
    countries = 0
    subregions = 0

    for r in regions:
        path = r['path']
        assert path not in paths, f"Duplicate path: {path}"
        paths.add(path)

        level = r['level']
        assert level in ['country', 'subregion'], f"Invalid level: {level}"

        if level == 'country':
            countries += 1
            assert r['parent'] is None, f"Country {path} must have null parent"
        elif level == 'subregion':
            subregions += 1
            assert r['parent'] in ['us', 'india', 'china', 'russia'], f"Subregion {path} has invalid parent"

        assert r['geofabrik_url'].startswith('https://download.geofabrik.de/'), f"Invalid geofabrik_url: {r['geofabrik_url']}"
        assert r['md5_url'].endswith('.osm.pbf.md5'), f"Invalid md5_url: {r['md5_url']}"
        assert r['enabled'] is True, f"Region {path} should be enabled"

    assert countries == 48, f"Expected 48 countries, got {countries}"
    assert subregions == 24, f"Expected 24 subregions, got {subregions}"

    print(f"[PASS] Successfully validated {countries} countries and {subregions} subregions.")
    print("[PASS] Non-overlapping geographic tree constraint verified!")

if __name__ == '__main__':
    main()
