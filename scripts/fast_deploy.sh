#!/bin/bash
set -e

export PATH='/root/.risc0/toolchains/v1.97.0-rust-x86_64-unknown-linux-gnu/bin:/root/.risc0/bin:/usr/local/bin:/usr/bin:/bin:$PATH'
export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible
mkdir -p "$LEE_WALLET_HOME_DIR"

WALLET=/root/lez-testnet-compatible/target/release/wallet
ELF_PATH=/mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry

echo "=================================================="
echo "STEP 1: Initializing fresh wallet with testnet"
echo "=================================================="
printf "atlasmirror123\n" | $WALLET change-network testnet

echo "=================================================="
echo "STEP 2: Running check-health"
echo "=================================================="
$WALLET check-health

echo "=================================================="
echo "STEP 3: Creating public account"
echo "=================================================="
ACC_OUT=$($WALLET account new public)
echo "$ACC_OUT"
PUB_ACC=$(echo "$ACC_OUT" | grep -o 'Public/[A-Za-z0-9]*' | head -n 1)
echo "Designated Public Account: $PUB_ACC"

echo "=================================================="
echo "STEP 4: Initializing account with auth-transfer"
echo "=================================================="
$WALLET auth-transfer init --account-id "$PUB_ACC" || true

echo "=================================================="
echo "STEP 5: Claiming Piñata faucet tokens"
echo "=================================================="
$WALLET pinata claim --to "$PUB_ACC"

echo "=================================================="
echo "STEP 6: Verifying account balance"
echo "=================================================="
$WALLET account get --account-id "$PUB_ACC"

echo "=================================================="
echo "STEP 7: Deploying osm_registry to Testnet"
echo "=================================================="
DEPLOY_OUT=$($WALLET deploy-program "$ELF_PATH")
echo "$DEPLOY_OUT"

echo "=================================================="
echo "DEPLOYMENT COMPLETE!"
echo "=================================================="
