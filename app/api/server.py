from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

from app.dashboard.static import DASHBOARD_HTML
from app.database.json_repository import JSONRepository


class APIServer:
    def __init__(self, repository: JSONRepository) -> None:
        self.repository = repository

    def serve(self, host: str, port: int) -> None:
        repository = self.repository

        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self) -> None:
                if self.path in {"/", "/dashboard"}:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    return
                try:
                    route(repository, self.path)
                    self.send_response(200)
                except KeyError:
                    self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()

            def do_GET(self) -> None:
                try:
                    if self.path in {"/", "/dashboard"}:
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
                        return
                    payload = route(repository, self.path)
                    self.send_response(200)
                except KeyError:
                    payload = {"error": "not_found"}
                    self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))

            def log_message(self, format: str, *args: object) -> None:
                return

        ThreadingHTTPServer((host, port), Handler).serve_forever()


def route(repository: JSONRepository, path: str) -> object:
    if path == "/api/top10":
        return repository.latest_results(limit=10)
    if path == "/api/top20":
        return repository.latest_results(limit=20)
    if path == "/api/latest":
        return repository.latest_payload()
    if path == "/api/dashboard":
        payload = repository.latest_payload()
        return payload if payload else {"top10": [], "top20": [], "ranking": [], "altSeasonIndex": 0}
    if path == "/api/altscore":
        payload = repository.latest_payload()
        return {"time": payload.get("scanTime"), "altSeasonIndex": payload.get("altSeasonIndex", 0)}
    if path.startswith("/api/history/"):
        symbol = unquote(path.removeprefix("/api/history/")).upper()
        return repository.symbol_history(symbol)
    raise KeyError(path)
