from __future__ import annotations

from datetime import datetime

from app.ai_engine.scoring import AIScoreEngine
from app.domain.models import MarketSeries, ScanReport, ScanResult
from app.scanner.relative_strength import alt_season_index, relative_score


class RankingEngine:
    def __init__(self, score_engine: AIScoreEngine | None = None) -> None:
        self.score_engine = score_engine or AIScoreEngine()

    def rank(
        self,
        btc: MarketSeries,
        markets: list[MarketSeries],
        previous_top10: set[str] | None = None,
        previous_streaks: dict[str, tuple[int, int]] | None = None,
        leading_scores: dict[str, float] | None = None,
    ) -> ScanReport:
        previous_top10 = previous_top10 or set()
        previous_streaks = previous_streaks or {}
        leading_scores = leading_scores or {}
        btc_return = btc.latest.return_pct
        scan_time = btc.latest.close_time
        provisional: list[ScanResult] = []

        for market in markets:
            coin_return = market.latest.return_pct
            rel = relative_score(coin_return, btc_return)
            breakdown = self.score_engine.score(market, btc, leading_score=leading_scores.get(market.symbol, 50.0))
            provisional.append(
                ScanResult(
                    symbol=market.symbol,
                    scan_time=scan_time,
                    btc_return=round(btc_return, 4),
                    coin_return=round(coin_return, 4),
                    relative_score=round(rel, 4),
                    cumulative_relative_score=breakdown.cumulative_relative_score,
                    ai_score=breakdown.ai_score,
                    volume_score=breakdown.volume_score,
                    trend_score=breakdown.trend_score,
                    leading_score=breakdown.leading_score,
                    volatility_score=breakdown.volatility_score,
                    rank=0,
                    top10_streak=0,
                    top20_streak=0,
                )
            )

        sorted_results = sorted(provisional, key=lambda item: (item.ai_score, item.relative_score), reverse=True)
        ranked: list[ScanResult] = []
        for idx, result in enumerate(sorted_results, start=1):
            old10, old20 = previous_streaks.get(result.symbol, (0, 0))
            top10_streak = old10 + 1 if idx <= 10 else 0
            top20_streak = old20 + 1 if idx <= 20 else 0
            ranked.append(result.__class__(**{**result.__dict__, "rank": idx, "top10_streak": top10_streak, "top20_streak": top20_streak}))

        new_entries = [result.symbol for result in ranked[:10] if result.symbol not in previous_top10]
        volume_spikes = [result.symbol for result in ranked if result.volume_score >= 80][:10]
        return ScanReport(
            scan_time=scan_time,
            btc_return=round(btc_return, 4),
            alt_season_index=alt_season_index([item.relative_score for item in ranked]),
            results=ranked,
            new_entries=new_entries,
            volume_spikes=volume_spikes,
        )
