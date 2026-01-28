import atexit
import logging
import os
import subprocess

from dotenv import load_dotenv

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Constants
CLI_TIMEOUT_SECONDS = 120
SLACK_MESSAGE_LIMIT = 3900
ERROR_PREVIEW_LIMIT = 500
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
    logger.info("Caffeinate 시작됨 (PID: %d)", caffeinate_proc.pid)


def stop_caffeinate():
    global caffeinate_proc
    if caffeinate_proc and caffeinate_proc.poll() is None:
        caffeinate_proc.terminate()
        caffeinate_proc.wait()
        logger.info("Caffeinate 종료됨")
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
        logger.info("세션 리셋")
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

    logger.info("Slack Input: %s", text)

    try:
        cmd = ["claude", "-p", "--dangerously-skip-permissions"]
        if session_started:
            cmd.append("-c")
        cmd.append(text)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT_SECONDS,
        )

        session_started = True

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            err_msg = f"⚠️ CLI 오류 (exit code {result.returncode})"
            if stderr:
                err_msg += f": {stderr[:ERROR_PREVIEW_LIMIT]}"
            elif stdout:
                err_msg += f": {stdout[:ERROR_PREVIEW_LIMIT]}"
            logger.warning("CLI 오류: exit code %d", result.returncode)
            say(err_msg)
        elif stdout:
            if stderr:
                logger.warning("stderr 출력 있음: %s", stderr[:ERROR_PREVIEW_LIMIT])
            original_len = len(stdout)
            if original_len > SLACK_MESSAGE_LIMIT:
                stdout = stdout[:SLACK_MESSAGE_LIMIT] + f"\n... (truncated, {original_len}자 중 {SLACK_MESSAGE_LIMIT}자 표시)"
            logger.info("Slack Output: %d자", min(original_len, SLACK_MESSAGE_LIMIT))
            say(stdout)
        elif stderr:
            err_msg = f"⚠️ Error: {stderr[:ERROR_PREVIEW_LIMIT]}"
            logger.warning("Slack Output: %s", err_msg)
            say(err_msg)
        else:
            logger.info("Slack Output: (응답 없음)")
            say("(응답 없음)")

    except subprocess.TimeoutExpired:
        msg = f"⏱️ Timeout: {CLI_TIMEOUT_SECONDS}초 내에 응답이 없습니다."
        logger.warning(msg)
        say(msg)
    except FileNotFoundError:
        msg = "⚠️ `claude` CLI를 찾을 수 없습니다. PATH를 확인하세요."
        logger.error(msg)
        say(msg)
    except Exception as e:
        msg = f"⚠️ 오류 발생: {str(e)[:ERROR_PREVIEW_LIMIT]}"
        logger.exception("예상치 못한 오류 발생")
        say(msg)


if __name__ == "__main__":
    start_caffeinate()
    logger.info("Claude Bridge Active on %s", TARGET_CHANNEL_ID)
    logger.warning("--dangerously-skip-permissions 모드로 실행 중입니다.")
    logger.warning("Claude CLI가 파일 생성/수정/삭제, 명령 실행 등을 확인 없이 수행합니다.")
    logger.warning("신뢰할 수 있는 사용자만 Slack 채널에 접근할 수 있도록 하세요.")
    logger.info("caffeinate 활성화됨. !sleep, !awake 명령으로 제어 가능.")
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
