import urllib.request
import re

for tag in ["v0.2.1", "v0.2.2", "v0.2.3", "v0.2.4"]:
    url = f"https://raw.githubusercontent.com/logos-blockchain/logos-execution-zone/{tag}/lez/programs/src/lib.rs"
    try:
        with urllib.request.urlopen(url) as r:
            code = r.read().decode('utf-8')
            print(f"=== {tag} lez/programs/src/lib.rs ===")
            print(code[:1000])
    except Exception as e:
        print(f"{tag}: {e}")
