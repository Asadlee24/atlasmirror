import subprocess
import json
import time
import sys
import os

WALLET_DIR = "/tmp/atlasmirror_wallet"
BIN_PATH = "/mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry.bin"
EVIDENCE_DIR = "/mnt/c/Users/Aftab/Desktop/atlasmirror/evidence"

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

def run_wsl(cmd_str):
    cmd = ["wsl", "-u", "root", "bash", "-c", cmd_str]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

def main():
    print("=== 1. Checking sequencer_service binary ===")
    ret, out, err = run_wsl("test -f /tmp/lez/bin-sequencer/bin/sequencer_service && echo 'EXISTS'")
    if "EXISTS" not in out:
        print("Sequencer binary not yet built. Waiting for task-1156 to finish.")
        sys.exit(1)
        
    print("Copying sequencer_service to /usr/local/bin...")
    run_wsl("cp /tmp/lez/bin-sequencer/bin/sequencer_service /usr/local/bin/sequencer_service && chmod +x /usr/local/bin/sequencer_service")
    
    print("=== 2. Cleaning old state ===")
    run_wsl("killall -9 sequencer_service 2>/dev/null || true")
    run_wsl("rm -rf /tmp/sequencer_db /tmp/rocksdb /tmp/lez_db /tmp/atlasmirror_wallet")
    run_wsl(f"mkdir -p {WALLET_DIR}")
    
    with open("C:/Users/Aftab/Desktop/atlasmirror/scripts/temp_wallet_config.json", "w") as f:
        json.dump(CONFIG_CONTENT, f, indent=4)
    run_wsl(f"cp /mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/temp_wallet_config.json {WALLET_DIR}/wallet_config.json")
    
    print("=== 3. Starting LEZ sequencer_service ===")
    run_wsl(f"RUST_LOG=info /usr/local/bin/sequencer_service /tmp/lez/lez/sequencer/service/configs/debug/sequencer_config.json > {EVIDENCE_DIR}/lez-start.log 2>&1 &")
    
    # Wait for sequencer to be healthy
    print("Waiting for sequencer to be healthy at http://127.0.0.1:3040...")
    healthy = False
    for _ in range(30):
        time.sleep(1)
        ret, out, _ = run_wsl("curl -s http://127.0.0.1:3040/health || true")
        if ret == 0 and len(out.strip()) > 0:
            print(f"Sequencer is responding: {out.strip()}")
            healthy = True
            break
            
    if not healthy:
        print("Sequencer did not become healthy within 30s. Check evidence/lez-start.log")
        _, log, _ = run_wsl(f"cat {EVIDENCE_DIR}/lez-start.log")
        print("LOG:", log)
        sys.exit(1)
        
    print("=== 4. Initializing wallet ===")
    wallet_pass = os.environ.get("WALLET_PASSWORD", "")
    env = f"export LEE_WALLET_HOME_DIR='{WALLET_DIR}'"
    run_wsl(f"{env} && echo '{wallet_pass}' | /usr/local/bin/wallet account list || true")
    
    print("=== 5. Creating 1 Header + 4 Segment Accounts ===")
    accounts = []
    for i in range(5):
        ret, out, err = run_wsl(f"{env} && echo '{wallet_pass}' | /usr/local/bin/wallet account new public")
        # Find 32-byte base58 account id from output
        # Output usually contains account id
        print(f"Account {i} output: {out}")
        for line in out.splitlines():
            if "Public/" in line or len(line.strip()) == 44 or "Generated" in line:
                print(f"  Line: {line}")
                
    # List all accounts to capture exact IDs
    ret, out, err = run_wsl(f"{env} && /usr/local/bin/wallet account list")
    print("Wallet accounts list:\n", out)
    
if __name__ == "__main__":
    main()
