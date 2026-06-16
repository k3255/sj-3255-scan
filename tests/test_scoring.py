from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.ai_engine.scoring import AIScoreEngine
from app.domain.models import Candle, MarketSeries
from app.ranking.ranker import RankingEngine
from app.scanner.relative_strength import alt_season_index, relative_score


def candle(index: int, open_price: float, close_price: float, quote_volume: float = 1000) -> Candle:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=4 * index)
    return Candle(
        open_time=start,
        open=open_price,
        high=max(open_price, close_price),
        low=min(open_price, close_price),
        close=close_price,
        volume=100,
        quote_volume=quote_volume,
        close_time=start + timedelta(hours=4),
    )


def series(symbol: str, returns: list[float]) -> MarketSeries:
    candles = []
    price = 100.0
    for index, ret in enumerate(returns):
        close = price * (1 + ret / 100)
        candles.append(candle(index, price, close, 1000 + index * 100))
        price = close
    return MarketSeries(symbol=symbol, candles=candles)


def test_relative_score_subtracts_btc_return() -> None:
    assert relative_score(-0.4, -3.8) == 3.4


def test_alt_season_index_counts_positive_relative_scores() -> None:
    assert alt_season_index([1, -1, 2, 0]) == 50.0


def test_ai_score_rewards_coin_that_outperforms_btc() -> None:
    btc = series("BTCUSDT", [-2, -1, -3, -2, -1])
    link = series("LINKUSDT", [0, 1, -0.5, 0.8, 2])
    weak = series("WEAKUSDT", [-4, -3, -5, -4, -3])

    engine = AIScoreEngine()

    assert engine.score(link, btc).ai_score > engine.score(weak, btc).ai_score


def test_ranking_assigns_rank_and_new_entries() -> None:
    btc = series("BTCUSDT", [-2, -1, -3, -2, -1])
    link = series("LINKUSDT", [0, 1, -0.5, 0.8, 2])
    weak = series("WEAKUSDT", [-4, -3, -5, -4, -3])

    report = RankingEngine().rank(btc, [weak, link], previous_top10={"OLDUSDT"})

    assert report.top10[0].symbol == "LINKUSDT"
    assert report.top10[0].rank == 1
    assert "LINKUSDT" in report.new_entries
