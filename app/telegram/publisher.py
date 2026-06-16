from __future__ import annotations

import time
from pathlib import Path

import httpx


class TelegramPublisher:
    def __init__(self, token: str | None, chat_id: str | None, timeout: int = 60, max_retries: int = 3) -> None:
        self.token = token
        self.chat_id = chat_id
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def publish(self, text: str, image_path: Path | None = None) -> bool:
        if not self.enabled:
            return False
        assert self.token is not None
        assert self.chat_id is not None
        base = f"https://api.telegram.org/bot{self.token}"
        try:
            self._with_retries(lambda: self._send_message(base, text))
            if image_path and image_path.exists():
                self._with_retries(lambda: self._send_photo(base, image_path))
        except httpx.HTTPError as exc:
            print(f"Telegram publish failed after retries: {exc}")
            return False
        return True

    def _send_message(self, base: str, text: str) -> None:
        with httpx.Client(timeout=self.timeout) as client:
            client.post(f"{base}/sendMessage", data={"chat_id": self.chat_id, "text": text}).raise_for_status()

    def _send_photo(self, base: str, image_path: Path) -> None:
        with httpx.Client(timeout=self.timeout) as client:
            with image_path.open("rb") as image_file:
                client.post(
                    f"{base}/sendPhoto",
                    data={"chat_id": self.chat_id},
                    files={"photo": image_file},
                ).raise_for_status()

    def _with_retries(self, operation) -> None:
        last_error: httpx.HTTPError | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                operation()
                return
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2 * attempt)
        if last_error is not None:
            raise last_error
