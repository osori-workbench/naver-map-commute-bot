# naver-map-commute-bot

NAVER Maps 현행 `map-direction/v1/driving` API를 사용해 출발지→도착지 예상 소요 시간과 기름값을 계산하고, 필요하면 Slack webhook으로 전송하는 배치입니다.

## 기존 `gohome.ts`에서 바꾼 점
- 예전 코드: Next.js API route + `map-direction-15/v1/driving` + Slack bot token 직접 호출
- 현재 배치: 독립 실행형 Python CLI + 현행 `map-direction/v1/driving` + Slack incoming webhook
- 결과: 웹앱 없이도 로컬 cron/launchd/GitHub Actions 어디서든 바로 실행 가능

## 기본 동작
- 오전(08:45 실행): `운정자이 시그니처` → `FITI시험연구원`
- 오후(17:15 실행): `FITI시험연구원` → `운정자이 시그니처`
- 기본 경로 옵션: `traoptimal`
- 기본 연료 타입: `gasoline`
- 기본 연비: `14km/L`
- Slack 메시지는 2~3줄 요약으로 전송

## 환경변수
필수:
- `NAVER_MAP_API_KEY_ID`
- `NAVER_MAP_API_KEY`

Slack 전송 시 추가:
- `SLACK_WEBHOOK_URL`

선택:
- `ROUTE_START_NAME`
- `ROUTE_START`
- `ROUTE_GOAL_NAME`
- `ROUTE_GOAL`
- `ROUTE_FUEL_TYPE`
- `ROUTE_MILEAGE`
- `ROUTE_OPTION`
- `ROUTE_LANG`

## 실행
```bash
cd /Users/osori/workbench/naver-map-commute-bot
cp .env.example .env
# .env 값 입력 후
set -a
source .env
set +a
PYTHONPATH=src .venv/bin/python -m naver_map_commute_bot
```

Slack까지 보내려면:
```bash
PYTHONPATH=src .venv/bin/python -m naver_map_commute_bot --send
```

## 예시 출력
```text
지금 출발 기준 일산 Sphere → 수명산 파크 예상 소요 75분 · 거리 31.0km · 기름값 9,020원 · 통행료 2,300원
```

## 테스트
```bash
uv run --group dev pytest tests/ -q
```

## launchd 등록
설치 스크립트:
```bash
./scripts/install_launchd.sh
```

실행 wrapper:
```bash
./scripts/run_commute_batch.sh morning
./scripts/run_commute_batch.sh evening
```

등록되는 LaunchAgent:
- `com.osori.naver-map-commute-bot.morning` → 매일 `08:45`
- `com.osori.naver-map-commute-bot.evening` → 매일 `17:15`

로그 파일:
- `logs/launchd.log`
- `logs/launchd.stdout.log`
- `logs/launchd.stderr.log`
