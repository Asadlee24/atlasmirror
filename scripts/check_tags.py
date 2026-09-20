import urllib.request
import re

tags = ["v0.2.1", "v0.2.2", "v0.2.3", "v0.2.4", "v0.2.5-rc1", "v0.2.5-rc2", "v0.2.5-rc3"]

for tag in tags:
    url = f"https://raw.githubusercontent.com/logos-blockchain/logos-execution-zone/{tag}/lez/programs/src/lib.rs"
    try:
        with urllib.request.urlopen(url) as r:
            code = r.read().decode('utf-8')
            has_pinata = "pinata" in code
            has_fee = "fee" in code
            print(f"Tag {tag}: has_pinata={has_pinata}, has_fee={has_fee}")
    except Exception as e:
        print(f"Tag {tag}: error {e}")
