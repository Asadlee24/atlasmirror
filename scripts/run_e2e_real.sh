#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${REPO_ROOT}/scripts/standalone:/usr/local/bin:/usr/bin:/bin:${PATH}"
export LOGOS_MODULES_DIR="${REPO_ROOT}/modules"
export OSM_REGISTRY_PROGRAM_ID="bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f"

mkdir -p "${LOGOS_MODULES_DIR}/storage_module"
cd "${REPO_ROOT}"

python3 tests/integration/test_e2e_real.py
