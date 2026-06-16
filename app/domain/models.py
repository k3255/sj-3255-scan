from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Candle:
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    close_time: datetime

    @property
    def return_pct(self) -> float:
        if self.open == 0:
            return 0.0
        return (self.close - self.open) / self.open * 100


@dataclass(frozen=True)
class MarketSeries:
    symbol: str
    candles: list[Candle]

    @property
    def latest(self) -> Candle:
        return self.candles[-1]


@dataclass(frozen=True)
class ScanResult:
    symbol: str
    scan_time: datetime
    btc_return: float
    coin_return: float
    relative_score: float
    cumulative_relative_score: float
    ai_score: float
    volume_score: float
    trend_score: float
    leading_score: float
    volatility_score: float
    rank: int
    top10_streak: int
    top20_streak: int


@dataclass(frozen=True)
class ScanReport:
    scan_time: datetime
    btc_return: float
    alt_season_index: float
    results: list[ScanResult]
    new_entries: list[str]
    volume_spikes: list[str]

    @property
    def top10(self) -> list[ScanResult]:
        return self.results[:10]

    @property
    def top20(self) -> list[ScanResult]:
        return self.results[:20]
