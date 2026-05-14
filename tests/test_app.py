from __future__ import annotations

import pytest

from naver_map_commute_bot.app import (
    RouteSummary,
    build_message,
    build_slack_payload,
    extract_route_summary,
    summarize_route_guides,
)


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


def test_build_message_includes_timestamped_emoji_title_eta_and_costs() -> None:
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

    message = build_message(
        snapshot_time="08:45",
        title_emoji="🌅",
        start_name="운정자이 시그니처",
        goal_name="FITI시험연구원",
        summary=summary,
        via_summary="탑골IC → 법곳IC → 이산포분기점",
    )

    lines = message.splitlines()
    assert lines[0] == "🌅 08:45 | 운정자이 시그니처 → FITI시험연구원"
    assert "90분" in lines[1]
    assert "10,321원" in lines[1]
    assert "38.5km" in lines[1]
    assert lines[2] == "경유: 탑골IC → 법곳IC → 이산포분기점"


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

    payload = build_slack_payload(
        snapshot_time="08:45",
        title_emoji="🌅",
        start_name="운정자이 시그니처",
        goal_name="FITI시험연구원",
        summary=summary,
        via_summary="탑골IC → 법곳IC",
    )

    assert payload["text"].startswith("🌅 08:45")
    assert payload["blocks"][0]["type"] == "section"
    assert "경유: 탑골IC → 법곳IC" in payload["blocks"][0]["text"]["text"]


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

    payload = build_slack_payload(
        snapshot_time="17:15",
        title_emoji="🌆",
        start_name="FITI시험연구원",
        goal_name="운정자이 시그니처",
        summary=summary,
        via_summary="가양대교 → 장월IC",
    )

    assert "통행료 4,500원" in payload["blocks"][0]["text"]["text"]


def test_summarize_route_guides_returns_named_waypoints_only() -> None:
    via = summarize_route_guides(
        [
            {"instructions": "탑골IC에서 '서울, 제2자유로' 방면으로 왼쪽 방향"},
            {"instructions": "법곳IC에서 '김포, 킨텍스' 방면으로 지하차도 오른쪽 옆길"},
            {"instructions": "우회전"},
            {"instructions": "이산포분기점에서 '서울, 장항IC' 방면으로 오른쪽 방향"},
            {"instructions": "오른쪽 방향"},
        ]
    )

    assert via == "탑골IC → 법곳IC → 이산포분기점"


def test_extract_route_summary_raises_clear_error_when_route_missing() -> None:
    with pytest.raises(ValueError, match="No route"):
        extract_route_summary({"route": {"traoptimal": []}})
