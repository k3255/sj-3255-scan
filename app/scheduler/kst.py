from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


KST_SCAN_HOURS = {1, 5, 9, 13, 17, 21}


def is_scan_window(now: datetime | None = None) -> bool:
    current = now or datetime.now(tz=ZoneInfo("Asia/Seoul"))
    return current.hour in KST_SCAN_HOURS and 2 <= current.minute <= 8
