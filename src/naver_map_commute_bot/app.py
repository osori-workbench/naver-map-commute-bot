from __future__ import annotations

import re
from dataclasses import dataclass


class ApiResponseError(ValueError):
    pass


@dataclass(frozen=True)
class RouteSummary:
    duration_minutes: int
    distance_km: float
    fuel_price: int
    toll_fare: int


def extract_route_summary(response: dict, *, route_option: str = "traoptimal") -> RouteSummary:
    route = _extract_route(response, route_option=route_option)
    summary = route.get("summary")
    if not isinstance(summary, dict):
        raise ApiResponseError("Invalid NAVER Maps response: missing summary object")

    try:
        duration = summary["duration"]
        distance = summary["distance"]
        fuel_price = summary["fuelPrice"]
    except KeyError as exc:
        raise ApiResponseError(f"Invalid NAVER Maps response: missing field '{exc.args[0]}'") from exc

    return RouteSummary(
        duration_minutes=round(duration / 1000 / 60),
        distance_km=round(distance / 1000, 1),
        fuel_price=int(fuel_price),
        toll_fare=int(summary.get("tollFare", 0)),
    )


def summarize_route_guides(guides: list[dict], *, limit: int = 3) -> str:
    names: list[str] = []
    for guide in guides:
        instruction = guide.get("instructions")
        if not isinstance(instruction, str):
            continue
        name = _extract_waypoint_name(instruction)
        if not name or name in {"회전교차로", "교차로"} or name in names:
            continue
        names.append(name)
        if len(names) >= limit:
            break
    return " → ".join(names)


def build_message(
    *,
    snapshot_time: str,
    title_emoji: str,
    start_name: str,
    goal_name: str,
    summary: RouteSummary,
    via_summary: str = "",
) -> str:
    cost_line = f"{summary.duration_minutes}분 · {summary.distance_km:.1f}km · 기름값 {summary.fuel_price:,}원"
    if summary.toll_fare:
        cost_line += f" · 통행료 {summary.toll_fare:,}원"

    lines = [
        f"{title_emoji} {snapshot_time} | {start_name} → {goal_name}",
        cost_line,
    ]
    if via_summary:
        lines.append(f"경유: {via_summary}")
    return "\n".join(lines)


def build_slack_payload(
    *,
    snapshot_time: str,
    title_emoji: str,
    start_name: str,
    goal_name: str,
    summary: RouteSummary,
    via_summary: str = "",
) -> dict:
    message = build_message(
        snapshot_time=snapshot_time,
        title_emoji=title_emoji,
        start_name=start_name,
        goal_name=goal_name,
        summary=summary,
        via_summary=via_summary,
    )
    return {
        "text": message,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message.replace("\n", "\n"),
                },
            }
        ],
    }


def _extract_route(response: dict, *, route_option: str) -> dict:
    if not isinstance(response, dict):
        raise ApiResponseError("Invalid NAVER Maps response: expected a JSON object")
    route = response.get("route")
    if not isinstance(route, dict):
        raise ApiResponseError("Invalid NAVER Maps response: missing route object")
    routes = route.get(route_option, [])
    if not routes:
        raise ApiResponseError(f"No route returned from NAVER Maps driving API for option '{route_option}'")
    if not isinstance(routes[0], dict):
        raise ApiResponseError("Invalid NAVER Maps response: invalid route entry")
    return routes[0]


def _extract_waypoint_name(instruction: str) -> str | None:
    leading_match = re.search(r"^([가-힣A-Za-z0-9]+(?:IC|JC|TG|분기점|교차로|대교|역))에서", instruction)
    if leading_match:
        return leading_match.group(1)
    ic_match = re.search(r"([가-힣A-Za-z0-9]+(?:IC|JC|TG))", instruction)
    if ic_match:
        return ic_match.group(1)
    named_match = re.search(r"([가-힣A-Za-z0-9]+(?:분기점|교차로|대교|역))", instruction)
    if named_match:
        return named_match.group(1)
    road_match = re.search(r"(제2자유로|자유로|강변북로|올림픽대로)", instruction)
    if road_match:
        return road_match.group(1)
    return None
