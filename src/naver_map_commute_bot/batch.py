from __future__ import annotations

from dataclasses import dataclass

from naver_map_commute_bot.app import RouteSummary, build_message, build_slack_payload, extract_route_summary


@dataclass(frozen=True)
class BatchConfig:
    start_name: str
    start: str
    goal_name: str
    goal: str
    fuel_type: str = "gasoline"
    mileage: float = 14.0
    route_option: str = "traoptimal"
    language: str = "ko"
    send_slack: bool = False


@dataclass(frozen=True)
class BatchResult:
    message: str
    summary: RouteSummary
    payload: dict


def run_batch(*, config: BatchConfig, directions_client, slack_client=None) -> BatchResult:
    response = directions_client.fetch(
        start=config.start,
        goal=config.goal,
        fuel_type=config.fuel_type,
        mileage=config.mileage,
        option=config.route_option,
        lang=config.language,
    )
    summary = extract_route_summary(response, route_option=config.route_option)
    message = build_message(start_name=config.start_name, goal_name=config.goal_name, summary=summary)
    payload = build_slack_payload(start_name=config.start_name, goal_name=config.goal_name, summary=summary)
    if config.send_slack:
        if slack_client is None:
            raise ValueError("slack_client is required when send_slack=True")
        slack_client.send(payload)
    return BatchResult(message=message, summary=summary, payload=payload)
