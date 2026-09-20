import json
import urllib.request

url = "https://testnet.lez.logos.co/"

def call_rpc(method, params=[]):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

acc_b58 = "5MmpKSBLk5ixgwnuzS9AjpDu9oW5EUUdZpfSvNUHcnYb"

for m in ["checkHealth", "getLastBlockId", "getAccountBalance", "getChannelId", "getProgramIds"]:
    if m in ["getAccountBalance", "getAccount"]:
        p = [acc_b58]
    else:
        p = []
    print(f"{m}:", call_rpc(m, p))
