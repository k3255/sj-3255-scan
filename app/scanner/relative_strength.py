from __future__ import annotations

from app.domain.models import MarketSeries


def relative_score(coin_return: float, btc_return: float) -> float:
    return coin_return - btc_return


def recent_relative_scores(series: MarketSeries, btc: MarketSeries, periods: int = 5) -> list[float]:
    coin_candles = series.candles[-periods:]
    btc_candles = btc.candles[-periods:]
    return [
        relative_score(coin.return_pct, btc_candle.return_pct)
        for coin, btc_candle in zip(coin_candles, btc_candles, strict=False)
    ]


def alt_season_index(relative_scores: list[float]) -> float:
    if not relative_scores:
        return 0.0
    strong = sum(1 for score in relative_scores if score > 0)
    return round(strong / len(relative_scores) * 100, 2)
