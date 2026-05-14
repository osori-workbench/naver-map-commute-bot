from __future__ import annotations

from naver_map_commute_bot.client import NaverDirectionsClient


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.status_code = 200
        self.text = "ok"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class DummySession:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def get(self, url: str, *, headers: dict, params: dict, timeout: int) -> DummyResponse:
        self.calls.append({
            "url": url,
            "headers": headers,
            "params": params,
            "timeout": timeout,
        })
        return DummyResponse(self.payload)


def test_client_calls_current_map_direction_endpoint_with_expected_query() -> None:
    session = DummySession(payload={"code": 0, "route": {"traoptimal": [{"summary": {"duration": 1, "distance": 1, "fuelPrice": 1, "tollFare": 0}}]}})
    client = NaverDirectionsClient(api_key_id="key-id", api_key="key", session=session)

    payload = client.fetch(start="126.7780,37.6580", goal="126.8232,37.5513", fuel_type="gasoline", mileage=12.4)

    assert payload["code"] == 0
    assert session.calls == [
        {
            "url": "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving",
            "headers": {
                "x-ncp-apigw-api-key-id": "key-id",
                "x-ncp-apigw-api-key": "key",
            },
            "params": {
                "start": "126.7780,37.6580",
                "goal": "126.8232,37.5513",
                "option": "traoptimal",
                "fueltype": "gasoline",
                "mileage": "12.4",
                "lang": "ko",
            },
            "timeout": 20,
        }
    ]
