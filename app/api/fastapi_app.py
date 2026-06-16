from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.dashboard.static import DASHBOARD_HTML
from app.database.json_repository import JSONRepository


def create_app(repository: JSONRepository) -> FastAPI:
    app = FastAPI(title="AI Crypto Relative Strength Scanner")

    @app.get("/", response_class=HTMLResponse)
    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard() -> str:
        return DASHBOARD_HTML

    @app.head("/")
    @app.head("/dashboard")
    def dashboard_head() -> None:
        return None

    @app.get("/api/top10")
    def top10() -> list[dict[str, object]]:
        return repository.latest_results(limit=10)

    @app.get("/api/top20")
    def top20() -> list[dict[str, object]]:
        return repository.latest_results(limit=20)

    @app.get("/api/latest")
    def latest() -> dict[str, object]:
        return repository.latest_payload()

    @app.get("/api/history/{symbol}")
    def history(symbol: str) -> list[dict[str, object]]:
        return repository.symbol_history(symbol)

    @app.get("/api/altscore")
    def altscore() -> dict[str, object]:
        payload = repository.latest_payload()
        return {"time": payload.get("scanTime"), "altSeasonIndex": payload.get("altSeasonIndex", 0)}

    @app.get("/api/dashboard")
    def dashboard_json() -> dict[str, object]:
        payload = repository.latest_payload()
        if not payload:
            return {"top10": [], "top20": [], "ranking": [], "altSeasonIndex": 0}
        return payload

    return app
