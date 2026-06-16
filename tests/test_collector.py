from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.collector.binance import BinanceFuturesCollector


def kline(open_time: datetime, close_time: datetime) -> list[object]:
    return [
        int(open_time.timestamp() * 1000),
        "100",
        "110",
        "90",
        "105",
        "10",
        int(close_time.timestamp() * 1000),
        "1000",
    ]


def test_fetch_series_excludes_current_open_candle() -> None:
    now = datetime.now(tz=timezone.utc)
    closed_open = now - timedelta(hours=8)
    closed_close = now - timedelta(hours=4)
    open_open = now - timedelta(minutes=30)
    future_close = now + timedelta(hours=3)
    collector = BinanceFuturesCollector("https://example.test")
    collector._get = lambda path, params=None: [kline(closed_open, closed_close), kline(open_open, future_close)]  # type: ignore[method-assign]

    series = collector.fetch_series("LINKUSDT")

    assert len(series.candles) == 1
    assert int(series.candles[0].close_time.timestamp() * 1000) == int(closed_close.timestamp() * 1000)
