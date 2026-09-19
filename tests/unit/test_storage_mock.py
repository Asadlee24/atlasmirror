#!/usr/bin/env python3
"""
Unit Test: Logos Storage Client Adapter (Mock Server)
NOTE: This is a UNIT TEST of the client adapter logic, exponential backoff,
and retry mechanisms. It uses a mock local HTTP server.
It does NOT constitute evidence of real Logos Storage integration.
Real Logos Storage integration is tested separately in tests/integration/test_logos_storage_real.py.
"""

import http.server
import json
import socketserver
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

class MockLogosStorageHandler(http.server.BaseHTTPRequestHandler):
    storage_db = {}
    failure_counter = 0

    def do_POST(self):
        if self.path == "/api/v0/storage/upload":
            # Simulate transient errors for retry/backoff testing
            if MockLogosStorageHandler.failure_counter < 2:
                MockLogosStorageHandler.failure_counter += 1
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"error": "Node busy, retry later"}')
                return

            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            # Simulated mock CID for unit test only
            mock_cid = "mock_unit_test_cid_" + str(len(body))
            MockLogosStorageHandler.storage_db[mock_cid] = body
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"cid": mock_cid, "size": len(body)}).encode("utf-8"))

    def do_GET(self):
        if self.path.startswith("/api/v0/storage/download"):
            from urllib.parse import parse_qs, urlparse
            qs = parse_qs(urlparse(self.path).query)
            cid = qs.get("cid", [""])[0]
            if cid in MockLogosStorageHandler.storage_db:
                data = MockLogosStorageHandler.storage_db[cid]
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()

def upload_with_retry(endpoint: str, data: bytes, max_retries: int = 5) -> str:
    url = f"{endpoint}/api/v0/storage/upload"
    delay = 0.1
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/octet-stream"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["cid"]
        except urllib.error.HTTPError as e:
            if e.code == 503 and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise

def test_storage_client_unit():
    print("Running Milestone 3: Storage Client Adapter Unit Tests (Mock Server)...")

    # Start mock server on random high port
    with socketserver.TCPServer(("127.0.0.1", 0), MockLogosStorageHandler) as httpd:
        port = httpd.server_address[1]
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        endpoint = f"http://127.0.0.1:{port}"
        test_data = b"SAMPLE_PAYLOAD_FOR_STORAGE_UNIT_TEST" * 50

        # Reset failure counter
        MockLogosStorageHandler.failure_counter = 0

        print("[1/2] Testing client retry with exponential backoff on transient errors (503)...")
        cid = upload_with_retry(endpoint, test_data)
        assert cid.startswith("mock_unit_test_cid_"), "Did not receive expected mock CID"
        print(f"  Received mock CID: {cid}")
        print("  Exponential backoff retry: [PASS]")

        print("[2/2] Downloading from mock server and asserting byte equality...")
        download_url = f"{endpoint}/api/v0/storage/download?cid={cid}"
        with urllib.request.urlopen(download_url, timeout=5) as resp:
            downloaded = resp.read()
        assert downloaded == test_data, "Downloaded bytes do not match uploaded bytes"
        print("  Exact byte equality on mock roundtrip: [PASS]")

        httpd.shutdown()

    print("\n[PASS] Storage client unit tests = VERIFIED UNIT TEST")
    print("  (Note: Actual Logos Storage integration = NOT VERIFIED)")

if __name__ == "__main__":
    test_storage_client_unit()
