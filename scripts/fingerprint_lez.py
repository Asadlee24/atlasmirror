import urllib.request
import json
import time

TARGET_IDS = {
    "authenticated_transfer": [583309054, 2344528779, 3806558405, 2890696795, 2257354672, 3978764116, 2273929063, 1518858078],
    "token": [1047643340, 4291649067, 2093396023, 4016657193, 3904308476, 481382041, 2987082047, 2603530278],
    "pinata": [2062635772, 3904239712, 2833328350, 20714435, 436307236, 2247732790, 2681611470, 2354246644]
}

def gh_api(path):
    url = f"https://api.github.com/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"API Error for {path}: {e}")
        return None

print("=== Phase 1: Inspecting candidate tags in logos-execution-zone ===")
tags_to_check = [
    "v0.2.0-rc1", "v0.2.0-rc2", "v0.2.0-rc3", "v0.2.0-rc4", "v0.2.0-rc5", "v0.2.0-rc6",
    "v0.2.0", "v0.2.1", "v0.2.2-rc1", "v0.2.2", "v0.2.3", "v0.2.4",
    "v0.2.5-rc1", "v0.2.5-rc2", "v0.2.5-rc3"
]

print("\n=== Fetching artifact shas across candidate tags ===")
tag_shas = {}
for tag in tags_to_check:
    items = gh_api(f"repos/logos-blockchain/logos-execution-zone/contents/artifacts/lez/programs?ref={tag}")
    if items and isinstance(items, list):
        shas = {x['name']: x['sha'] for x in items if x['name'].endswith('.bin')}
        tag_shas[tag] = shas
        auth_sha = shas.get('authenticated_transfer.bin', 'NONE')
        tok_sha = shas.get('token.bin', 'NONE')
        pin_sha = shas.get('pinata.bin', 'NONE')
        print(f"Tag {tag:12} | auth: {auth_sha[:10]} | token: {tok_sha[:10]} | pinata: {pin_sha[:10]}")
    else:
        print(f"Tag {tag:12} | No artifacts found or error")

print("\n=== Checking commits touching artifacts/lez/programs ===")
commits = gh_api("repos/logos-blockchain/logos-execution-zone/commits?path=artifacts/lez/programs&per_page=50")
if commits and isinstance(commits, list):
    for c in commits:
        sha = c['sha']
        msg = c['commit']['message'].split('\n')[0]
        date = c['commit']['committer']['date']
        print(f"{sha[:10]} | {date} | {msg}")
