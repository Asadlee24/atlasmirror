from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import sys
import time

class BedrockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[Bedrock L1] GET {self.path}", flush=True)
        if "/channel/" in self.path:
            # 404 indicates channel does not exist yet (sequencer starts as creator)
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Channel not found"}')
        elif "/time/info" in self.path:
            now_ms = int(time.time() * 1000)
            data = {
                "slot_duration_ms": 1000,
                "genesis_time_unix_ms": now_ms - 100000,
                "current_slot": 100,
                "current_epoch": 1
            }
            body = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif "/cryptarchia/info" in self.path or "/mantle/status" in self.path:
            data = {
                "cryptarchia_info": {
                    "mode": "online",
                    "slot": 100,
                    "lib": "0000000000000000000000000000000000000000000000000000000000000000",
                    "lib_slot": 100,
                    "tip": "0000000000000000000000000000000000000000000000000000000000000000",
                    "height": 100,
                    "epoch": 1,
                    "state": "Online"
                },
                "phase": "Following"
            }
            body = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif "/cryptarchia/events/blocks/stream" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.end_headers()
            event = {
                "block": {
                    "header": {
                        "id": "0000000000000000000000000000000000000000000000000000000000000000",
                        "parent_block": "0000000000000000000000000000000000000000000000000000000000000000",
                        "slot": 100,
                        "body_root": "0000000000000000000000000000000000000000000000000000000000000000",
                        "proof_of_leadership": {
                            "proof": "00" * 128,
                            "entropy_contribution": "0000000000000000000000000000000000000000000000000000000000000000",
                            "leader_key": "0000000000000000000000000000000000000000000000000000000000000000",
                            "voucher_cm": "0000000000000000000000000000000000000000000000000000000000000000"
                        }
                    },
                    "uncle_headers": [],
                    "transactions": []
                },
                "tip": "0000000000000000000000000000000000000000000000000000000000000000",
                "tip_slot": 100,
                "lib": "0000000000000000000000000000000000000000000000000000000000000000",
                "lib_slot": 100
            }
            line = (json.dumps(event) + "\n").encode("utf-8")
            try:
                self.wfile.write(line)
                self.wfile.flush()
                while True:
                    time.sleep(10)
            except Exception:
                pass
        elif "/cryptarchia/blocks" in self.path:
            body = b'[]'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b'{}')

    def do_POST(self):
        print(f"[Bedrock L1] POST {self.path}", flush=True)
        if "/wallet/fund" in self.path:
            content_length = int(self.headers.get('Content-Length', 0))
            req_body = self.rfile.read(content_length)
            req_json = json.loads(req_body) if req_body else {}
            mantle_tx = req_json.get("tx_builder", {}).get("mantle_tx", {"ops": []})
            resp_data = {
                "tip": "0000000000000000000000000000000000000000000000000000000000000000",
                "funded_tx": mantle_tx,
                "transfer_proof": None
            }
            body = json.dumps(resp_data).encode("utf-8")
        else:
            body = b'null'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = 18080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    server = ThreadingHTTPServer(('127.0.0.1', port), BedrockHandler)
    print(f"Mock Bedrock L1 listening on 127.0.0.1:{port}...", flush=True)
    server.serve_forever()
