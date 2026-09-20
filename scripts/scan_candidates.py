import urllib.request
import subprocess
import json
import os
import sys

TARGETS = {
    "authenticated_transfer": [583309054, 2344528779, 3806558405, 2890696795, 2257354672, 3978764116, 2273929063, 1518858078],
    "token": [1047643340, 4291649067, 2093396023, 4016657193, 3904308476, 481382041, 2987082047, 2603530278],
    "pinata": [2062635772, 3904239712, 2833328350, 20714435, 436307236, 2247732790, 2681611470, 2354246644]
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "target", "artifact_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

COMPUTE_ID_BIN = "/root/lez-v021/target/release/compute_id"

def get_image_id_wsl(bin_path):
    # Convert windows path to wsl path
    wsl_path = bin_path.replace("\\", "/").replace("C:", "/mnt/c")
    cmd = ["wsl", "-u", "root", COMPUTE_ID_BIN, wsl_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout.strip()
    if out.startswith("[") and out.endswith("]"):
        return json.loads(out)
    return None

def check_ref(ref_name, ref_type="ref"):
    print(f"\n--- Checking {ref_name} ---", flush=True)
    matched_all = True
    results = {}
    for prog in ["authenticated_transfer", "token", "pinata"]:
        url = f"https://raw.githubusercontent.com/logos-blockchain/logos-execution-zone/{ref_name}/artifacts/lez/programs/{prog}.bin"
        cached_file = os.path.join(CACHE_DIR, f"{ref_name.replace('/', '_')}_{prog}.bin")
        if not os.path.exists(cached_file):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                data = urllib.request.urlopen(req).read()
                with open(cached_file, "wb") as f:
                    f.write(data)
            except Exception as e:
                print(f"  {prog}: Failed to download ({e})", flush=True)
                matched_all = False
                continue

        img_id = get_image_id_wsl(cached_file)
        results[prog] = img_id
        if img_id == TARGETS[prog]:
            print(f"  {prog}: MATCH! {img_id}", flush=True)
        else:
            print(f"  {prog}: NO MATCH (computed: {img_id})", flush=True)
            matched_all = False

    if matched_all:
        print(f"\n>>> EXACT 3/3 MATCH FOUND FOR {ref_name}! <<<", flush=True)
        return True
    return False

# Candidate refs: tags and intermediate commits
CANDIDATES = [
    "v0.2.0-rc6",
    "v0.2.0",
    "v0.2.1",
    "v0.2.2-rc1",
    "v0.2.2",
    "v0.2.3",
    "v0.2.4",
    # Intermediate commits touching artifacts between v0.2.1 and v0.2.5
    "c9a7ede209",
    "765de8de03",
    "449e9e366c",
    "483821967d",
    "cb24da6e4d",
    "096312547b",
    "dad565945e",
    "7b06525f97",
    "d7a143d26c",
    "39b3018058",
    "96c8577db8",
    "72782beb34",
    "2ba1ecd609",
    "d52c76e2b5",
    "7b6b439eb2",
    "2a7a586a59",
    "a6aa5ff358",
    "be81184028",
    "17b49f5a94"
]

for cand in CANDIDATES:
    if check_ref(cand):
        sys.exit(0)

print("\nFinished checking candidate refs. No exact match found.", flush=True)
