#!/bin/bash
set -e

export LEE_WALLET_HOME_DIR=/root/.lee/wallet-v021
mkdir -p "$LEE_WALLET_HOME_DIR"

echo "=== Initializing / Changing network to testnet ==="
printf "atlasmirror123\n" | /root/lez-v021/target/release/wallet change-network testnet

echo "=== Running check-health ==="
/root/lez-v021/target/release/wallet check-health
