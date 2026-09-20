#!/bin/bash
set -e

export PATH='/root/.risc0/toolchains/v1.97.0-rust-x86_64-unknown-linux-gnu/bin:/root/.risc0/bin:/usr/local/bin:/usr/bin:/bin:$PATH'
export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible
mkdir -p "$LEE_WALLET_HOME_DIR"

WALLET_BIN=/root/lez-testnet-compatible/target/release/wallet

echo "=== 1. Initializing wallet and pointing to testnet ==="
printf "atlasmirror123\n" | $WALLET_BIN change-network testnet

echo "=== 2. Running check-health ==="
$WALLET_BIN check-health

echo "=== 3. Creating new public account ==="
ACC_OUTPUT=$($WALLET_BIN account new public)
echo "$ACC_OUTPUT"
PUB_ACC=$(echo "$ACC_OUTPUT" | grep -o 'Public/[A-Za-z0-9]*' | head -n 1)
echo "Created Public Account: $PUB_ACC"

echo "=== 4. Initializing account with auth-transfer init ==="
$WALLET_BIN auth-transfer init --account-id "$PUB_ACC" || true

echo "=== 5. Claiming Piñata faucet funds ==="
$WALLET_BIN pinata claim --to "$PUB_ACC"

echo "=== 6. Verifying balance ==="
$WALLET_BIN account get --account-id "$PUB_ACC"
