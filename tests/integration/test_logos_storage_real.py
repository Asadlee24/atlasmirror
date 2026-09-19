#!/usr/bin/env python3
"""
Integration Test: Real Logos Storage via logoscore and storage_module
Reference: logos-co/logos-storage-module doctests/storage-module-runtime.test.yaml
Architecture: logoscore CLI -> storage_module -> uploadUrl -> storageUploadDone -> downloadToUrl

This test NEVER connects to fake HTTP endpoints (/api/v0/storage/...) or mock servers.
If logoscore or storage_module is absent, it reports BLOCKED and exits with code 2.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def test_logoscore_storage():
    print("Checking for logoscore executable...")
    logoscore_bin = shutil.which("logoscore")
    if not logoscore_bin:
        print("\n[BLOCKED] 'logoscore' executable not found in PATH.")
        print("To run this test:")
        print("  1. Build logoscore and ensure it is in PATH.")
        print("  2. Build storage_module from https://github.com/logos-co/logos-storage-module")
        print("  3. Run: bash tests/integration/storage_real.sh")
        print("\nIntegration Status: NOT_VERIFIED (logoscore absent)")
        sys.exit(2)

    modules_dir = Path(os.environ.get("LOGOS_MODULES_DIR", "./modules"))
    storage_mod = modules_dir / "storage_module"
    storage_lgx = modules_dir / "storage_module.lgx"
    if not storage_mod.exists() and not storage_lgx.exists():
        print(f"\n[BLOCKED] storage_module not found in {modules_dir}.")
        print("Integration Status: NOT_VERIFIED (storage_module absent)")
        sys.exit(2)

    # If logoscore and storage_module are present, execute bash test
    res = subprocess.run(["bash", "tests/integration/storage_real.sh"], capture_output=False)
    sys.exit(res.returncode)

if __name__ == "__main__":
    test_logoscore_storage()
