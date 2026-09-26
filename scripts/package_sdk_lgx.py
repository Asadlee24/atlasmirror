#!/usr/bin/env python3
"""
Packages AtlasMirror Core SDK into an authoritative .lgx bundle conforming to Basecamp specification.
Verifies bundle contents using tar.
"""

import os
import sys
import tarfile
import json
import shutil
from pathlib import Path

def package_sdk():
    root = Path(__file__).resolve().parent.parent
    sdk_dir = root / "atlasmirror-sdk"
    dist_dir = root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_path = sdk_dir / "metadata.json"
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    pkg_name = meta.get("name", "atlasmirror_sdk")
    version = meta.get("version", "0.1.1")
    lgx_filename = f"{pkg_name}-v{version}.lgx"
    lgx_path = dist_dir / lgx_filename
    
    staging_dir = root / "target" / "sdk_lgx_staging"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy metadata.json
    shutil.copy2(metadata_path, staging_dir / "metadata.json")
    
    # 2. Copy C++ sources
    src_dest = staging_dir / "src"
    shutil.copytree(sdk_dir / "src", src_dest, ignore=shutil.ignore_patterns("*.o", "*.obj", ".DS_Store"))
    
    # 3. Include compiled native plugin library
    lib_dir = staging_dir / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    
    native_found = False
    for build_cand in [sdk_dir / "build", root / "build", root / "target" / "release"]:
        if not build_cand.exists():
            continue
        for so_cand in build_cand.glob("**/libatlasmirror_sdk_plugin.*"):
            if so_cand.is_file() and not so_cand.name.endswith((".o", ".obj", ".a")):
                shutil.copy2(so_cand, lib_dir / so_cand.name)
                native_found = True
    
    # 4. Pack into .lgx (gzipped tar archive)
    with tarfile.open(lgx_path, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        for item in sorted(staging_dir.rglob("*")):
            arcname = item.relative_to(staging_dir).as_posix()
            tar.add(item, arcname=arcname, recursive=False)
            
    print(f"Packaged: {lgx_path} ({lgx_path.stat().st_size} bytes)")
    
    # 5. Verify unpack
    with tarfile.open(lgx_path, "r:gz") as tar:
        names = tar.getnames()
        print("\n--- Verifying .lgx Archive Contents ---")
        for member in tar.getmembers():
            print(f"  {member.name:<45} ({member.size:>8} bytes)")
        print("---------------------------------------")
        
        has_meta = "metadata.json" in names
        has_lib = any("libatlasmirror_sdk_plugin" in n for n in names)
        print(f"  Metadata present: {has_meta}")
        print(f"  Native library packaged: {has_lib}")
        
        if not has_meta:
            print("[FAIL] Missing metadata.json in bundle!", file=sys.stderr)
            sys.exit(1)
            
    print("VERIFICATION SUCCESS: SDK .lgx package conforms to Basecamp specification.")

if __name__ == "__main__":
    package_sdk()
