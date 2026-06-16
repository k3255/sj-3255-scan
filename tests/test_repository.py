from __future__ import annotations

from datetime import datetime, timezone

from app.database.json_repository import JSONRepository
from app.domain.models import ScanReport, ScanResult
from app.report.text_report import render_text_report


def result(symbol: str, rank: int) -> ScanResult:
    return ScanResult(
        symbol=symbol,
        scan_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        btc_return=-1.0,
        coin_return=1.0,
        relative_score=2.0,
        cumulative_relative_score=5.0,
        ai_score=80.0 - rank,
        volume_score=70.0,
        trend_score=60.0,
        leading_score=50.0,
        volatility_score=90.0,
        rank=rank,
        top10_streak=1,
        top20_streak=1,
    )


def test_repository_saves_and_reads_latest(tmp_path) -> None:
    repository = JSONRepository(tmp_path / "data")
    report = ScanReport(
        scan_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        btc_return=-1.0,
        alt_season_index=50.0,
        results=[result("LINKUSDT", 1), result("SOLUSDT", 2)],
        new_entries=["LINKUSDT"],
        volume_spikes=[],
    )

    repository.save_report(report)

    latest = repository.latest_results(limit=1)
    assert latest[0]["symbol"] == "LINK"
    assert repository.previous_top10() == {"LINKUSDT", "SOLUSDT"}
    assert repository.has_scan(datetime(2026, 1, 1, tzinfo=timezone.utc)) is True
    assert (tmp_path / "data" / "history" / "2026" / "01" / "01" / "0000.json").exists()
    assert (tmp_path / "data" / "ranking" / "latest.json").exists()
    assert (tmp_path / "data" / "dashboard" / "dashboard.json").exists()
    assert (tmp_path / "data" / "dashboard" / "index.html").exists()


def test_repository_calculates_leading_scores(tmp_path) -> None:
    repository = JSONRepository(tmp_path / "data")
    first = ScanReport(
        scan_time=datetime(2026, 1, 1, 0, tzinfo=timezone.utc),
        btc_return=-2.0,
        alt_season_index=50.0,
        results=[result("LINKUSDT", 1)],
        new_entries=["LINKUSDT"],
        volume_spikes=[],
    )
    second_result = result("LINKUSDT", 1)
    second = ScanReport(
        scan_time=datetime(2026, 1, 1, 4, tzinfo=timezone.utc),
        btc_return=1.0,
        alt_season_index=50.0,
        results=[second_result.__class__(**{**second_result.__dict__, "scan_time": datetime(2026, 1, 1, 4, tzinfo=timezone.utc)})],
        new_entries=[],
        volume_spikes=[],
    )

    repository.save_report(first)
    repository.save_report(second)

    assert repository.leading_scores()["LINKUSDT"] == 100.0


def test_text_report_contains_korean_explanations() -> None:
    report = ScanReport(
        scan_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        btc_return=-1.0,
        alt_season_index=67.0,
        results=[result("LINKUSDT", 1)],
        new_entries=["LINKUSDT"],
        volume_spikes=[],
    )

    text = render_text_report(report)

    assert "해석:" in text
    assert "KST 2026-01-01 09:00" in text
    assert "BTC 대비" in text
    assert "추가 관찰 우선순위" in text
