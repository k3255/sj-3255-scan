from __future__ import annotations

from pathlib import Path

import httpx


class TelegramPublisher:
    def __init__(self, token: str | None, chat_id: str | None) -> None:
        self.token = token
        self.chat_id = chat_id

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def publish(self, text: str, image_path: Path | None = None) -> None:
        if not self.enabled:
            return
        assert self.token is not None
        assert self.chat_id is not None
        base = f"https://api.telegram.org/bot{self.token}"
        with httpx.Client(timeout=30) as client:
            client.post(f"{base}/sendMessage", data={"chat_id": self.chat_id, "text": text}).raise_for_status()
            if image_path and image_path.exists():
                with image_path.open("rb") as image_file:
                    client.post(
                        f"{base}/sendPhoto",
                        data={"chat_id": self.chat_id},
                        files={"photo": image_file},
                    ).raise_for_status()
