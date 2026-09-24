import urllib.request, json, struct

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
manifest_map = {e['region']: e for e in manifest if e.get('in_closed_set')}
counting_25 = [e['region'] for e in manifest if e.get('in_closed_set')][:25]

print(f'Total on-chain records in T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci: {len(records)}')
print(f'Last updated timestamp: {last_updated}')

print('\n--- AUDITING ALL 25 COUNTING ENTRIES (HIERARCHY, CID & MD5) ---')
mismatches = []
for reg_name in counting_25:
    onchain = next((r for r in records if r['region'] == reg_name), None)
    expected_cat = cat_map.get(reg_name)
    expected_man = manifest_map.get(reg_name)
    if not onchain:
        print(f'MISSING ON CHAIN: {reg_name}')
        mismatches.append((reg_name, "MISSING_ON_CHAIN"))
        continue
    exp_lvl = expected_cat['level'] if expected_cat else 'country'
    exp_parent = expected_cat['parent'] if expected_cat else None
    exp_cid = expected_man['cid'] if expected_man else ''
    exp_md5 = expected_man['geofabrik_md5'] if expected_man else ''
    
    match_hier = (onchain['level'] == exp_lvl and onchain['parent'] == exp_parent)
    match_cid = (not exp_cid or onchain['cid'] == exp_cid)
    match_md5 = (not exp_md5 or onchain['checksum'] == exp_md5)

    if not (match_hier and match_cid and match_md5):
        mismatches.append((reg_name, f"hier={match_hier}, cid={match_cid}, md5={match_md5}"))
        print(f'MISMATCH: {reg_name} -> On-Chain CID: {onchain["cid"]} | Exp CID: {exp_cid} | MD5: {onchain["checksum"]} vs {exp_md5}')
    else:
        print(f'OK: {reg_name} (level={exp_lvl}, parent={exp_parent}, CID={onchain["cid"][:12]}..., MD5={onchain["checksum"]})')

print(f'\nTotal Mismatches in 25 counting set: {len(mismatches)}')
if mismatches:
    print('Mismatched regions list:')
    for m in mismatches:
        print(f'  {m[0]}: {m[1]}')
else:
    print('ALL 25/25 COUNTING ENTRIES 100% MATCHED (HIERARCHY, CID, AND MD5)!')
