"""
SA-CP (Sovereign Antigravity Co-Pilot Engine v11.0 - Full Chrome Extension PNA/CORS Bypass Engine)
- Dedicated 1:1 Live AI Co-Pilot Local Stream Server.
- Full Chrome Extension Private Network Access (PNA) & CORS headers.
- GET /api/stream -> Returns live sacp_direct_chat_stream.json content.
- POST /api/chat -> Appends ONLY raw user message with 'processed_by_antigravity': false.
"""

import os
import json
import time
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE_DIR = os.path.abspath("g:/내 드라이브/실험실")
SACP_DIR = os.path.join(WORKSPACE_DIR, "SA-CP")
STREAM_FILE = os.path.join(SACP_DIR, "sacp_direct_chat_stream.json")

os.makedirs(SACP_DIR, exist_ok=True)

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [SA-CP PNA/CORS Engine v11.0] {msg}")

def get_stream_data():
    if os.path.exists(STREAM_FILE):
        try:
            with open(STREAM_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "module": "SA-CP (Sovereign Antigravity Co-Pilot Engine v11.0)",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "quota_policy": "ANTIGRAVITY_IDE_ONLY (GCP Credit: $0.00, Spark Quota: 0.00%)",
        "chat_messages": []
    }

def append_raw_user_message(user_text):
    """Appends ONLY raw user message with processed_by_antigravity: false."""
    timestamp_now = time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    stream_data = get_stream_data()
    messages = stream_data.get("chat_messages", [])
    
    user_msg = {
        "id": f"msg-user-{int(time.time() * 1000)}",
        "timestamp": timestamp_now,
        "sender": "The Architect (시장님)",
        "role": "user",
        "text": user_text,
        "processed_by_antigravity": False
    }
    messages.append(user_msg)

    stream_data["chat_messages"] = messages
    stream_data["last_updated"] = timestamp_now

    with open(STREAM_FILE, "w", encoding="utf-8") as f:
        json.dump(stream_data, f, indent=2, ensure_ascii=False)

    log(f"📥 Stashed Raw User Msg -> '{user_text}'")
    return stream_data

class SacpFullCorsHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Allow-Private-Network', 'true')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        stream_data = get_stream_data()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(stream_data, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        payload = json.loads(post_data.decode('utf-8'))
        
        user_text = payload.get("text", "")
        log(f"📥 Received from Chrome Extension: '{user_text}'")

        updated_stream = append_raw_user_message(user_text)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(updated_stream, ensure_ascii=False).encode('utf-8'))

def run_bridge_server():
    server_address = ('0.0.0.0', 8899)
    httpd = HTTPServer(server_address, SacpFullCorsHandler)
    log("🚀 SA-CP Full PNA/CORS Server running on http://127.0.0.1:8899 (0.0.0.0:8899) ...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_bridge_server()
