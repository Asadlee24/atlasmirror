import subprocess
import json
import os

WALLET_DIR = "/tmp/atlasmirror_wallet"
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

def main():
    cmd = [
        "wsl", "-u", "root", "bash", "-c",
        f"""
        mkdir -p {WALLET_DIR}
        cat << 'EOF' > {WALLET_DIR}/wallet_config.json
{json.dumps(CONFIG_CONTENT, indent=4)}
EOF
        export LEE_WALLET_HOME_DIR="{WALLET_DIR}"
        
        # Initialize storage if not already initialized
        if [ ! -f "{WALLET_DIR}/persistent_storage.json" ]; then
            echo "Initializing wallet persistent storage..."
            echo "atlasmirror" | /usr/local/bin/wallet account list || true
        fi
        
        echo "Creating accounts..."
        header_raw=$(echo "atlasmirror" | /usr/local/bin/wallet account new public)
        echo "Header account output: $header_raw"
        
        # Create 4 segment accounts
        seg0=$(echo "atlasmirror" | /usr/local/bin/wallet account new public)
        seg1=$(echo "atlasmirror" | /usr/local/bin/wallet account new public)
        seg2=$(echo "atlasmirror" | /usr/local/bin/wallet account new public)
        seg3=$(echo "atlasmirror" | /usr/local/bin/wallet account new public)
        
        echo "=== ALL ACCOUNTS IN WALLET ==="
        echo "atlasmirror" | /usr/local/bin/wallet account list
        """
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)

if __name__ == "__main__":
    main()
