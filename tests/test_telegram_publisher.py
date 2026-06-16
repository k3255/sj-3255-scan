from __future__ import annotations

import httpx

from app.telegram.publisher import TelegramPublisher


def test_telegram_publish_returns_false_after_retry_failure(monkeypatch) -> None:
    attempts = 0
    monkeypatch.setattr("app.telegram.publisher.time.sleep", lambda seconds: None)

    def fail() -> None:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("timeout")

    publisher = TelegramPublisher("token", "chat", max_retries=3)
    monkeypatch.setattr(publisher, "_send_message", lambda base, text: fail())

    assert publisher.publish("hello") is False
    assert attempts == 3


def test_telegram_publish_disabled_without_credentials() -> None:
    assert TelegramPublisher(None, None).publish("hello") is False
