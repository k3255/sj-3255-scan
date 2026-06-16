from __future__ import annotations

from pathlib import Path

from app.domain.models import ScanReport


class ImageReportGenerator:
    def __init__(self, report_dir: Path) -> None:
        self.report_dir = report_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, report: ScanReport) -> Path | None:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            return None

        symbols = [item.symbol.replace("USDT", "") for item in report.top10]
        scores = [item.ai_score for item in report.top10]
        colors = ["#008f70" if item.relative_score >= 0 else "#c2413b" for item in report.top10]
        fig, ax = plt.subplots(figsize=(12, 9))
        fig.patch.set_facecolor("#f7f8fa")
        ax.set_facecolor("#ffffff")
        ax.barh(symbols[::-1], scores[::-1], color=colors[::-1])
        ax.set_xlim(0, 100)
        ax.set_xlabel("AI Score")
        ax.set_title(
            f"BTC Relative Strength | BTC {report.btc_return:+.2f}% | Alt Season {report.alt_season_index:.0f}",
            pad=18,
            weight="bold",
        )
        for index, item in enumerate(report.top10[::-1]):
            label = (
                f"AI {item.ai_score:.1f}  RS {item.relative_score:+.2f}  "
                f"T10 {item.top10_streak}  VOL {item.volume_score:.0f}"
            )
            ax.text(min(item.ai_score + 1, 96), index, label, va="center", fontsize=9)
        ax.grid(axis="x", color="#d9dee7", linewidth=0.8)
        ax.spines[["top", "right", "left"]].set_visible(False)
        fig.text(0.02, 0.02, f"Generated {report.scan_time.isoformat()}", fontsize=9, color="#687385")
        fig.tight_layout(rect=(0, 0.04, 1, 0.96))
        path = self.report_dir / f"{report.scan_time.strftime('%Y%m%d_%H%M')}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path
