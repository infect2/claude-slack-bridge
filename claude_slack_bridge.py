import atexit
import os
import subprocess

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
TARGET_CHANNEL_ID = os.environ["TARGET_CHANNEL_ID"]

app = App(token=SLACK_BOT_TOKEN)

session_started = False
caffeinate_proc = None


def start_caffeinate():
    global caffeinate_proc
    if caffeinate_proc and caffeinate_proc.poll() is None:
        return
    caffeinate_proc = subprocess.Popen(["caffeinate", "-i"])
    print(f"[Caffeinate] ➤ 시작됨 (PID: {caffeinate_proc.pid})")


def stop_caffeinate():
    global caffeinate_proc
    if caffeinate_proc and caffeinate_proc.poll() is None:
        caffeinate_proc.terminate()
        caffeinate_proc.wait()
        print("[Caffeinate] ➤ 종료됨")
        caffeinate_proc = None


def cleanup_caffeinate():
    stop_caffeinate()


atexit.register(cleanup_caffeinate)


@app.event("message")
def handle_message(body, say):
    global session_started
    event = body.get("event", {})
    channel_id = event.get("channel")
    text = event.get("text", "")

    if "bot_id" in event or channel_id != TARGET_CHANNEL_ID:
        return
    if not text.strip():
        return

    if text.strip() == "!new":
        session_started = False
        print("[Session] ➤ 세션 리셋")
        say("🔄 세션이 리셋되었습니다. 새로운 대화를 시작합니다.")
        return

    if text.strip() == "!sleep":
        stop_caffeinate()
        say("😴 Sleep 모드 허용됨. 노트북이 자연스럽게 sleep에 들어갈 수 있습니다.\n`!awake`로 다시 sleep 방지를 활성화하세요.")
        return

    if text.strip() == "!awake":
        start_caffeinate()
        say("☀️ Sleep 방지 활성화됨. 노트북이 sleep에 들어가지 않습니다.")
        return

    print(f"[Slack Input] ➤ {text}")

    try:
        cmd = ["claude", "-p", "--dangerously-skip-permissions"]
        if session_started:
            cmd.append("-c")
        cmd.append(text)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        session_started = True

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
    start_caffeinate()
    print(f"🚀 Claude Bridge Active on {TARGET_CHANNEL_ID}")
    print("⚠️  WARNING: --dangerously-skip-permissions 모드로 실행 중입니다.")
    print("⚠️  Claude CLI가 파일 생성/수정/삭제, 명령 실행 등을 확인 없이 수행합니다.")
    print("⚠️  신뢰할 수 있는 사용자만 Slack 채널에 접근할 수 있도록 하세요.")
    print("☕ caffeinate 활성화됨. !sleep, !awake 명령으로 제어 가능.")
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
