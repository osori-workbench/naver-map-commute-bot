from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

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


def test_build_config_rejects_non_positive_mileage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROUTE_MILEAGE", "0")

    with pytest.raises(ValueError, match="positive"):
        cli.build_config(send_slack=False)


def test_main_exits_with_api_response_error_when_payload_shape_is_invalid(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("NAVER_MAP_API_KEY_ID", "id")
    monkeypatch.setenv("NAVER_MAP_API_KEY", "key")

    class BrokenPayloadClient(StubDirectionsClient):
        def fetch(self, **kwargs):
            return {"route": {"traoptimal": [{"summary": {}}]}}

    monkeypatch.setattr(cli, "NaverDirectionsClient", BrokenPayloadClient)
    monkeypatch.setattr(cli, "SlackWebhookClient", StubSlackClient)

    with pytest.raises(SystemExit) as exc:
        cli.main([])

    assert exc.value.code == 1
    assert "API response error" in capsys.readouterr().err


def test_main_rejects_empty_slack_webhook_when_send_enabled(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("NAVER_MAP_API_KEY_ID", "id")
    monkeypatch.setenv("NAVER_MAP_API_KEY", "key")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "")
    monkeypatch.setattr(cli, "NaverDirectionsClient", StubDirectionsClient)
    monkeypatch.setattr(cli, "SlackWebhookClient", StubSlackClient)

    with pytest.raises(SystemExit) as exc:
        cli.main(["--send"])

    assert exc.value.code == 2
    assert "SLACK_WEBHOOK_URL" in capsys.readouterr().err


def test_main_exits_with_api_response_error_when_payload_is_not_a_dict(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("NAVER_MAP_API_KEY_ID", "id")
    monkeypatch.setenv("NAVER_MAP_API_KEY", "key")

    class NonDictPayloadClient(StubDirectionsClient):
        def fetch(self, **kwargs):
            return None

    monkeypatch.setattr(cli, "NaverDirectionsClient", NonDictPayloadClient)
    monkeypatch.setattr(cli, "SlackWebhookClient", StubSlackClient)

    with pytest.raises(SystemExit) as exc:
        cli.main([])

    assert exc.value.code == 1
    assert "API response error" in capsys.readouterr().err


def test_main_exits_with_api_response_error_when_route_field_is_not_an_object(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("NAVER_MAP_API_KEY_ID", "id")
    monkeypatch.setenv("NAVER_MAP_API_KEY", "key")

    class BrokenRouteClient(StubDirectionsClient):
        def fetch(self, **kwargs):
            return {"route": None}

    monkeypatch.setattr(cli, "NaverDirectionsClient", BrokenRouteClient)
    monkeypatch.setattr(cli, "SlackWebhookClient", StubSlackClient)

    with pytest.raises(SystemExit) as exc:
        cli.main([])

    assert exc.value.code == 1
    assert "API response error" in capsys.readouterr().err


def test_build_config_selects_morning_route_before_noon() -> None:
    config = cli.build_config(
        send_slack=False,
        now=datetime(2026, 5, 14, 8, 45, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert config.commute_label == "오전 출근길"
    assert config.start_name == "운정자이 시그니처"
    assert config.goal_name == "FITI시험연구원"
    assert config.start == "126.7295793,37.7236352"
    assert config.goal == "126.8385696,37.5684853"


def test_build_config_selects_evening_route_after_noon() -> None:
    config = cli.build_config(
        send_slack=False,
        now=datetime(2026, 5, 14, 17, 15, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert config.commute_label == "오후 퇴근길"
    assert config.start_name == "FITI시험연구원"
    assert config.goal_name == "운정자이 시그니처"
    assert config.start == "126.8385696,37.5684853"
    assert config.goal == "126.7295793,37.7236352"


def test_build_config_respects_explicit_route_mode_over_current_time() -> None:
    config = cli.build_config(
        send_slack=False,
        now=datetime(2026, 5, 14, 17, 15, tzinfo=ZoneInfo("Asia/Seoul")),
        mode="morning",
    )

    assert config.commute_label == "오전 출근길"
    assert config.start_name == "운정자이 시그니처"
    assert config.goal_name == "FITI시험연구원"
