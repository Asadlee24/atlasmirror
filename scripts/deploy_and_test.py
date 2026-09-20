#!/usr/bin/env python3
import subprocess
import sys
import time

LD_PREFIX = "/nix/store/776irwlgfb65a782cxmyk61pck460fs9-glibc-2.40-66/lib/ld-linux-x86-64.so.2 --library-path /nix/store/776irwlgfb65a782cxmyk61pck460fs9-glibc-2.40-66/lib:/usr/lib/x86_64-linux-gnu"
WALLET_BIN = "/root/lez-testnet-compatible/target/release/wallet"
RUNNER_BIN = "/root/lez-testnet-compatible/target/release/run_osm_registry"
WRAP_BIN = "/root/lez-testnet-compatible/target/release/wrap_elf"

ELF_PATH = "/mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry"
BIN_PATH = "/mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry.bin"
STATE_ACCOUNT = "4CSAM4M1GtrF1tGMJmnCaipbkHH3kYjsMNmWYs6jJHJQ"

def run_wsl(cmd_str):
    print(f"\n[RUNNING] {cmd_str}")
    full_cmd = ["bash", "-c", cmd_str]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("[STDERR]", res.stderr, file=sys.stderr)
    if res.returncode != 0:
        print(f"[ERROR] Command failed with code {res.returncode}")
        sys.exit(res.returncode)
    return res.stdout

def main():
    print("=== Step 1: Wrap ELF into ProgramBinary ===")
    wrap_cmd = f"{LD_PREFIX} {WRAP_BIN} {ELF_PATH} {BIN_PATH}"
    run_wsl(wrap_cmd)

    print("\n=== Step 2: Deploy Program to Logos Testnet ===")
    deploy_cmd = f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && {LD_PREFIX} {WALLET_BIN} deploy-program {BIN_PATH}"
    deploy_out = run_wsl(deploy_cmd)

    print("\n=== Step 3: Register Region on Testnet ===")
    reg_cmd = (
        f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && "
        f"{LD_PREFIX} {RUNNER_BIN} {BIN_PATH} {STATE_ACCOUNT} register china/henan "
        f"zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4 378df25f824177ebcbe9aa11d88bbd6b "
        f"https://download.geofabrik.de/asia/china/henan-latest.osm.pbf 2026-09-19 1726747200"
    )
    reg_out = run_wsl(reg_cmd)

    print("\n=== Step 4: Query Account State ===")
    query_cmd = (
        f"export LEE_WALLET_HOME_DIR=/root/.lee/wallet-testnet-compatible && "
        f"{LD_PREFIX} {RUNNER_BIN} {BIN_PATH} {STATE_ACCOUNT} query"
    )
    query_out = run_wsl(query_cmd)

    print("\n=== SUCCESS: All steps completed! ===")

if __name__ == "__main__":
    main()
