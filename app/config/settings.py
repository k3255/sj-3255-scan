from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    exchange: str
    binance_fapi_base_url: str
    bitget_base_url: str
    bitget_product_type: str
    min_quote_volume: float
    min_listing_days: int
    scan_interval: str
    report_dir: Path
    enable_git_versioning: bool
    git_remote: str
    git_branch: str
    telegram_bot_token: str | None
    telegram_chat_id: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        return cls(
            data_dir=Path(os.getenv("DATA_DIR", "data")),
            exchange=os.getenv("EXCHANGE", "bitget").lower(),
            binance_fapi_base_url=os.getenv("BINANCE_FAPI_BASE_URL", "https://fapi.binance.com"),
            bitget_base_url=os.getenv("BITGET_BASE_URL", "https://api.bitget.com"),
            bitget_product_type=os.getenv("BITGET_PRODUCT_TYPE", "USDT-FUTURES"),
            min_quote_volume=float(os.getenv("MIN_QUOTE_VOLUME", "50000000")),
            min_listing_days=int(os.getenv("MIN_LISTING_DAYS", "14")),
            scan_interval=os.getenv("SCAN_INTERVAL", "4h"),
            report_dir=Path(os.getenv("REPORT_DIR", "data/report")),
            enable_git_versioning=os.getenv("ENABLE_GIT_VERSIONING", "false").lower() in {"1", "true", "yes"},
            git_remote=os.getenv("GIT_REMOTE", "origin"),
            git_branch=os.getenv("GIT_BRANCH", "main"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
        )
