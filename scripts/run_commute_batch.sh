#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/osori/workbench/naver-map-commute-bot"
ENV_FILE="$PROJECT_DIR/.env"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/launchd.log"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
MODE="${1:-}"

if [ -z "$MODE" ]; then
  echo "Usage: $0 <morning|evening>" >&2
  exit 2
fi

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

if [ ! -f "$ENV_FILE" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Missing .env file at $ENV_FILE" >> "$LOG_FILE"
  exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Missing python interpreter at $PYTHON_BIN" >> "$LOG_FILE"
  exit 1
fi

unset VIRTUAL_ENV
set -a
source "$ENV_FILE"
set +a

export PYTHONPATH="$PROJECT_DIR/src"

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting commute batch mode=$MODE"
  "$PYTHON_BIN" -m naver_map_commute_bot --send --mode "$MODE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Finished commute batch mode=$MODE"
} >> "$LOG_FILE" 2>&1
