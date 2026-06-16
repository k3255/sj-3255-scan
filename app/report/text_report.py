from __future__ import annotations

from zoneinfo import ZoneInfo

from app.domain.models import ScanReport


def render_text_report(report: ScanReport) -> str:
    kst_time = report.scan_time.astimezone(ZoneInfo("Asia/Seoul"))
    top10 = "\n".join(
        (
            f"{item.rank}. {item.symbol.replace('USDT', '')} "
            f"| AI {item.ai_score:.1f}점 "
            f"| BTC 대비 {item.relative_score:+.2f}%"
        )
        for item in report.top10
    )
    new_entries = ", ".join(symbol.replace("USDT", "") for symbol in report.new_entries) or "-"
    strong = ", ".join(
        f"{item.symbol.replace('USDT', '')}({item.top10_streak}회)"
        for item in report.top10
        if item.top10_streak >= 2
    ) or "-"
    volume = ", ".join(symbol.replace("USDT", "") for symbol in report.volume_spikes) or "-"
    picks = ", ".join(item.symbol.replace("USDT", "") for item in report.top10[:3])
    market_comment = _alt_season_comment(report.alt_season_index)
    btc_comment = "BTC가 약보합/하락 중입니다." if report.btc_return < 0 else "BTC가 상승 중입니다."
    return (
        "BTC 상대강도 스캐너\n\n"
        f"기준 시간\nKST {kst_time:%Y-%m-%d %H:%M}\n\n"
        f"BTC 변동률\n{report.btc_return:+.2f}%\n"
        f"해석: {btc_comment} 아래 코인들은 이 구간에서 BTC보다 상대적으로 강했던 순서입니다.\n\n"
        f"AI TOP10\n{top10}\n"
        "해석: AI 점수는 상대강도, 최근 5봉 지속성, 거래량, EMA 추세, 변동성 안정성을 합산한 100점 기준 점수입니다.\n\n"
        f"신규 진입\n{new_entries}\n"
        "해석: 직전 스캔 TOP10에는 없었지만 이번 스캔에서 TOP10에 새로 들어온 코인입니다.\n\n"
        f"연속 강세\n{strong}\n"
        "해석: 여러 번 연속으로 TOP10에 남아 있는 코인입니다. 숫자가 높을수록 단기 강세가 지속 중입니다.\n\n"
        f"거래량 급증\n{volume}\n"
        "해석: 최근 평균 대비 거래대금 증가가 큰 코인입니다. '-'이면 뚜렷한 거래량 급증 신호가 없다는 뜻입니다.\n\n"
        f"알트 시즌 지수\n{report.alt_season_index:.0f}/100\n"
        f"해석: 전체 분석 코인 중 BTC보다 강한 코인의 비율입니다. 현재 상태는 '{market_comment}'입니다.\n\n"
        f"관심 후보\n{picks}\n"
        "해석: 이번 스캔 기준 최상위 후보입니다. 매수 신호가 아니라 추가 관찰 우선순위입니다."
    )


def _alt_season_comment(score: float) -> str:
    if score >= 80:
        return "강한 알트 시장"
    if score >= 60:
        return "알트 강세장"
    if score >= 40:
        return "중립"
    if score >= 20:
        return "약세장"
    return "강한 BTC 우위"
