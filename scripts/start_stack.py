import subprocess
import time

def main():
    cmd = [
        "wsl", "-u", "root", "bash", "-c",
        """
        killall -9 sequencer_service 2>/dev/null || true
        pkill -f mock_bedrock || true
        nohup python3 /mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/mock_bedrock.py > /tmp/bedrock.log 2>&1 &
        sleep 1
        export RUST_LOG=info
        nohup /usr/local/bin/sequencer_service /tmp/lez/lez/sequencer/service/configs/debug/sequencer_config.json > /tmp/sequencer.log 2>&1 &
        sleep 3
        cat /tmp/sequencer.log
        """
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)

if __name__ == "__main__":
    main()
