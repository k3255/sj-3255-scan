from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.domain.models import Candle, MarketSeries


STABLE_PREFIXES = {"USDC", "BUSD", "FDUSD", "TUSD", "USDP", "DAI"}


class BinanceFuturesCollector:
    def __init__(self, base_url: str, timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def discover_symbols(self, min_quote_volume: float) -> list[str]:
        exchange_info = self._get("/fapi/v1/exchangeInfo")
        tickers = {item["symbol"]: float(item.get("quoteVolume", 0)) for item in self._get("/fapi/v1/ticker/24hr")}
        symbols: list[str] = []
        for item in exchange_info["symbols"]:
            symbol = item["symbol"]
            base_asset = item.get("baseAsset", "")
            if item.get("contractType") != "PERPETUAL":
                continue
            if item.get("quoteAsset") != "USDT" or item.get("status") != "TRADING":
                continue
            if base_asset in STABLE_PREFIXES or symbol == "BTCUSDT":
                continue
            if tickers.get(symbol, 0) < min_quote_volume:
                continue
            symbols.append(symbol)
        return sorted(symbols)

    def fetch_series(self, symbol: str, interval: str = "4h", limit: int = 80) -> MarketSeries:
        payload = self._get("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})
        candles = [self._parse_candle(row) for row in payload]
        closed_candles = [candle for candle in candles if candle.close_time <= datetime.now(tz=timezone.utc)]
        return MarketSeries(symbol=symbol, candles=closed_candles)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}{path}", params=params)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _parse_candle(row: list[Any]) -> Candle:
        return Candle(
            open_time=datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
            close_time=datetime.fromtimestamp(row[6] / 1000, tz=timezone.utc),
            quote_volume=float(row[7]),
        )
