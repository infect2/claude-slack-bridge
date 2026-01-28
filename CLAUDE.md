# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Slack bot that bridges Slack messages to the Claude CLI tool, allowing users to interact with Claude through Slack.

- **claude_slack_bridge.py** — `subprocess.run`으로 Claude CLI를 호출하고, Slack Socket Mode로 메시지를 주고받는 구현

Slack Socket Mode (not HTTP webhooks)를 사용하며, `claude` CLI binary와 통신합니다.

## Running

```bash
pip install slack-bolt python-dotenv
python claude_slack_bridge.py
```

Requires `claude` CLI to be in PATH.

## Environment Variables

`.env` 파일 또는 환경 변수로 다음 값을 설정해야 합니다:

- `SLACK_APP_TOKEN` — Slack App-level token (`xapp-...`)
- `SLACK_BOT_TOKEN` — Slack Bot token (`xoxb-...`)
- `TARGET_CHANNEL_ID` — 메시지를 수신할 Slack 채널 ID

`python-dotenv`를 사용하여 `.env` 파일에서 자동 로드합니다.

## Architecture

1. Slack Socket Mode로 대상 채널의 메시지를 수신
2. 사용자 메시지를 `claude -p --dangerously-skip-permissions` 명령으로 실행
3. Claude CLI 출력을 Slack에 전송 (터미널에도 동시 출력)
4. `-c` 플래그로 대화 컨텍스트를 유지 (세션 지속)
5. `!new` 명령으로 세션 리셋 가능

## Key Behaviors

- 응답이 3900자를 초과하면 truncate 처리
- CLI 타임아웃: 120초
- 봇 자신의 메시지는 무시 (`bot_id` 체크)
