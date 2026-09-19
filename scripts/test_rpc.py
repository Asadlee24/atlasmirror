import urllib.request
import json

def main():
    url = "http://127.0.0.1:9000/"
    req_data = {
        "jsonrpc": "2.0",
        "method": "getLastBlockId",
        "params": [],
        "id": 1
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(req_data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print("HTTP Status:", response.status)
            print("Response Body:", res_body)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
