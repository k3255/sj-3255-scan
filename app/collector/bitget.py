from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.domain.models import Candle, MarketSeries


STABLE_BASE_COINS = {"USDC", "BUSD", "FDUSD", "TUSD", "USDP", "DAI"}
INTERVAL_MAP = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1H",
    "2h": "2H",
    "4h": "4H",
    "6h": "6H",
    "12h": "12H",
    "1d": "1D",
}
INTERVAL_DURATION = {
    "1m": timedelta(minutes=1),
    "3m": timedelta(minutes=3),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1H": timedelta(hours=1),
    "2H": timedelta(hours=2),
    "4H": timedelta(hours=4),
    "6H": timedelta(hours=6),
    "12H": timedelta(hours=12),
    "1D": timedelta(days=1),
}


class BitgetFuturesCollector:
    def __init__(self, base_url: str, product_type: str = "USDT-FUTURES", timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.product_type = product_type
        self.timeout = timeout

    def discover_symbols(self, min_quote_volume: float, min_listing_days: int = 14) -> list[str]:
        contracts = self._data("/api/v2/mix/market/contracts", {"productType": self.product_type})
        tickers = {
            item["symbol"]: float(item.get("usdtVolume") or item.get("quoteVolume") or 0)
            for item in self._data("/api/v2/mix/market/tickers", {"productType": self.product_type})
        }
        now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        min_age_ms = min_listing_days * 24 * 60 * 60 * 1000
        symbols: list[str] = []
        for item in contracts:
            symbol = str(item.get("symbol", ""))
            base_coin = str(item.get("baseCoin", ""))
            launch_time = _to_int(item.get("launchTime"), default=0)
            if item.get("quoteCoin") != "USDT":
                continue
            if item.get("symbolType") != "perpetual" or item.get("symbolStatus") != "normal":
                continue
            if base_coin in STABLE_BASE_COINS or symbol == "BTCUSDT":
                continue
            if launch_time > 0 and now_ms - launch_time < min_age_ms:
                continue
            if tickers.get(symbol, 0) < min_quote_volume:
                continue
            symbols.append(symbol)
        return sorted(symbols)

    def fetch_series(self, symbol: str, interval: str = "4h", limit: int = 80) -> MarketSeries:
        granularity = INTERVAL_MAP.get(interval, interval)
        duration = INTERVAL_DURATION.get(granularity)
        if duration is None:
            raise ValueError(f"Unsupported Bitget interval: {interval}")
        rows = self._data(
            "/api/v2/mix/market/candles",
            {
                "symbol": symbol,
                "productType": self.product_type,
                "granularity": granularity,
                "limit": str(limit),
            },
        )
        candles = [self._parse_candle(row, duration) for row in rows]
        closed_candles = [candle for candle in candles if candle.close_time <= datetime.now(tz=timezone.utc)]
        return MarketSeries(symbol=symbol, candles=sorted(closed_candles, key=lambda candle: candle.open_time))

    def _data(self, path: str, params: dict[str, Any]) -> Any:
        payload = self._get(path, params)
        if payload.get("code") != "00000":
            raise RuntimeError(f"Bitget API error: {payload.get('code')} {payload.get('msg')}")
        return payload.get("data", [])

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}{path}", params=params)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _parse_candle(row: list[Any], duration: timedelta) -> Candle:
        open_time = datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc)
        close_time = open_time + duration - timedelta(milliseconds=1)
        return Candle(
            open_time=open_time,
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
            quote_volume=float(row[6]),
            close_time=close_time,
        )


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
