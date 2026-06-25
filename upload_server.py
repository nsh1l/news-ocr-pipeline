#!/usr/bin/env python3
"""HTTPS upload server + static HTML uploader. Python 3.13 compatible."""

import os, ssl, http.server, socketserver, re, base64
from pathlib import Path

PORT = 8443
PASSFILE = "/tmp/upload.creds"
UPLOAD_DIR = Path("/home/nsh1l/news-input")
STATIC_DIR = Path("/home/nsh1l")
UPLOAD_DIR.mkdir(exist_ok=True)

# Load credentials
creds = {}
if Path(PASSFILE).exists():
    for line in open(PASSFILE):
        line = line.strip()
        if ":" in line:
            u, _, p = line.partition(":")
            creds[u] = p

def check_auth(handler):
    hdr = handler.headers.get("Authorization", "")
    if not hdr.startswith("Basic "):
        return False
    try:
        token = base64.b64decode(hdr[6:]).decode()
        u, _, p = token.partition(":")
        return creds.get(u) == p
    except:
        return False

def parse_multipart(body: bytes, content_type: str) -> list[tuple[str, bytes]]:
    m = re.search(r'boundary=(["\']?)([^"\']+)\1?$', content_type)
    if not m:
        return []
    boundary = "--" + m.group(2).replace("\r", "").replace("\n", "")

    parts = []
    chunks = body.split(boundary.encode())
    for chunk in chunks:
        if not chunk.strip() or chunk == b'--' or chunk == b'--\r\n':
            continue
        chunk = chunk.strip(b'\r\n')
        if not chunk:
            continue
        idx = chunk.find(b'\r\n\r\n')
        if idx == -1:
            continue
        header_block = chunk[:idx].decode('utf-8', errors='replace')
        file_data = chunk[idx+4:]
        if file_data.endswith(b'\r\n'):
            file_data = file_data[:-2]

        fn_m = re.search(r'filename=(["\']?)([^"\']+)\1', header_block)
        if not fn_m:
            continue
        fname = os.path.basename(fn_m.group(2)).replace("..", "_")
        parts.append((fname, file_data))
    return parts

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_auth(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="upload"')
        self.end_headers()

    def send_file(self, path: Path, ct: str):
        if not path.exists():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        # Serve uploader HTML at root
        if self.path in ("/", "/index.html", "/uploader.html"):
            return self.send_file(STATIC_DIR / "upload.html", "text/html; charset=utf-8")
        # Serve static JS/CSS from /home/nsh1l/
        if self.path.startswith("/static/"):
            subpath = self.path[len("/static/"):]
            file_path = STATIC_DIR / subpath
            return self.send_file(file_path, "application/octet-stream")
        # File download
        if self.path.startswith("/download/"):
            fname = self.path[len("/download/"):]
            path = UPLOAD_DIR / fname
            return self.send_file(path, "application/pdf")
        # File list
        if self.path == "/files":
            if not check_auth(self):
                return self.send_auth()
            items = []
            for f in sorted(UPLOAD_DIR.glob("*")):
                if f.is_file():
                    sz = f.stat().st_size
                    items.append(f'<li><a href="/download/{f.name}">{f.name}</a> ({sz//1024}KB)</li>')
            body = ("<html><body><h1>Files</h1><ul>" +
                    ("".join(items) if items else "<li>no files yet</li>") +
                    "</ul><hr><a href='/'>← Upload</a></body></html>").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
            return
        # API: list files as JSON (for JS uploader)
        if self.path == "/api/files":
            if not check_auth(self):
                return self.send_auth()
            import json
            items = [{"name": f.name, "size": f.stat().st_size}
                    for f in sorted(UPLOAD_DIR.glob("*")) if f.is_file()]
            body = json.dumps(items).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if not check_auth(self):
            return self.send_auth()
        ct = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ct:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"multipart/form-data required")
            return
        cl = int(self.headers.get("Content-Length", 0))
        if cl == 0 or cl > 500 * 1024 * 1024:
            self.send_response(413)
            self.end_headers()
            self.wfile.write(b"file too large or empty")
            return
        body = self.rfile.read(cl)
        files = parse_multipart(body, ct)
        if not files:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>400: no file found</h1>")
            return

        saved = []
        for fname, data in files:
            path = UPLOAD_DIR / fname
            with open(path, "wb") as out:
                out.write(data)
            saved.append(f"{fname} ({len(data)//1024}KB)")
            print(f"[upload] Saved: {fname} ({len(data)//1024}KB)")

        body = ("<html><body><h1>Uploaded</h1><ul>" +
                "".join(f"<li>{s}</li>" for s in saved) +
                "</ul><a href='/'>← More</a></body></html>").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        if not check_auth(self):
            return self.send_auth()
        self.send_response(200)
        self.end_headers()

CERT_KEY = Path("/home/nsh1l/news-input/upload.key")
CERT_CRT = Path("/home/nsh1l/news-input/upload.crt")

if not CERT_CRT.exists():
    import subprocess
    print("[upload] Generating self-signed cert...")
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", str(CERT_KEY), "-out", str(CERT_CRT),
        "-days", "365", "-nodes", "-subj", "/CN=upload.soichi.ro"
    ], check=True, capture_output=True)
    print("[upload] Cert generated.")

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(str(CERT_CRT), str(CERT_KEY))

print(f"[upload] Starting HTTPS on :{PORT}")
print(f"[upload] Uploader: https://upload.soichi.ro/")
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as srv:
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    srv.serve_forever()
