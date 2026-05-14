from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteSummary:
    duration_minutes: int
    distance_km: float
    fuel_price: int
    toll_fare: int


def extract_route_summary(response: dict, *, route_option: str = "traoptimal") -> RouteSummary:
    routes = response.get("route", {}).get(route_option, [])
    if not routes:
        raise ValueError(f"No route returned from NAVER Maps driving API for option '{route_option}'")
    summary = routes[0]["summary"]
    return RouteSummary(
        duration_minutes=round(summary["duration"] / 1000 / 60),
        distance_km=round(summary["distance"] / 1000, 1),
        fuel_price=int(summary["fuelPrice"]),
        toll_fare=int(summary.get("tollFare", 0)),
    )


def build_message(*, start_name: str, goal_name: str, summary: RouteSummary) -> str:
    toll_suffix = f" · 통행료 {summary.toll_fare:,}원" if summary.toll_fare else ""
    return (
        f"지금 출발 기준 {start_name} → {goal_name} 예상 소요 {summary.duration_minutes}분"
        f" · 거리 {summary.distance_km:.1f}km · 기름값 {summary.fuel_price:,}원{toll_suffix}"
    )


def build_slack_payload(*, start_name: str, goal_name: str, summary: RouteSummary) -> dict:
    message = build_message(start_name=start_name, goal_name=goal_name, summary=summary)
    toll_line = f"\n\n*예상 통행료*\n{summary.toll_fare:,}원" if summary.toll_fare else ""
    return {
        "text": message,
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🏠 귀가 경로 브리핑"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*경로*\n{start_name} → {goal_name}\n\n"
                        f"*예상 소요*\n{summary.duration_minutes}분\n\n"
                        f"*예상 거리*\n{summary.distance_km:.1f}km\n\n"
                        f"*예상 기름값*\n{summary.fuel_price:,}원"
                        f"{toll_line}"
                    ),
                },
            },
        ],
    }
