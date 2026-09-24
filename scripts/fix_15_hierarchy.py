#!/usr/bin/env python3
import urllib.request, json, struct, time, subprocess, sys

url = 'https://testnet.lez.logos.co/'
req = urllib.request.Request(url, data=json.dumps({'jsonrpc':'2.0','id':1,'method':'getAccount','params':['T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci']}).encode(), headers={'Content-Type':'application/json'})
raw = bytes(json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['result']['data'])

offset = 0
def read_u64():
    global offset
    v = struct.unpack_from('<Q', raw, offset)[0]
    offset += 8
    return v

def read_u32():
    global offset
    v = struct.unpack_from('<I', raw, offset)[0]
    offset += 4
    return v

def read_u8():
    global offset
    v = raw[offset]
    offset += 1
    return v

def read_string():
    global offset
    l = read_u32()
    s = raw[offset:offset+l].decode('utf-8')
    offset += l
    return s

def read_opt_string():
    tag = read_u8()
    if tag == 0:
        return None
    elif tag == 1:
        return read_string()
    else:
        raise ValueError(f'Invalid opt tag: {tag}')

total_regions = read_u64()
last_updated = read_u64()
num_records = read_u32()

records = []
for i in range(num_records):
    reg = read_string()
    parent = read_opt_string()
    lvl = 'country' if read_u8() == 0 else 'subregion'
    cid = read_string()
    src = read_string()
    cs = read_string()
    ver = read_string()
    h = (read_u8() != 0)
    ts = read_u64()
    records.append({
        'region': reg, 'parent': parent, 'level': lvl,
        'cid': cid, 'checksum': cs, 'version': ver,
        'hosted': h, 'timestamp': ts, 'source_url': src
    })

cat = json.load(open('metadata/regions.json'))['regions']
cat_map = {r['path']: r for r in cat}
manifest = json.load(open('evidence/a1-coverage-manifest.json'))['entries']
counting_25 = [e['region'] for e in manifest if e.get('in_closed_set')][:25]

mismatches = []
for reg_name in counting_25:
    onchain = next((r for r in records if r['region'] == reg_name), None)
    expected = cat_map.get(reg_name)
    if not onchain:
        continue
    exp_lvl = expected['level'] if expected else 'country'
    exp_parent = expected['parent'] if expected else None
    if onchain['level'] != exp_lvl or onchain['parent'] != exp_parent:
        mismatches.append(onchain)

print(f"Found {len(mismatches)} mismatches to fix.")
cur_ts = max(int(time.time()), last_updated + 100)

batch_records = []
for m in mismatches:
    print(f"Target: {m['region']} | CID: {m['cid']} | Checksum: {m['checksum']} | URL: {m['source_url']}")
    batch_records.append({
        "region": m['region'],
        "parent": None,
        "level": "Country",
        "cid": m['cid'],
        "source_url": m['source_url'],
        "checksum": m['checksum'],
        "version": m['version'],
        "hosted": True,
        "timestamp": cur_ts
    })

batch_file = "batch_15.json"
with open(batch_file, "w") as f:
    json.dump(batch_records, f, indent=2)

print(f"\nGenerated {batch_file} with {len(batch_records)} records at timestamp {cur_ts}.")
