from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from naver_map_commute_bot.app import ApiResponseError
from naver_map_commute_bot.batch import BatchConfig, run_batch
from naver_map_commute_bot.client import NaverDirectionsClient
from naver_map_commute_bot.slack import SlackWebhookClient

KST = ZoneInfo("Asia/Seoul")

MORNING_ROUTE = {
    "commute_label": "오전 출근길",
    "title_emoji": "🌅",
    "start_name": "운정자이 시그니처",
    "start": "126.7295793,37.7236352",
    "goal_name": "FITI시험연구원",
    "goal": "126.8385696,37.5684853",
}

EVENING_ROUTE = {
    "commute_label": "오후 퇴근길",
    "title_emoji": "🌆",
    "start_name": "FITI시험연구원",
    "start": "126.8385696,37.5684853",
    "goal_name": "운정자이 시그니처",
    "goal": "126.7295793,37.7236352",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NAVER Maps commute batch")
    parser.add_argument("--send", action="store_true", help="Send the result to Slack webhook")
    parser.add_argument("--mode", choices=["morning", "evening"], help="Override route direction")
    return parser


class ConfigError(ValueError):
    pass


def build_config(*, send_slack: bool, now: datetime | None = None, mode: str | None = None) -> BatchConfig:
    try:
        mileage = float(os.environ.get("ROUTE_MILEAGE", "14"))
    except ValueError as exc:
        raise ConfigError("ROUTE_MILEAGE must be a number") from exc
    if mileage <= 0:
        raise ConfigError("ROUTE_MILEAGE must be a positive number")

    current = now.astimezone(KST) if now else datetime.now(tz=KST)
    selected_mode = mode or ("morning" if current.hour < 12 else "evening")
    route = MORNING_ROUTE if selected_mode == "morning" else EVENING_ROUTE

    return BatchConfig(
        commute_label=route["commute_label"],
        start_name=route["start_name"],
        start=route["start"],
        goal_name=route["goal_name"],
        goal=route["goal"],
        title_emoji=route["title_emoji"],
        snapshot_time=current.strftime("%H:%M"),
        fuel_type=os.environ.get("ROUTE_FUEL_TYPE", "gasoline"),
        mileage=mileage,
        route_option=os.environ.get("ROUTE_OPTION", "traoptimal"),
        language=os.environ.get("ROUTE_LANG", "ko"),
        send_slack=send_slack,
    )


def main(argv: list[str] | None = None) -> None:
    try:
        args = build_parser().parse_args(argv)
        config = build_config(send_slack=args.send, mode=args.mode)
        api_key_id = os.environ["NAVER_MAP_API_KEY_ID"]
        api_key = os.environ["NAVER_MAP_API_KEY"]
        slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL") if args.send else None
        if args.send and not slack_webhook_url:
            raise ConfigError("SLACK_WEBHOOK_URL must be set when using --send")
    except KeyError as exc:
        print(f"Missing required environment variable: {exc.args[0]}", file=sys.stderr)
        raise SystemExit(2) from exc
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    directions = NaverDirectionsClient(
        api_key_id=api_key_id,
        api_key=api_key,
    )
    slack = SlackWebhookClient(slack_webhook_url) if slack_webhook_url else None

    try:
        result = run_batch(config=config, directions_client=directions, slack_client=slack)
    except ApiResponseError as exc:
        print(f"API response error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except requests.RequestException as exc:
        print(f"NAVER Maps request failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(result.message)


if __name__ == "__main__":
    main()
