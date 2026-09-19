import subprocess
import time
import sys

def main():
    cmd = [
        "wsl", "-u", "root", "bash", "-c",
        """
        pkill -f mock_bedrock || true
        killall -9 sequencer_service 2>/dev/null || true
        
        nohup python3 /mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/mock_bedrock.py > /tmp/bedrock.log 2>&1 &
        sleep 1
        
        export RUST_LOG=info
        export RUST_BACKTRACE=1
        /usr/local/bin/sequencer_service /tmp/lez/lez/sequencer/service/configs/debug/sequencer_config.json
        """
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait up to 10 seconds to capture output
    time.sleep(6)
    
    # Check if process is still running
    poll = proc.poll()
    if poll is None:
        print("Sequencer is RUNNING actively!")
        # Check listening ports
        chk = subprocess.run(["wsl", "bash", "-c", "ss -tulpn | grep -E '3040|9000|sequencer'"], capture_output=True, text=True)
        print("PORTS:\n", chk.stdout)
    else:
        out, err = proc.communicate()
        print(f"Sequencer exited with code {poll}!")
        print("STDOUT:\n", out)
        print("STDERR:\n", err)

if __name__ == "__main__":
    main()
