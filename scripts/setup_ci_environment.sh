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

echo "========================================================"
echo " Infrastructure setup complete:"
echo "   logoscore:         $(which logoscore)"
echo "   spel:              $(which spel)"
echo "   sequencer_service: $(which sequencer_service)"
echo "   wallet:            $(which wallet)"
echo "   storage_module:    ${MODULES_DIR}/storage_module"
echo "========================================================"
