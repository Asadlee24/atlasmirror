#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="/usr/local/bin:${PATH}"
export LOGOS_MODULES_DIR="${REPO_ROOT}/modules"
export OSM_REGISTRY_PROGRAM_ID="bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f"
export LEE_WALLET_HOME_DIR="${LEE_WALLET_HOME_DIR:-${HOME}/.lee/wallet}"

# Ensure genuine binaries are installed if not present
if ! command -v logoscore >/dev/null 2>&1 || ! command -v spel >/dev/null 2>&1 || [ ! -d "${LOGOS_MODULES_DIR}/storage_module" ]; then
    bash "${REPO_ROOT}/scripts/setup_ci_environment.sh" /usr/local/bin "${LOGOS_MODULES_DIR}"
fi

cd "${REPO_ROOT}"
python3 tests/integration/test_e2e_real.py
