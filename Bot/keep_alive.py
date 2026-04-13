"""
Minimal HTTP server to keep Render free-tier Web Service alive.
Runs on a background thread so it doesn't block the Discord bot.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os


class HealthHandler(BaseHTTPRequestHandler):
    """Responds 200 OK to any GET request."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive")

    # Suppress per-request log spam
    def log_message(self, format, *args):
        pass


def keep_alive():
    """Start the health-check server on PORT (Render injects this)."""
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Health server listening on port {port}")
