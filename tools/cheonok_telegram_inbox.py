# -*- coding: utf-8 -*-
"""
CHEONOK Telegram Inbox v0.2
---------------------------
Mobile-first inbox for Social Signal Scout.

Mobile workflow:
1. Share TikTok / YouTube / Threads / web link to Telegram bot.
2. This runner receives the message on PC.
3. It routes URL to social_signal_universal_v01.py.
4. It appends DB via social_signal_scout_v04_db.py.
5. It sends a short result back to Telegram.

Supported input:
- text containing URL
- text memo
- photo/document screenshot: saved for later review

Required:
- Telegram bot token.
- If missing, this runner asks for the token locally and saves it to config/telegram_inbox_token.txt.

Run:
python tools/cheonok_telegram_inbox.py

Safety:
- Single-message inbox processing.
- No mass crawling.
- No login bypass.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
CONFIG = ROOT / "config"
DATA = ROOT / "data" / "social_signal_scout"
INBOX = DATA / "telegram_inbox"
FILES = INBOX / "files"
CONFIG.mkdir(parents=True, exist_ok=True)
INBOX.mkdir(parents=True, exist_ok=True)
FILES.mkdir(parents=True, exist_ok=True)

URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)


def token_path() -> Path:
    return CONFIG / "telegram_inbox_token.txt"


def normalize_token(token: str) -> str:
    return (token or "").strip().replace("\ufeff", "")


def looks_like_token(token: str) -> bool:
    # Telegram bot tokens commonly look like 123456789:ABCdef...
    return bool(re.match(r"^\d{6,}:[A-Za-z0-9_-]{20,}$", token or ""))


def local_token_setup() -> str:
    cfg = token_path()
    print("=" * 72)
    print("CHEONOK TELEGRAM INBOX TOKEN SETUP")
    print("=" * 72)
    print("Telegram bot token is missing.")
    print("1) Open Telegram")
    print("2) Search: @BotFather")
    print("3) Send: /newbot")
    print("4) Copy the bot token")
    print("5) Paste it here. It will be saved only on this PC.")
    print("")
    print("Token file:", cfg)
    print("Do NOT paste the token into ChatGPT.")
    print("=" * 72)
    try:
        webbrowser.open("https://t.me/BotFather")
    except Exception:
        pass
    token = normalize_token(input("Paste Telegram bot token here: "))
    if not token:
        raise RuntimeError("TOKEN_EMPTY")
    if not looks_like_token(token):
        print("WARN: This does not look like a normal Telegram bot token. Saving anyway.")
    cfg.write_text(token, encoding="utf-8")
    print("Saved token:", cfg)
    return token


def env_token() -> str:
    token = normalize_token(os.environ.get("TELEGRAM_BOT_TOKEN", ""))
    cfg = token_path()
    if not token and cfg.exists():
        token = normalize_token(cfg.read_text(encoding="utf-8", errors="replace"))
    if not token:
        token = local_token_setup()
    return token


def api_url(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


def http_json(url: str, data: dict | None = None) -> dict:
    if data is None:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def validate_token(token: str) -> tuple[bool, str]:
    try:
        res = http_json(api_url(token, "getMe"))
        if not res.get("ok"):
            return False, str(res)
        bot = res.get("result", {})
        username = bot.get("username", "")
        return True, username
    except Exception as e:
        return False, str(e)


def send_message(token: str, chat_id: int | str, text: str) -> None:
    text = text[:3900]
    http_json(api_url(token, "sendMessage"), {"chat_id": chat_id, "text": text})


def get_file_path(token: str, file_id: str) -> str:
    res = http_json(api_url(token, "getFile") + "?" + urllib.parse.urlencode({"file_id": file_id}))
    if not res.get("ok"):
        raise RuntimeError(str(res))
    return res["result"]["file_path"]


def download_file(token: str, file_path: str, out: Path) -> None:
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    urllib.request.urlretrieve(url, out)


def run_cmd(cmd, timeout=1800):
    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return p.returncode, p.stdout, p.stderr


def latest_report() -> Path | None:
    files = list(DATA.rglob("report.md"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def read_text(path: Path, limit=5000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def process_url(url: str) -> tuple[bool, str]:
    universal = TOOLS / "social_signal_universal_v01.py"
    db = TOOLS / "social_signal_scout_v04_db.py"
    if not universal.exists():
        return False, "social_signal_universal_v01.py not found"
    if not db.exists():
        return False, "social_signal_scout_v04_db.py not found"

    code, out, err = run_cmd([sys.executable, str(universal), url], timeout=1800)
    if code != 0:
        return False, err or out or f"universal exit {code}"

    rep = latest_report()
    if not rep:
        return False, "report.md not found"
    workdir = rep.parent

    code, out2, err2 = run_cmd([sys.executable, str(db), str(workdir)], timeout=600)
    if code != 0:
        return False, err2 or out2 or f"db exit {code}"

    ideas = read_text(workdir / "content_ideas.md", limit=1800)
    return True, f"DONE\nWORKDIR: {workdir}\n\n{ideas[:1800]}"


def extract_url(text: str) -> str | None:
    if not text:
        return None
    m = URL_RE.search(text)
    if not m:
        return None
    return m.group(0).strip().rstrip(").,;]")


def save_text_memo(message: dict) -> Path:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = INBOX / f"memo_{now}.txt"
    text = message.get("text") or message.get("caption") or ""
    out.write_text(text, encoding="utf-8")
    return out


def handle_message(token: str, message: dict) -> None:
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

    text = message.get("text") or message.get("caption") or ""
    url = extract_url(text)

    if url:
        send_message(token, chat_id, f"CHEONOK INBOX received URL:\n{url}\n\nAnalyzing...")
        ok, result = process_url(url)
        send_message(token, chat_id, ("PASS\n" if ok else "ERROR\n") + result)
        return

    if "photo" in message:
        photo = message["photo"][-1]
        fid = photo["file_id"]
        fpath = get_file_path(token, fid)
        ext = Path(fpath).suffix or ".jpg"
        out = FILES / (datetime.now().strftime("photo_%Y%m%d_%H%M%S") + ext)
        download_file(token, fpath, out)
        send_message(token, chat_id, f"CHEONOK INBOX saved image:\n{out}\n\nImage saved. Vision analysis can be added as next module.")
        return

    if "document" in message:
        doc = message["document"]
        fid = doc["file_id"]
        name = doc.get("file_name") or (datetime.now().strftime("document_%Y%m%d_%H%M%S"))
        fpath = get_file_path(token, fid)
        out = FILES / name
        download_file(token, fpath, out)
        send_message(token, chat_id, f"CHEONOK INBOX saved document:\n{out}")
        return

    if text:
        out = save_text_memo(message)
        send_message(token, chat_id, f"CHEONOK INBOX saved memo:\n{out}")
        return

    send_message(token, chat_id, "CHEONOK INBOX received unsupported message type.")


def main():
    token = env_token()
    ok, bot_info = validate_token(token)
    if not ok:
        bad = token_path()
        print("TOKEN_VALIDATION_FAILED:", bot_info)
        print("Delete or edit token file:", bad)
        raise RuntimeError("Invalid Telegram bot token")

    print("CHEONOK Telegram Inbox START")
    print("Bot:", "@" + bot_info if bot_info else "OK")
    print("INBOX:", INBOX)
    print("Send a message/link/photo to your Telegram bot from the phone.")

    offset = 0
    state = INBOX / "telegram_offset.txt"
    if state.exists():
        try:
            offset = int(state.read_text().strip())
        except Exception:
            offset = 0

    while True:
        try:
            params = {"timeout": 30, "offset": offset + 1}
            res = http_json(api_url(token, "getUpdates") + "?" + urllib.parse.urlencode(params))
            if not res.get("ok"):
                print("API_NOT_OK", res)
                time.sleep(5)
                continue
            for upd in res.get("result", []):
                offset = max(offset, upd.get("update_id", 0))
                state.write_text(str(offset), encoding="utf-8")
                msg = upd.get("message") or upd.get("edited_message")
                if msg:
                    print("MESSAGE_RECEIVED", datetime.now().strftime("%H:%M:%S"))
                    handle_message(token, msg)
        except KeyboardInterrupt:
            print("STOP")
            break
        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
