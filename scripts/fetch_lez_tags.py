import json
import urllib.request

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=== LEZ Releases ===")
try:
    releases = fetch("https://api.github.com/repos/logos-blockchain/logos-execution-zone/releases")
    for r in releases:
        print(f"Tag: {r.get('tag_name')}, Name: {r.get('name')}, Published: {r.get('published_at')}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== LEZ Tags ===")
try:
    tags = fetch("https://api.github.com/repos/logos-blockchain/logos-execution-zone/tags?per_page=30")
    for t in tags:
        print(f"Tag: {t.get('name')}, Commit: {t.get('commit', {}).get('sha')}")
except Exception as e:
    print(f"Error: {e}")
