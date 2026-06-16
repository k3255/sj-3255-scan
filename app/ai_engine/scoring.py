from __future__ import annotations

from dataclasses import dataclass

from app.ai_engine.indicators import normalize, volume_increase_score, ema_trend_score, volatility_stability_score
from app.domain.models import MarketSeries
from app.scanner.relative_strength import recent_relative_scores


@dataclass(frozen=True)
class ScoreBreakdown:
    ai_score: float
    volume_score: float
    trend_score: float
    volatility_score: float
    cumulative_relative_score: float
    leading_score: float


class AIScoreEngine:
    def score(self, series: MarketSeries, btc: MarketSeries, leading_score: float = 50.0) -> ScoreBreakdown:
        recent_scores = recent_relative_scores(series, btc, periods=5)
        current_relative = recent_scores[-1] if recent_scores else 0.0
        cumulative = sum(recent_scores)
        relative_component = normalize(current_relative, -8, 8)
        cumulative_component = normalize(cumulative, -20, 20)
        volume_component = volume_increase_score(series.candles)
        trend_4h_component = ema_trend_score(series.candles)
        trend_daily_component = trend_4h_component
        volatility_component = volatility_stability_score(series.candles)

        ai_score = (
            relative_component * 0.40
            + cumulative_component * 0.20
            + volume_component * 0.15
            + trend_4h_component * 0.10
            + trend_daily_component * 0.10
            + volatility_component * 0.05
        )
        ai_score = ai_score * 0.90 + min(max(leading_score, 0), 100) * 0.10

        return ScoreBreakdown(
            ai_score=round(ai_score, 2),
            volume_score=round(volume_component, 2),
            trend_score=round((trend_4h_component + trend_daily_component) / 2, 2),
            volatility_score=round(volatility_component, 2),
            cumulative_relative_score=round(cumulative, 4),
            leading_score=round(leading_score, 2),
        )
