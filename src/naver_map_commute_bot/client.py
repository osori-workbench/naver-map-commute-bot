from __future__ import annotations

from typing import Any

import requests


class NaverDirectionsClient:
    def __init__(self, *, api_key_id: str, api_key: str, session: requests.Session | Any | None = None) -> None:
        self.api_key_id = api_key_id
        self.api_key = api_key
        self.session = session or requests.Session()

    def fetch(
        self,
        *,
        start: str,
        goal: str,
        fuel_type: str = "gasoline",
        mileage: float = 14.0,
        option: str = "traoptimal",
        lang: str = "ko",
    ) -> dict[str, Any]:
        response = self.session.get(
            "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving",
            headers={
                "x-ncp-apigw-api-key-id": self.api_key_id,
                "x-ncp-apigw-api-key": self.api_key,
            },
            params={
                "start": start,
                "goal": goal,
                "option": option,
                "fueltype": fuel_type,
                "mileage": str(mileage),
                "lang": lang,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
