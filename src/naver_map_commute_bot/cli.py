from __future__ import annotations

import argparse
import os
import sys

import requests

from naver_map_commute_bot.batch import BatchConfig, run_batch
from naver_map_commute_bot.client import NaverDirectionsClient
from naver_map_commute_bot.slack import SlackWebhookClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NAVER Maps commute batch")
    parser.add_argument("--send", action="store_true", help="Send the result to Slack webhook")
    return parser


def build_config(*, send_slack: bool) -> BatchConfig:
    try:
        mileage = float(os.environ.get("ROUTE_MILEAGE", "14"))
    except ValueError as exc:
        raise ValueError("ROUTE_MILEAGE must be a number") from exc

    return BatchConfig(
        start_name=os.environ.get("ROUTE_START_NAME", "일산 Sphere"),
        start=os.environ.get("ROUTE_START", "126.77801150878531,37.658031591237425"),
        goal_name=os.environ.get("ROUTE_GOAL_NAME", "수명산 파크"),
        goal=os.environ.get("ROUTE_GOAL", "126.82325269403174,37.55138140215686"),
        fuel_type=os.environ.get("ROUTE_FUEL_TYPE", "gasoline"),
        mileage=mileage,
        route_option=os.environ.get("ROUTE_OPTION", "traoptimal"),
        language=os.environ.get("ROUTE_LANG", "ko"),
        send_slack=send_slack,
    )


def main(argv: list[str] | None = None) -> None:
    try:
        args = build_parser().parse_args(argv)
        config = build_config(send_slack=args.send)
        directions = NaverDirectionsClient(
            api_key_id=os.environ["NAVER_MAP_API_KEY_ID"],
            api_key=os.environ["NAVER_MAP_API_KEY"],
        )
        slack = SlackWebhookClient(os.environ["SLACK_WEBHOOK_URL"]) if args.send else None
        result = run_batch(config=config, directions_client=directions, slack_client=slack)
    except KeyError as exc:
        print(f"Missing required environment variable: {exc.args[0]}", file=sys.stderr)
        raise SystemExit(2) from exc
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except requests.RequestException as exc:
        print(f"NAVER Maps request failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(result.message)


if __name__ == "__main__":
    main()
