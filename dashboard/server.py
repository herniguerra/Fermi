#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = 8080
SCRIPT_DIR = Path(__file__).parent
WORKSPACE_DIR = SCRIPT_DIR.parent
MEMORY_DIR = WORKSPACE_DIR / "memory"
PUBLIC_DIR = SCRIPT_DIR / "public"

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static files from PUBLIC_DIR
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path.startswith("/api/"):
            self.handle_api(path, query)
        else:
            # Serve static files relative to PUBLIC_DIR
            super().do_GET()

    def handle_api(self, path, query):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        response = {}
        try:
            if path == "/api/today":
                today_path = MEMORY_DIR / "TODAY.md"
                content = today_path.read_text(encoding="utf-8") if today_path.exists() else "No briefing found."
                response = {"content": content}

            elif path == "/api/beliefs":
                beliefs_path = MEMORY_DIR / "BELIEFS.md"
                content = beliefs_path.read_text(encoding="utf-8") if beliefs_path.exists() else "No beliefs found."
                response = {"content": content}

            elif path == "/api/memory":
                # For dashboard, show the living consolidated reflections file reflections.md
                refl_path = MEMORY_DIR / "reflections" / "reflections.md"
                content = refl_path.read_text(encoding="utf-8") if refl_path.exists() else "No reflections file found."
                response = {"content": content}

            elif path == "/api/archives":
                today_archives = []
                today_dir = MEMORY_DIR / "today"
                if today_dir.exists():
                    for r, d, files in os.walk(today_dir):
                        for f in files:
                            if f.endswith(".md"):
                                today_archives.append(f)
                
                dream_archives = []
                dreams_dir = MEMORY_DIR / "dreams"
                if dreams_dir.exists():
                    for r, d, files in os.walk(dreams_dir):
                        for f in files:
                            if f.endswith(".md"):
                                dream_archives.append(f)

                response = {
                    "today": sorted(today_archives, reverse=True),
                    "dreams": sorted(dream_archives, reverse=True)
                }

            elif path == "/api/archive":
                archive_type = query.get("type", ["today"])[0]
                filename = query.get("file", [""])[0]
                
                if not filename or ".." in filename or filename.startswith("/") or filename.startswith("\\"):
                    response = {"error": "Invalid file"}
                else:
                    if archive_type == "today":
                        # today_YYYY-MM-DD.md -> Extract YYYY and MM
                        # e.g., today_2026-07-03.md -> parts = ["2026", "07", "03"]
                        date_part = filename.replace("today_", "").replace(".md", "")
                        parts = date_part.split("-")
                        if len(parts) == 3:
                            file_path = MEMORY_DIR / "today" / parts[0] / parts[1] / filename
                        else:
                            file_path = MEMORY_DIR / "today" / filename
                    else:
                        # dreams
                        date_part = filename.replace("dream_", "").replace(".md", "")
                        parts = date_part.split("-")
                        if len(parts) == 3:
                            file_path = MEMORY_DIR / "dreams" / parts[0] / parts[1] / filename
                        else:
                            file_path = MEMORY_DIR / "dreams" / filename
                    
                    content = file_path.read_text(encoding="utf-8") if file_path.exists() else f"Archive file not found: {file_path.name}"
                    response = {"content": content}

            else:
                response = {"error": "Not Found"}

        except Exception as e:
            response = {"error": str(e)}

        self.wfile.write(json.dumps(response).encode("utf-8"))

def run():
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Serving Fermi Dashboard at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run()
