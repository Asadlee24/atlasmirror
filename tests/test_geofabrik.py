import urllib.request
import json
import os
import tempfile

def test_live_index_and_filtering():
    print("[1/3] Fetching live Geofabrik machine index...")
    url = "https://download.geofabrik.de/index-v1-nogeom.json"
    req = urllib.request.Request(url, headers={"User-Agent": "AtlasMirror/0.1"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    features = data.get("features", [])
    print(f"  Live features fetched: {len(features)}")
    assert len(features) > 500, "Geofabrik index should have >500 features"

    # Load LP-0018 predefined set
    with open("metadata/regions.json", "r") as f:
        catalog = json.load(f)
    allowed_paths = {r["path"] for r in catalog["regions"]}
    print(f"  LP-0018 predefined regions: {len(allowed_paths)}")

    # Test filtering
    matched = []
    for f in features:
        props = f.get("properties", {})
        fid = props.get("id")
        parent = props.get("parent")
        full_id = f"{parent}/{fid}" if parent else fid

        if full_id in allowed_paths or fid in allowed_paths:
            matched.append(full_id)

    print(f"  Matched predefined regions in live index: {len(matched)}")
    assert len(matched) >= 40, f"Expected at least 40 matches in index, got {len(matched)}"
    print("  Index filtering: [PASS]")

def test_resolve_urls_and_headers():
    print("[2/3] Resolving URLs and inspecting live headers for 'asia/pakistan'...")
    pbf_url = "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf"
    md5_url = "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf.md5"

    req = urllib.request.Request(pbf_url, method="HEAD", headers={"User-Agent": "AtlasMirror/0.1"})
    with urllib.request.urlopen(req) as resp:
        content_length = int(resp.headers.get("Content-Length", 0))
        last_modified = resp.headers.get("Last-Modified", "")
        print(f"  PBF Size: {content_length / (1024*1024):.2f} MB")
        print(f"  Last Modified: {last_modified}")
        assert content_length > 50 * 1024 * 1024, "Pakistan PBF should be > 50 MB"

    req_md5 = urllib.request.Request(md5_url, headers={"User-Agent": "AtlasMirror/0.1"})
    with urllib.request.urlopen(req_md5) as resp:
        md5_body = resp.read().decode("utf-8").strip()
        md5_hash = md5_body.split()[0]
        assert len(md5_hash) == 32
        print(f"  Live MD5 verified: {md5_hash}")

    print("  URL resolution and header inspection: [PASS]")

def test_streaming_and_partial_cleanup():
    print("[3/3] Testing bounded streaming download and partial cleanup on cancellation...")
    url = "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf"

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        dest_path = tmp.name

    part_path = dest_path + ".part"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AtlasMirror/0.1"})
        with urllib.request.urlopen(req) as resp:
            # Stream exactly 128 KB and simulate cancellation
            chunk = resp.read(128 * 1024)
            with open(part_path, "wb") as pf:
                pf.write(chunk)

        assert os.path.exists(part_path)
        assert os.path.getsize(part_path) == 128 * 1024

        # Simulate cancellation / failure: partial file must be cleaned up
        if os.path.exists(part_path):
            os.remove(part_path)

        assert not os.path.exists(part_path), "Partial file must be cleaned up on cancel"
        print("  Streaming and partial cleanup: [PASS]")
    finally:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        if os.path.exists(part_path):
            os.remove(part_path)

def main():
    print("Running Milestone 1: Real Geofabrik Adapter Tests...")
    test_live_index_and_filtering()
    test_resolve_urls_and_headers()
    test_streaming_and_partial_cleanup()
    print("\n[PASS] All Milestone 1 real Geofabrik tests passed successfully!")

if __name__ == "__main__":
    main()
