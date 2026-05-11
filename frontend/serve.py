#!/usr/bin/env python3
"""Simple HTTP server that disables caching — for local development only."""
from http.server import SimpleHTTPRequestHandler, HTTPServer

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # suppress request logs

if __name__ == "__main__":
    server = HTTPServer(("", 5501), NoCacheHandler)
    print("Frontend running at http://localhost:5501")
    server.serve_forever()
