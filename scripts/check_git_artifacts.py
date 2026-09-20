import urllib.request
import json

tags = ['v0.2.1', 'v0.2.2', 'v0.2.3', 'v0.2.4']
for tag in tags:
    url = f'https://api.github.com/repos/logos-blockchain/logos-execution-zone/contents/artifacts/lez/programs?ref={tag}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode('utf-8'))
            names = [x['name'] for x in data if x['name'].endswith('.bin')]
            print(f'{tag}: {len(names)} bin files found')
            for item in data:
                if item['name'] == 'authenticated_transfer.bin':
                    print(f"  authenticated_transfer.bin sha: {item['sha']}")
    except Exception as e:
        print(f'{tag}: {e}')
