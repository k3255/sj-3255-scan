from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.dashboard.static import DASHBOARD_HTML
from app.domain.models import ScanReport, ScanResult


class JSONRepository:
    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.history_dir = self.data_dir / "history"
        self.ranking_dir = self.data_dir / "ranking"
        self.dashboard_dir = self.data_dir / "dashboard"
        self.report_dir = self.data_dir / "report"

    def migrate(self) -> None:
        for directory in [self.history_dir, self.ranking_dir, self.dashboard_dir, self.report_dir, self.data_dir / "config"]:
            directory.mkdir(parents=True, exist_ok=True)

    def save_report(self, report: ScanReport) -> None:
        self.migrate()
        payload = self._report_payload(report)
        scan_time = report.scan_time
        history_path = (
            self.history_dir
            / f"{scan_time:%Y}"
            / f"{scan_time:%m}"
            / f"{scan_time:%d}"
            / f"{scan_time:%H%M}.json"
        )
        self._write_json(history_path, payload)
        self._write_json(self.ranking_dir / "latest.json", {"time": payload["scanTime"], "ranking": payload["ranking"]})
        self._write_json(self.ranking_dir / "top10.json", {"time": payload["scanTime"], "ranking": payload["top10"]})
        self._write_json(self.ranking_dir / "top20.json", {"time": payload["scanTime"], "ranking": payload["top20"]})
        self._write_json(self.ranking_dir / "leading.json", {"time": payload["scanTime"], "ranking": payload["leading"]})
        self._write_json(self.ranking_dir / "altscore.json", {"time": payload["scanTime"], "altSeasonIndex": report.alt_season_index})
        self._write_json(self.dashboard_dir / "dashboard.json", payload)
        self._write_json(self.dashboard_dir / "summary.json", self._summary_payload(report))
        self._write_json(self.dashboard_dir / "trend.json", self._trend_payload())
        self._write_json(self.dashboard_dir / "heatmap.json", self._heatmap_payload(report))
        (self.dashboard_dir / "index.html").write_text(DASHBOARD_HTML, encoding="utf-8")

    def leading_scores(self) -> dict[str, float]:
        events: dict[str, list[bool]] = {}
        previous_payload: dict[str, Any] | None = None
        for path in sorted(self.history_dir.glob("*/*/*/*.json")):
            payload = self._read_json(path)
            if previous_payload and previous_payload.get("btcReturn", 0) < 0 and payload.get("btcReturn", 0) > 0:
                current_by_symbol = {str(row["symbol"]): row for row in payload.get("ranking", [])}
                for row in previous_payload.get("ranking", []):
                    symbol = str(row["symbol"])
                    if float(row.get("relativeScore", 0)) <= 0:
                        continue
                    current = current_by_symbol.get(symbol)
                    if current is None:
                        continue
                    events.setdefault(self._with_usdt(symbol), []).append(float(current.get("coinReturn", 0)) > 0)
            previous_payload = payload
        scores: dict[str, float] = {}
        for symbol, outcomes in events.items():
            if outcomes:
                scores[symbol] = round(sum(outcomes) / len(outcomes) * 100, 2)
        return scores

    def latest_results(self, limit: int | None = None) -> list[dict[str, Any]]:
        payload = self._read_json(self.ranking_dir / "latest.json")
        ranking = list(payload.get("ranking", [])) if payload else []
        return ranking[:limit] if limit is not None else ranking

    def latest_payload(self) -> dict[str, Any]:
        return self._read_json(self.dashboard_dir / "dashboard.json")

    def symbol_history(self, symbol: str, limit: int = 30) -> list[dict[str, Any]]:
        normalized = self._normalize_symbol(symbol)
        records: list[dict[str, Any]] = []
        for path in sorted(self.history_dir.glob("*/*/*/*.json"), reverse=True):
            payload = self._read_json(path)
            for row in payload.get("ranking", []):
                if self._normalize_symbol(str(row.get("symbol", ""))) == normalized:
                    records.append(row | {"scanTime": payload.get("scanTime")})
                    break
            if len(records) >= limit:
                break
        return records

    def previous_top10(self) -> set[str]:
        return {self._with_usdt(str(row["symbol"])) for row in self.latest_results(limit=10)}

    def previous_streaks(self) -> dict[str, tuple[int, int]]:
        return {
            self._with_usdt(str(row["symbol"])): (int(row.get("top10Streak", 0)), int(row.get("top20Streak", 0)))
            for row in self.latest_results()
        }

    def _report_payload(self, report: ScanReport) -> dict[str, Any]:
        ranking = [self._result_payload(result) for result in report.results]
        return {
            "scanTime": report.scan_time.isoformat(),
            "btcReturn": report.btc_return,
            "altSeasonIndex": report.alt_season_index,
            "top10": ranking[:10],
            "top20": ranking[:20],
            "ranking": ranking,
            "newEntries": [self._strip_usdt(symbol) for symbol in report.new_entries],
            "volumeSpikes": [self._strip_usdt(symbol) for symbol in report.volume_spikes],
            "leading": sorted(ranking, key=lambda row: row["leadingScore"], reverse=True)[:20],
            "recommended": [row["symbol"] for row in ranking[:3]],
        }

    def _result_payload(self, result: ScanResult) -> dict[str, Any]:
        raw = asdict(result)
        return {
            "rank": raw["rank"],
            "symbol": self._strip_usdt(raw["symbol"]),
            "scanTime": result.scan_time.isoformat(),
            "btcReturn": raw["btc_return"],
            "coinReturn": raw["coin_return"],
            "relativeScore": raw["relative_score"],
            "cumulativeRelativeScore": raw["cumulative_relative_score"],
            "aiScore": raw["ai_score"],
            "score": raw["ai_score"],
            "volumeScore": raw["volume_score"],
            "trendScore": raw["trend_score"],
            "leadingScore": raw["leading_score"],
            "volatilityScore": raw["volatility_score"],
            "top10Streak": raw["top10_streak"],
            "top20Streak": raw["top20_streak"],
        }

    def _summary_payload(self, report: ScanReport) -> dict[str, Any]:
        leader = report.top10[0].symbol.replace("USDT", "") if report.top10 else None
        return {
            "scanTime": report.scan_time.isoformat(),
            "btcReturn": report.btc_return,
            "altSeasonIndex": report.alt_season_index,
            "leader": leader,
            "newEntries": [self._strip_usdt(symbol) for symbol in report.new_entries],
            "recommended": [item.symbol.replace("USDT", "") for item in report.top10[:3]],
        }

    def _trend_payload(self) -> dict[str, Any]:
        rows = []
        for path in sorted(self.history_dir.glob("*/*/*/*.json"))[-30:]:
            payload = self._read_json(path)
            rows.append(
                {
                    "scanTime": payload.get("scanTime"),
                    "btcReturn": payload.get("btcReturn"),
                    "altSeasonIndex": payload.get("altSeasonIndex"),
                    "leader": payload.get("top10", [{}])[0].get("symbol") if payload.get("top10") else None,
                }
            )
        return {"trend": rows}

    def _heatmap_payload(self, report: ScanReport) -> dict[str, Any]:
        return {
            "scanTime": report.scan_time.isoformat(),
            "items": [
                {"symbol": row.symbol.replace("USDT", ""), "relativeScore": row.relative_score, "aiScore": row.ai_score}
                for row in report.top20
            ],
        }

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _strip_usdt(symbol: str) -> str:
        return symbol.removesuffix("USDT")

    @staticmethod
    def _with_usdt(symbol: str) -> str:
        return symbol if symbol.endswith("USDT") else f"{symbol}USDT"

    @classmethod
    def _normalize_symbol(cls, symbol: str) -> str:
        return cls._strip_usdt(symbol.upper())
