import subprocess

target_id = "583309054"
target_pinata = "2062635772"

print(f"Searching for {target_id} and {target_pinata}...")

cmd = [
    "wsl.exe", "-d", "Ubuntu", "-u", "root", "--",
    "bash", "-c",
    f"cd /root/.cargo/git/checkouts/logos-execution-zone-6bae42d7c9cadfe7/47eba25 && git log -S {target_id} --oneline"
]
p = subprocess.run(cmd, capture_output=True, text=True)
print("Git log -S target_id:")
print(p.stdout)
print(p.stderr)

cmd2 = [
    "wsl.exe", "-d", "Ubuntu", "-u", "root", "--",
    "bash", "-c",
    f"cd /root/.cargo/git/checkouts/logos-execution-zone-6bae42d7c9cadfe7/47eba25 && git log -S {target_pinata} --oneline"
]
p2 = subprocess.run(cmd2, capture_output=True, text=True)
print("Git log -S target_pinata:")
print(p2.stdout)
print(p2.stderr)
