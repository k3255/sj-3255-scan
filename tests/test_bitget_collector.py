from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.collector.bitget import BitgetFuturesCollector


def test_bitget_discover_symbols_filters_contracts_and_volume() -> None:
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    collector = BitgetFuturesCollector("https://example.test")

    def fake_data(path: str, params: dict[str, object]) -> list[dict[str, object]]:
        if path.endswith("/contracts"):
            return [
                {
                    "symbol": "BTCUSDT",
                    "baseCoin": "BTC",
                    "quoteCoin": "USDT",
                    "symbolType": "perpetual",
                    "symbolStatus": "normal",
                    "launchTime": str(now_ms - 30 * 24 * 60 * 60 * 1000),
                },
                {
                    "symbol": "LINKUSDT",
                    "baseCoin": "LINK",
                    "quoteCoin": "USDT",
                    "symbolType": "perpetual",
                    "symbolStatus": "normal",
                    "launchTime": str(now_ms - 30 * 24 * 60 * 60 * 1000),
                },
                {
                    "symbol": "NEWUSDT",
                    "baseCoin": "NEW",
                    "quoteCoin": "USDT",
                    "symbolType": "perpetual",
                    "symbolStatus": "normal",
                    "launchTime": str(now_ms - 1 * 24 * 60 * 60 * 1000),
                },
                {
                    "symbol": "MAINTUSDT",
                    "baseCoin": "MAINT",
                    "quoteCoin": "USDT",
                    "symbolType": "perpetual",
                    "symbolStatus": "maintain",
                    "launchTime": str(now_ms - 30 * 24 * 60 * 60 * 1000),
                },
            ]
        return [
            {"symbol": "LINKUSDT", "usdtVolume": "60000000"},
            {"symbol": "NEWUSDT", "usdtVolume": "90000000"},
            {"symbol": "MAINTUSDT", "usdtVolume": "90000000"},
        ]

    collector._data = fake_data  # type: ignore[method-assign]

    assert collector.discover_symbols(min_quote_volume=50_000_000, min_listing_days=14) == ["LINKUSDT"]


def test_bitget_fetch_series_parses_candles_and_excludes_open_candle() -> None:
    now = datetime.now(tz=timezone.utc)
    closed_open = now - timedelta(hours=8)
    open_open = now - timedelta(hours=1)
    collector = BitgetFuturesCollector("https://example.test")
    collector._data = lambda path, params: [  # type: ignore[method-assign]
        [
            str(int(closed_open.timestamp() * 1000)),
            "100",
            "110",
            "90",
            "105",
            "12",
            "1260",
        ],
        [
            str(int(open_open.timestamp() * 1000)),
            "105",
            "112",
            "100",
            "108",
            "10",
            "1080",
        ],
    ]

    series = collector.fetch_series("LINKUSDT", "4h")

    assert len(series.candles) == 1
    assert series.symbol == "LINKUSDT"
    assert series.candles[0].quote_volume == 1260
    assert series.candles[0].close_time == series.candles[0].open_time + timedelta(hours=4) - timedelta(milliseconds=1)
