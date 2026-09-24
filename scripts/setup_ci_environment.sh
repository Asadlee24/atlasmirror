#!/usr/bin/env bash
set -euo pipefail

echo "========================================================"
echo " Setting up Official Logos & LEZ Infrastructure"
echo "========================================================"

INSTALL_DIR="${1:-/usr/local/bin}"
MODULES_DIR="${2:-$(pwd)/modules}"

mkdir -p "${INSTALL_DIR}"
mkdir -p "${MODULES_DIR}/storage_module"
TMP_SETUP=$(mktemp -d /tmp/ci-setup.XXXXXX)
trap 'rm -rf "${TMP_SETUP}"' EXIT

# Install system dependencies
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo apt-get install -y -qq libpcsclite1 || true
fi

# 1. Download official sequencer_service, wallet, and spel
echo "==> Downloading official LEZ sequencer, wallet, and spel..."
curl -sSfL -o "${TMP_SETUP}/ci_bin.tar.gz" "https://github.com/Asadlee24/atlasmirror/releases/download/v0.1.0-e2e-tools/ci_bin.tar.gz"
tar -xzf "${TMP_SETUP}/ci_bin.tar.gz" -C "${TMP_SETUP}"
cp "${TMP_SETUP}/ci_bin/sequencer_service" "${INSTALL_DIR}/"
cp "${TMP_SETUP}/ci_bin/wallet" "${INSTALL_DIR}/"
cp "${TMP_SETUP}/ci_bin/spel" "${INSTALL_DIR}/"
chmod +x "${INSTALL_DIR}/sequencer_service" "${INSTALL_DIR}/wallet" "${INSTALL_DIR}/spel"

# 2. Download official logoscore
echo "==> Downloading official logoscore AppImage..."
curl -sSfL -o "${TMP_SETUP}/logoscore.tar.gz" "https://github.com/logos-co/logos-logoscore-cli/releases/download/0.2.0/logoscore-x86_64-linux.tar.gz"
tar -xzf "${TMP_SETUP}/logoscore.tar.gz" -C "${TMP_SETUP}"
cd "${TMP_SETUP}"
chmod +x ./logoscore-x86_64.AppImage
./logoscore-x86_64.AppImage --appimage-extract >/dev/null 2>&1
mkdir -p /opt/logoscore
cp -r squashfs-root/* /opt/logoscore/
chmod +x /opt/logoscore/AppRun
ln -sf /opt/logoscore/AppRun "${INSTALL_DIR}/logoscore"

# 3. Download official storage_module
echo "==> Downloading official storage_module..."
curl -sSfL -o "${TMP_SETUP}/storage_module.lgx" "https://github.com/logos-co/logos-modules-release/releases/download/storage_module-v2.1.3/storage_module-2.1.3.lgx"
tar -xf "${TMP_SETUP}/storage_module.lgx" -C "${MODULES_DIR}/storage_module"
cp "${MODULES_DIR}/storage_module/variants/linux-amd64/"* "${MODULES_DIR}/storage_module/"
printf "linux-amd64" > "${MODULES_DIR}/storage_module/variant"

# 4. Set up preconfigured CI wallet
WALLET_HOME="${HOME}/.lee/wallet"
mkdir -p "${WALLET_HOME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/ci_wallet.tar.gz" ]; then
    tar -xzf "${SCRIPT_DIR}/ci_wallet.tar.gz" -C "${WALLET_HOME}"
fi

cat > "${WALLET_HOME}/wallet_config.json" <<EOF
{
  "sequencers": [
    {
      "sequencer_addr": "https://testnet.lez.logos.co/"
    }
  ],
  "seq_poll_timeout": "120s",
  "seq_tx_poll_max_blocks": 60,
  "seq_poll_max_retries": 30,
  "seq_block_poll_max_amount": 100,
  "multi_sequencer_client_config": {
    "distribution_limit": 1,
    "calibration_limit": 100
  }
}
EOF

echo "========================================================"
echo " Infrastructure setup complete:"
echo "   logoscore:         $(which logoscore)"
echo "   spel:              $(which spel)"
echo "   sequencer_service: $(which sequencer_service)"
echo "   wallet:            $(which wallet)"
echo "   storage_module:    ${MODULES_DIR}/storage_module"
echo "========================================================"
