#!/usr/bin/env python3
"""
Integration Test: Real End-to-End PBF Pipeline Orchestration
Reference: tests/integration/e2e_real.sh
Orchestration:
1. Live Geofabrik PBF download for smallest practical region (china/henan, 46.86 MB)
2. Live published MD5 fetch & exact equality assertion
3. logoscore call storage_module uploadUrl -> captures genuine CID
4. spel CLI on-chain register-region transaction on LEZ sequencer -> captures genuine TX ID
5. spel inspect on-chain state query
6. logoscore call storage_module downloadToUrl
7. Exact SHA-256 byte-for-byte equality verification

NO FAKE REST APIS.
If logoscore, storage_module, or spel is absent, reports BLOCKED and exits with code 2.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def test_real_e2e():
    print("========================================================")
    print(" AtlasMirror Real End-to-End PBF Pipeline Preflight")
    print("========================================================")

    logoscore_bin = shutil.which("logoscore")
    spel_bin = shutil.which("spel") or shutil.which("spel-cli")
    modules_dir = Path(os.environ.get("LOGOS_MODULES_DIR", "./modules"))
    storage_mod = (modules_dir / "storage_module").exists() or (modules_dir / "storage_module.lgx").exists()
    program_id = os.environ.get("OSM_REGISTRY_PROGRAM_ID")

    print(f"  logoscore:       {'PRESENT' if logoscore_bin else 'UNAVAILABLE'}")
    print(f"  storage_module:  {'PRESENT' if storage_mod else 'UNAVAILABLE'}")
    print(f"  spel CLI:        {'PRESENT' if spel_bin else 'UNAVAILABLE'}")
    print(f"  OSM Program ID:  {program_id if program_id else 'NOT SET'}")

    if not logoscore_bin or not storage_mod or not spel_bin or not program_id:
        print("\n[CRITICAL FAILURE] Required Logos infrastructure is NOT running.")
        if not logoscore_bin:
            print("  - 'logoscore' daemon executable must be in PATH.")
        if not storage_mod:
            print(f"  - 'storage_module' plugin must be built in {modules_dir}.")
        if not spel_bin:
            print("  - 'spel' CLI must be installed from https://github.com/logos-co/spel.")
        if not program_id:
            print("  - OSM_REGISTRY_PROGRAM_ID must be set (deploy program first via make -C osm-registry deploy).")
        print("\nUnder LP-0018 rules, simulated fallbacks and mock servers are FORBIDDEN.")
        print("Integration Status: NOT_VERIFIED")
        sys.exit(2)

    # Execute genuine orchestration bash script
    res = subprocess.run(["bash", "tests/integration/e2e_real.sh"], capture_output=False)
    sys.exit(res.returncode)

if __name__ == "__main__":
    test_real_e2e()
