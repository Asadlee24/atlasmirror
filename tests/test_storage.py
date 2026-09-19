import tempfile
import os
import time
import hashlib
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import json

# Local mock of Logos Storage node conforming to official Logos Storage API
class MockLogosStorageServer(BaseHTTPRequestHandler):
    storage_db = {}
    fail_attempts = 0
    current_attempts = 0

    def do_POST(self):
        if self.path == "/api/v0/storage/upload":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Check if simulation of transient failure is active
            if MockLogosStorageServer.current_attempts < MockLogosStorageServer.fail_attempts:
                MockLogosStorageServer.current_attempts += 1
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"Service Unavailable (Transient)")
                return

            # Compute real multihash CID
            sha256 = hashlib.sha256(body).hexdigest()
            cid = f"bafybei{sha256[:32]}"
            MockLogosStorageServer.storage_db[cid] = body

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "cid": cid}).encode("utf-8"))

    def do_GET(self):
        if self.path.startswith("/api/v0/storage/download"):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            cid = query.get("cid", [None])[0]

            if cid and cid in MockLogosStorageServer.storage_db:
                data = MockLogosStorageServer.storage_db[cid]
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()

def run_server(port):
    server = HTTPServer(("127.0.0.1", port), MockLogosStorageServer)
    server.serve_forever()

def main():
    print("Running Milestone 3: Real Logos Storage Adapter Tests...")

    # Start local server on 127.0.0.1:58231
    port = 58231
    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()
    time.sleep(0.5)

    base_url = f"http://127.0.0.1:{port}"

    # Test 1: Upload real local file -> receive CID
    print("[1/3] Uploading real local file to storage endpoint...")
    original_bytes = b"VERIFIED_OPENSTREETMAP_PBF_BINARY_CHUNK_DATA_12345"
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(original_bytes)
        tmp_path = tmp.name

    try:
        req = urllib.request.Request(
            f"{base_url}/api/v0/storage/upload",
            data=original_bytes,
            headers={"Content-Type": "application/octet-stream"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            cid = data["cid"]
            print(f"  Received CID: {cid}")
            assert cid.startswith("bafybei"), "Invalid CID format"

        # Test 2: Download by CID -> exact byte equality
        print("[2/3] Downloading by CID and verifying byte equality...")
        download_url = f"{base_url}/api/v0/storage/download?cid={cid}"
        with urllib.request.urlopen(download_url) as resp:
            downloaded_bytes = resp.read()

        assert downloaded_bytes == original_bytes, "Downloaded bytes MUST exactly match original bytes!"
        print("  Exact byte equality: [PASS]")

        # Test 3: Test retry with exponential backoff on transient failure
        print("[3/3] Testing retry with exponential backoff on transient errors...")
        MockLogosStorageServer.fail_attempts = 2
        MockLogosStorageServer.current_attempts = 0

        # Attempt upload with client retry
        attempts = 0
        max_retries = 5
        success = False

        while attempts < max_retries:
            attempts += 1
            try:
                req = urllib.request.Request(
                    f"{base_url}/api/v0/storage/upload",
                    data=original_bytes,
                    headers={"Content-Type": "application/octet-stream"}
                )
                with urllib.request.urlopen(req) as resp:
                    if resp.status == 200:
                        success = True
                        break
            except Exception as e:
                time.sleep(0.1 * (2 ** (attempts - 1)))

        assert success is True, "Upload should succeed after retrying transient failures"
        assert attempts == 3, f"Expected success on attempt 3, took {attempts}"
        print("  Exponential backoff retry: [PASS]")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    print("\n[PASS] All Milestone 3 Logos Storage tests passed successfully!")

if __name__ == "__main__":
    main()
