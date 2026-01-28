import subprocess

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ==========================================
# [설정] 토큰 및 채널 ID
# ==========================================
SLACK_APP_TOKEN = "xapp-1-A0AB5DR0BM4-10366067207607-4d2f2209cd27a2f0dac84d18c1705a160c313edaef77a9f751070e531380c291"
SLACK_BOT_TOKEN = "xoxb-588388487269-10394435692193-DjYxb4N3JcuqDQbfA28R5kSo"
TARGET_CHANNEL_ID = "C0AB152FV7V"

app = App(token=SLACK_BOT_TOKEN)


@app.event("message")
def handle_message(body, say):
    event = body.get("event", {})
    channel_id = event.get("channel")
    text = event.get("text", "")

    if "bot_id" in event or channel_id != TARGET_CHANNEL_ID:
        return
    if not text.strip():
        return

    print(f"[Slack Input] ➤ {text}")

    try:
        result = subprocess.run(
            ["claude", "-p", text],
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = result.stdout.strip()
        if output:
            # Slack 메시지 길이 제한 (약 4000자)
            if len(output) > 3900:
                output = output[:3900] + "\n... (truncated)"
            print(f"[Slack Output] ➤\n{output}")
            say(output)
        elif result.stderr.strip():
            err_msg = f"⚠️ Error: {result.stderr.strip()[:500]}"
            print(f"[Slack Output] ➤ {err_msg}")
            say(err_msg)
        else:
            print("[Slack Output] ➤ (응답 없음)")
            say("(응답 없음)")

    except subprocess.TimeoutExpired:
        msg = "⏱️ Timeout: 120초 내에 응답이 없습니다."
        print(f"[Slack Output] ➤ {msg}")
        say(msg)
    except FileNotFoundError:
        msg = "⚠️ `claude` CLI를 찾을 수 없습니다. PATH를 확인하세요."
        print(f"[Slack Output] ➤ {msg}")
        say(msg)
    except Exception as e:
        msg = f"⚠️ 오류 발생: {str(e)[:500]}"
        print(f"[Slack Output] ➤ {msg}")
        say(msg)


if __name__ == "__main__":
    print(f"🚀 Claude Bridge Active on {TARGET_CHANNEL_ID}")
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
