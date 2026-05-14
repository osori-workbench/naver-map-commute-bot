from __future__ import annotations

import os

import pytest
import requests

from naver_map_commute_bot import cli
from naver_map_commute_bot.batch import BatchConfig, BatchResult
from naver_map_commute_bot.app import RouteSummary


class StubDirectionsClient:
    def __init__(self, *, should_raise: Exception | None = None, **_: object) -> None:
        self.should_raise = should_raise

    def fetch(self, **kwargs):
        if self.should_raise:
            raise self.should_raise
        return {"route": {"traoptimal": [{"summary": {"duration": 60000, "distance": 1000, "fuelPrice": 500, "tollFare": 0}}]}}


class StubSlackClient:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send(self, payload: dict) -> None:
        return None


def test_main_exits_with_clear_message_when_required_env_missing(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("NAVER_MAP_API_KEY_ID", raising=False)
    monkeypatch.delenv("NAVER_MAP_API_KEY", raising=False)
    monkeypatch.setattr(cli, "NaverDirectionsClient", StubDirectionsClient)
    monkeypatch.setattr(cli, "SlackWebhookClient", StubSlackClient)

    with pytest.raises(SystemExit) as exc:
        cli.main([])

    assert exc.value.code == 2
    assert "Missing required environment variable" in capsys.readouterr().err


def test_main_exits_with_clear_message_when_request_fails(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("NAVER_MAP_API_KEY_ID", "id")
    monkeypatch.setenv("NAVER_MAP_API_KEY", "key")
    monkeypatch.setattr(cli, "NaverDirectionsClient", lambda **kwargs: StubDirectionsClient(should_raise=requests.Timeout("boom")))
    monkeypatch.setattr(cli, "SlackWebhookClient", StubSlackClient)

    with pytest.raises(SystemExit) as exc:
        cli.main([])

    assert exc.value.code == 1
    assert "NAVER Maps request failed" in capsys.readouterr().err


def test_build_config_rejects_invalid_mileage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROUTE_MILEAGE", "not-a-number")

    with pytest.raises(ValueError, match="ROUTE_MILEAGE"):
        cli.build_config(send_slack=False)
