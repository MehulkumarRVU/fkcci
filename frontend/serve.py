#!/usr/bin/env python3
"""Local dev static file server for the frontend. Same as
`python -m http.server`, but disables browser caching so edited
HTML/JS/CSS always show up on reload instead of a stale cached copy -
plain http.server sends no Cache-Control header at all, so browsers fall
back to aggressive heuristic caching for static files during local dev.
"""
import http.server
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000


class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    http.server.test(HandlerClass=NoCacheHTTPRequestHandler, port=PORT)
