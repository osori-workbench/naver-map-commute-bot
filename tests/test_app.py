from __future__ import annotations

import pytest

from naver_map_commute_bot.app import build_message, build_slack_payload, extract_route_summary


def test_extract_route_summary_reads_eta_distance_and_fuel_price() -> None:
    response = {
        "route": {
            "traoptimal": [
                {
                    "summary": {
                        "duration": 4860000,
                        "distance": 41750,
                        "fuelPrice": 11874,
                        "tollFare": 3200,
                    }
                }
            ]
        }
    }

    summary = extract_route_summary(response)

    assert summary.duration_minutes == 81
    assert summary.distance_km == 41.8
    assert summary.fuel_price == 11874
    assert summary.toll_fare == 3200


def test_build_message_includes_route_names_eta_and_costs() -> None:
    summary = extract_route_summary(
        {
            "route": {
                "traoptimal": [
                    {
                        "summary": {
                            "duration": 5400000,
                            "distance": 38540,
                            "fuelPrice": 10321,
                            "tollFare": 0,
                        }
                    }
                ]
            }
        }
    )

    message = build_message(start_name="일산 Sphere", goal_name="수명산 파크", summary=summary)

    assert "일산 Sphere" in message
    assert "수명산 파크" in message
    assert "90분" in message
    assert "10,321원" in message
    assert "38.5km" in message


def test_build_slack_payload_uses_blocks_and_plaintext_fallback() -> None:
    summary = extract_route_summary(
        {
            "route": {
                "traoptimal": [
                    {
                        "summary": {
                            "duration": 3720000,
                            "distance": 27110,
                            "fuelPrice": 8200,
                            "tollFare": 0,
                        }
                    }
                ]
            }
        }
    )

    payload = build_slack_payload(start_name="사무실", goal_name="집", summary=summary)

    assert payload["text"].startswith("지금 출발 기준")
    assert payload["blocks"][0]["type"] == "header"
    assert payload["blocks"][1]["type"] == "section"
    assert "예상 소요" in payload["blocks"][1]["text"]["text"]
    assert "예상 통행료" not in payload["blocks"][1]["text"]["text"]


def test_build_slack_payload_includes_toll_when_present() -> None:
    summary = extract_route_summary(
        {
            "route": {
                "traoptimal": [
                    {
                        "summary": {
                            "duration": 1000,
                            "distance": 1000,
                            "fuelPrice": 1000,
                            "tollFare": 4500,
                        }
                    }
                ]
            }
        }
    )

    payload = build_slack_payload(start_name="사무실", goal_name="집", summary=summary)

    assert "예상 통행료" in payload["blocks"][1]["text"]["text"]
    assert "4,500원" in payload["blocks"][1]["text"]["text"]


def test_extract_route_summary_raises_clear_error_when_route_missing() -> None:
    with pytest.raises(ValueError, match="No route"):
        extract_route_summary({"route": {"traoptimal": []}})
