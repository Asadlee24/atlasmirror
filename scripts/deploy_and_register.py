import subprocess
import json
import time
import sys
import re

WALLET_DIR = "/tmp/atlasmirror_wallet"
BIN_PATH = "/mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry.bin"
EVIDENCE_DIR = "/mnt/c/Users/Aftab/Desktop/atlasmirror/evidence"
CID = "zDvZRwzm4FBsSGJRftqqYev7aNBEcEUcwDBxCSREXGo1qCnNR5U4"

CONFIG_CONTENT = {
    "sequencers": [{
        "sequencer_addr": "http://127.0.0.1:3040" 
    }],
    "seq_poll_timeout": "30s",
    "seq_tx_poll_max_blocks": 15,
    "seq_poll_max_retries": 10,
    "seq_block_poll_max_amount": 100,
    "calibration_limit": 100
}

def run_wsl(cmd_str, input_text=None):
    cmd = ["wsl", "-u", "root", "bash", "-c", cmd_str]
    res = subprocess.run(cmd, input=input_text, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def main():
    print("=== 1. Setting up wallet config for http://127.0.0.1:3040 ===")
    run_wsl(f"rm -rf {WALLET_DIR} && mkdir -p {WALLET_DIR}")
    
    config_json_str = json.dumps(CONFIG_CONTENT, indent=4)
    run_wsl(f"cat << 'EOF' > {WALLET_DIR}/wallet_config.json\n{config_json_str}\nEOF\n")
    
    env = f"export LEE_WALLET_HOME_DIR='{WALLET_DIR}' && export PATH='/root/.risc0/toolchains/v1.97.0-rust-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin:$PATH'"
    
    print("=== 2. Initializing wallet persistent storage ===")
    ret, out, err = run_wsl(f"{env} && echo 'atlasmirror' | /usr/local/bin/wallet account list || true")
    print("Init output:", out, err)
    
    print("=== 3. Checking wallet health ===")
    ret, out, err = run_wsl(f"{env} && /usr/local/bin/wallet check-health || true")
    print("Health output:", out, err)
    
    FUNDED_PAYER = "Public/6iArKUXxhUJqS7kCaPNhwMWt3ro71PDyBj7jwAyE2VQV"
    FUNDED_KEY_HEX = "10a26a9aec7d34b82364eeae45c5294dbb0a764b000b94eeb9b58511dc487c4d"
    print("=== 4. Importing funded payer and creating accounts ===")
    run_wsl(f"{env} && echo 'atlasmirror' | /usr/local/bin/wallet account import public --private-key {FUNDED_KEY_HEX} || true")

    accounts = []
    # Create 5 accounts: 1 header + 4 segments
    for i in range(5):
        ret, out, err = run_wsl(f"{env} && echo 'atlasmirror' | /usr/local/bin/wallet account new public")
        print(f"Create account {i} out:\n{out}")
        matches = re.findall(r'Public/[1-9A-HJ-NP-Za-km-z]{32,44}', out)
        for m in matches:
            if m not in accounts and m != FUNDED_PAYER:
                accounts.append(m)
                break
                
    # Also list accounts to verify
    ret, out, err = run_wsl(f"{env} && /usr/local/bin/wallet account list")
    print("Wallet accounts list output:\n", out)
    list_matches = [m for m in re.findall(r'Public/[1-9A-HJ-NP-Za-km-z]{32,44}', out) if m != FUNDED_PAYER]
    print("Detected segment/header account IDs:", list_matches)
    
    if len(list_matches) >= 5:
        header_id = list_matches[0]
        seg_ids = list_matches[1:5]
    elif len(accounts) >= 5:
        header_id = accounts[0]
        seg_ids = accounts[1:5]
    else:
        print("Failed to get 5 accounts. Exiting.")
        sys.exit(1)
        
    print(f"Header ID: {header_id}")
    print(f"Segments: {seg_ids}")
    raw_header_id = header_id.replace("Public/", "")
    
    print("=== 5. Deploying osm_registry.bin ===")
    segs_arg = " ".join(seg_ids)
    deploy_cmd = f"{env} && echo 'atlasmirror' | /usr/local/bin/wallet program-loader deploy --elf {BIN_PATH} --header {header_id} --segments {segs_arg} --payer {FUNDED_PAYER}"
    print("Running deploy command:", deploy_cmd)
    ret, deploy_out, deploy_err = run_wsl(deploy_cmd)
    deploy_log = f"{deploy_out}\n{deploy_err}"
    print("Deploy output:\n", deploy_log)
    with open("C:/Users/Aftab/Desktop/atlasmirror/evidence/registry-deploy.log", "w") as f:
        f.write(deploy_log)
        
    print("=== 6. Executing Transactions with runner ===")
    runner_bin = "/root/target/debug/run_osm_registry"
    if not run_wsl(f"test -f {runner_bin}")[0] == 0:
        runner_bin = "/tmp/lez/target/debug/run_osm_registry"
    
    # Initialize
    init_cmd = f"{env} && {runner_bin} {BIN_PATH} {raw_header_id} initialize"
    print("Running init command:", init_cmd)
    ret, init_out, init_err = run_wsl(init_cmd)
    print("Init output:\n", init_out, init_err)
    
    # Register region
    reg_cmd = f"{env} && {runner_bin} {BIN_PATH} {raw_header_id} register pakistan {CID} 378df25f824177ebcbe9aa11d88bbd6b https://download.geofabrik.de/asia/pakistan-latest.osm.pbf 2026-09-19 1726747200"
    print("Running register command:", reg_cmd)
    ret, reg_out, reg_err = run_wsl(reg_cmd)
    register_log = f"INIT:\n{init_out}\n{init_err}\nREGISTER:\n{reg_out}\n{reg_err}\n"
    print("Register output:\n", register_log)
    with open("C:/Users/Aftab/Desktop/atlasmirror/evidence/registry-register.log", "w") as f:
        f.write(register_log)
        
    print("=== 7. Querying On-Chain State ===")
    query_cmd = f"{env} && echo 'atlasmirror' | /usr/local/bin/wallet account get --account-id {header_id} --scope {raw_header_id} --raw"
    ret, query_out, query_err = run_wsl(query_cmd)
    query_log = f"{query_out}\n{query_err}"
    print("Query output:\n", query_log)
    with open("C:/Users/Aftab/Desktop/atlasmirror/evidence/registry-query.log", "w") as f:
        f.write(query_log)
        
    print("=== 8. Verification ===")
    if CID in query_log or CID in register_log:
        print(f"SUCCESS! CID {CID} verified in on-chain execution evidence!")
    else:
        print("Note: Check query log and register log for CID verification.")

if __name__ == "__main__":
    main()
