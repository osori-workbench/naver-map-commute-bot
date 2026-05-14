#!/bin/bash
set -euo pipefail

PROJECT_DIR="/Users/osori/workbench/naver-map-commute-bot"
AGENT_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$AGENT_DIR" "$PROJECT_DIR/logs"

install_agent() {
  local src="$1"
  local dst="$AGENT_DIR/$(basename "$src")"
  local label
  label=$(/usr/libexec/PlistBuddy -c 'Print :Label' "$src")

  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  rm -f "$dst"
  cp "$src" "$dst"
  launchctl bootstrap "gui/$(id -u)" "$dst"
  launchctl enable "gui/$(id -u)/$label"
}

install_agent "$PROJECT_DIR/deploy/launchd/com.osori.naver-map-commute-bot.morning.plist"
install_agent "$PROJECT_DIR/deploy/launchd/com.osori.naver-map-commute-bot.evening.plist"

launchctl print "gui/$(id -u)/com.osori.naver-map-commute-bot.morning" >/dev/null
launchctl print "gui/$(id -u)/com.osori.naver-map-commute-bot.evening" >/dev/null

echo "Installed launchd agents:"
echo "- com.osori.naver-map-commute-bot.morning (08:45)"
echo "- com.osori.naver-map-commute-bot.evening (17:15)"
