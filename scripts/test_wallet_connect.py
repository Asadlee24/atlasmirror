import subprocess
import json

WALLET_DIR = "/tmp/atlasmirror_wallet"
CONFIG_CONTENT = {
    "sequencers": [{
        "sequencer_addr": "http://127.0.0.1:9000" 
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
        export LEE_WALLET_HOME_DIR='{WALLET_DIR}'
        echo "=== Checking wallet health ==="
        /usr/local/bin/wallet check-health || true
        
        echo "=== Listing accounts ==="
        echo 'atlasmirror' | /usr/local/bin/wallet account list || true
        """
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)

if __name__ == "__main__":
    main()
