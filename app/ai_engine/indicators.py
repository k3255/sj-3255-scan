from __future__ import annotations

from statistics import pstdev

from app.domain.models import Candle


def ema(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    alpha = 2 / (period + 1)
    result = values[0]
    for value in values[1:]:
        result = value * alpha + result * (1 - alpha)
    return result


def normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    clipped = min(max(value, low), high)
    return (clipped - low) / (high - low) * 100


def volume_increase_score(candles: list[Candle], lookback: int = 20) -> float:
    if len(candles) < 2:
        return 0.0
    latest = candles[-1].quote_volume
    baseline_values = [c.quote_volume for c in candles[-lookback - 1 : -1]]
    baseline = sum(baseline_values) / len(baseline_values) if baseline_values else latest
    if baseline <= 0:
        return 0.0
    increase = (latest - baseline) / baseline * 100
    return normalize(increase, -50, 200)


def ema_trend_score(candles: list[Candle], fast: int = 9, slow: int = 21) -> float:
    closes = [c.close for c in candles]
    if len(closes) < 2:
        return 0.0
    fast_ema = ema(closes[-slow * 3 :], fast)
    slow_ema = ema(closes[-slow * 3 :], slow)
    if slow_ema == 0:
        return 0.0
    spread = (fast_ema - slow_ema) / slow_ema * 100
    return normalize(spread, -5, 5)


def volatility_stability_score(candles: list[Candle], lookback: int = 20) -> float:
    returns = [c.return_pct for c in candles[-lookback:]]
    if len(returns) < 2:
        return 50.0
    volatility = pstdev(returns)
    return 100 - normalize(volatility, 0, 12)
