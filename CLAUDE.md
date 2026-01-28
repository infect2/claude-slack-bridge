# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Slack bot that bridges Slack messages to the Claude CLI tool, allowing users to interact with Claude through Slack. There are two implementations:

- **claude_slack_bridge.py** — Uses `pexpect` for turn-based interaction with Claude CLI (waits for prompt before reading output)
- **claude_slack_bridge2.py** — Uses `pty` + `subprocess` with threaded streaming output (non-blocking reads via `select.select()`, buffers by time/size)

Both use Slack Socket Mode (not HTTP webhooks) and communicate with the `claude` CLI binary (not the API directly).

## Running

```bash
pip install slack-bolt pexpect
python claude_slack_bridge.py   # pexpect-based
python claude_slack_bridge2.py  # pty-based
```

Requires `claude` CLI to be in PATH.

## Architecture

Both implementations follow the same pattern:
1. Spawn a Claude CLI subprocess with terminal emulation
2. Listen for Slack messages in a target channel via Socket Mode
3. Forward user messages to Claude CLI as terminal input
4. Strip ANSI escape codes from Claude's output
5. Post cleaned output back to Slack as code blocks

Slack tokens and target channel ID are hardcoded in both files.
