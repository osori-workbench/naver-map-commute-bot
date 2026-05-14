from __future__ import annotations

from naver_map_commute_bot.batch import BatchConfig, run_batch


class StubDirectionsClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def fetch(self, **kwargs):
        self.calls.append(kwargs)
        return self.payload


class StubSlackClient:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def send(self, payload: dict) -> None:
        self.payloads.append(payload)


def test_run_batch_returns_message_and_sends_slack_payload() -> None:
    directions = StubDirectionsClient(
        {
            "route": {
                "traoptimal": [
                    {
                        "summary": {
                            "duration": 4500000,
                            "distance": 31020,
                            "fuelPrice": 9020,
                            "tollFare": 2300,
                        }
                    }
                ]
            }
        }
    )
    slack = StubSlackClient()
    config = BatchConfig(
        commute_label="오전 출근길",
        start_name="일산 Sphere",
        start="126.77801150878531,37.658031591237425",
        goal_name="수명산 파크",
        goal="126.82325269403174,37.55138140215686",
        fuel_type="gasoline",
        mileage=14.0,
        route_option="traoptimal",
        send_slack=True,
    )

    result = run_batch(config=config, directions_client=directions, slack_client=slack)

    assert "75분" in result.message
    assert result.summary.fuel_price == 9020
    assert result.via_summary == ""
    assert directions.calls == [
        {
            "start": "126.77801150878531,37.658031591237425",
            "goal": "126.82325269403174,37.55138140215686",
            "fuel_type": "gasoline",
            "mileage": 14.0,
            "option": "traoptimal",
            "lang": "ko",
        }
    ]
    assert len(slack.payloads) == 1
    assert slack.payloads[0]["text"] == result.message


def test_run_batch_skips_slack_when_disabled() -> None:
    directions = StubDirectionsClient(
        {
            "route": {
                "traavoidcaronly": [
                    {
                        "summary": {
                            "duration": 1200000,
                            "distance": 1000,
                            "fuelPrice": 500,
                            "tollFare": 0,
                        }
                    }
                ]
            }
        }
    )
    slack = StubSlackClient()
    config = BatchConfig(
        commute_label="오후 퇴근길",
        start_name="A",
        start="1,1",
        goal_name="B",
        goal="2,2",
        fuel_type="diesel",
        mileage=10.0,
        route_option="traavoidcaronly",
        send_slack=False,
    )

    result = run_batch(config=config, directions_client=directions, slack_client=slack)

    assert result.summary.duration_minutes == 20
    assert slack.payloads == []


def test_run_batch_reads_summary_from_requested_route_option() -> None:
    directions = StubDirectionsClient(
        {
            "route": {
                "traavoidcaronly": [
                    {
                        "summary": {
                            "duration": 1800000,
                            "distance": 5050,
                            "fuelPrice": 1900,
                            "tollFare": 0,
                        }
                    }
                ]
            }
        }
    )
    config = BatchConfig(
        commute_label="오후 퇴근길",
        start_name="A",
        start="1,1",
        goal_name="B",
        goal="2,2",
        route_option="traavoidcaronly",
        send_slack=False,
    )

    result = run_batch(config=config, directions_client=directions)

    assert result.summary.duration_minutes == 30
    assert "30분" in result.message
