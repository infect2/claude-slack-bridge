# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Slack bot that bridges Slack messages to the Claude CLI tool, allowing users to interact with Claude through Slack.

- **claude_slack_bridge.py** — `subprocess.run`으로 Claude CLI를 호출하고, Slack Socket Mode로 메시지를 주고받는 구현

Slack Socket Mode (not HTTP webhooks)를 사용하며, `claude` CLI binary와 통신합니다.

## Running

```bash
pip install slack-bolt
python claude_slack_bridge.py
```

Requires `claude` CLI to be in PATH.

## Architecture

1. Slack Socket Mode로 대상 채널의 메시지를 수신
2. 사용자 메시지를 `claude -p` 명령으로 실행
3. Claude CLI 출력을 Slack에 전송 (터미널에도 동시 출력)

Slack tokens and target channel ID are hardcoded in the file.
