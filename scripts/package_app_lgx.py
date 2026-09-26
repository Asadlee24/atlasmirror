#!/usr/bin/env python3
"""
Packages AtlasMirror Basecamp QML App into an authoritative .lgx bundle conforming to Basecamp specification.
Verifies bundle contents using tar to prove native backend inclusion.
"""

import os
import sys
import tarfile
import json
import shutil
from pathlib import Path

def package_app():
    root = Path(__file__).resolve().parent.parent
    app_dir = root / "atlasmirror-app"
    dist_dir = root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_path = app_dir / "metadata.json"
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    pkg_name = meta.get("name", "atlasmirror_app")
    version = meta.get("version", "0.1.1")
    lgx_filename = f"{pkg_name}-v{version}.lgx"
    lgx_path = dist_dir / lgx_filename
    
    staging_dir = root / "target" / "lgx_staging"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy metadata.json
    shutil.copy2(metadata_path, staging_dir / "metadata.json")
    
    # 2. Copy QML and icon sources
    src_dest = staging_dir / "src"
    shutil.copytree(app_dir / "src", src_dest, ignore=shutil.ignore_patterns("*.o", "*.obj", ".DS_Store"))
    
    # 3. Include compiled native backend library/binary placeholder / stub / built binary
    lib_dir = staging_dir / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    bin_dir = staging_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    backend_lib = lib_dir / "libatlasmirror_app_backend.so"
    # If a real build artifact exists in build dirs, copy it
    native_found = False
    for build_cand in [root / "build", app_dir / "build", root / "target" / "release"]:
        if not build_cand.exists():
            continue
        for so_cand in build_cand.glob("**/libatlasmirror_app_*.*"):
            if so_cand.is_file() and not so_cand.name.endswith((".o", ".obj", ".a")):
                shutil.copy2(so_cand, lib_dir / so_cand.name)
                native_found = True
        for bin_cand in build_cand.glob("**/atlasmirror-app*"):
            if bin_cand.is_file() and not bin_cand.name.endswith((".cpp", ".h", ".o", ".obj", ".dir", ".make", ".cmake")):
                shutil.copy2(bin_cand, bin_dir / bin_cand.name)
                native_found = True
                
    if not native_found:
        raise RuntimeError(
            "Native backend binaries (libatlasmirror_app_backend, libatlasmirror_app_plugin, atlasmirror-app) "
            "must be compiled before packaging .lgx bundle!"
        )
            
    # 4. Create uncompressed/gzipped tar archive as .lgx
    with tarfile.open(lgx_path, "w:gz") as tar:
        for item in sorted(staging_dir.iterdir()):
            tar.add(item, arcname=item.name)
            
    print(f"Packaged: {lgx_path} ({lgx_path.stat().st_size} bytes)")
    
    # 5. Unpack and audit proof
    print("\n--- Verifying .lgx Archive Contents ---")
    with tarfile.open(lgx_path, "r:gz") as tar:
        members = tar.getmembers()
        has_metadata = False
        has_native = False
        has_qml = False
        for m in members:
            print(f"  {m.name:<45} ({m.size:>8} bytes)")
            if m.name == "metadata.json":
                has_metadata = True
            if "libatlasmirror_app_" in m.name or "atlasmirror-app" in m.name:
                has_native = True
            if m.name.endswith(".qml"):
                has_qml = True
                
        print("---------------------------------------")
        print(f"  Metadata present: {has_metadata}")
        print(f"  Native backend packaged: {has_native}")
        print(f"  QML views packaged: {has_qml}")
        
        assert has_metadata, "Missing metadata.json"
        assert has_native, "Missing packaged native backend in lib/ or bin/"
        assert has_qml, "Missing QML views"
        print("VERIFICATION SUCCESS: .lgx package conforms to Basecamp specification.")

if __name__ == "__main__":
    package_app()
