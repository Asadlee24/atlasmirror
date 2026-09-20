import urllib.request
import json
import subprocess

# Download authenticated_transfer.bin from v0.2.1
url = "https://raw.githubusercontent.com/logos-blockchain/logos-execution-zone/v0.2.1/artifacts/lez/programs/authenticated_transfer.bin"
data = urllib.request.urlopen(url).read()
with open("authenticated_transfer_v021.bin", "wb") as f:
    f.write(data)
print(f"Downloaded v0.2.1 authenticated_transfer.bin: {len(data)} bytes")

# Also let's check r0vm image-id or risc0 image id using WSL
cmd = ["wsl.exe", "-d", "Ubuntu", "-u", "root", "--", "r0vm", "image-id", "--elf", "/mnt/c/Users/Aftab/Desktop/atlasmirror/authenticated_transfer_v021.bin"]
p = subprocess.run(cmd, capture_output=True, text=True)
print("r0vm image-id stdout:", p.stdout)
print("r0vm image-id stderr:", p.stderr)
