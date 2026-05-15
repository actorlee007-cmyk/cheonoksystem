# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal Scout AUTO WATCH
--------------------------------------
Zero-friction universal mode.

How it works:
1. Run this app once.
2. Copy any SNS/web URL.
3. The app detects the URL from clipboard automatically.
4. Universal reader decides media/text/fallback path.
5. DB appender runs.
6. ChatGPT-ready brief is copied back to clipboard.
7. Paste into ChatGPT with Ctrl+V.

Image clipboard:
- If an image/screenshot is copied instead of a URL, this app detects it when Pillow is available.
- It keeps the image in clipboard and tells the user to paste it directly into ChatGPT.

No manual PowerShell command. No file hunting.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import urllib.request
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

BASE = Path.home() / "Desktop" / "CHEONOK_SOCIAL_SCOUT"
TOOLS = BASE / "tools"
DATA = BASE / "data"
SCOUT_DATA = DATA / "social_signal_scout"
IMAGE_DIR = SCOUT_DATA / "clipboard_images"
RAW_BASE = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"
SCRIPTS = {
    "social_signal_scout_v02.py": f"{RAW_BASE}/social_signal_scout_v02.py",
    "social_signal_scout_v03_analyze.py": f"{RAW_BASE}/social_signal_scout_v03_analyze.py",
    "social_signal_scout_v04_db.py": f"{RAW_BASE}/social_signal_scout_v04_db.py",
    "social_signal_universal_v01.py": f"{RAW_BASE}/social_signal_universal_v01.py",
}

# Broad URL detection. Universal reader decides how to process it.
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)


def ensure_dirs() -> None:
    TOOLS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    SCOUT_DATA.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def download_scripts(log) -> None:
    ensure_dirs()
    for name, url in SCRIPTS.items():
        out = TOOLS / name
        log(f"Update {name}")
        urllib.request.urlretrieve(url, out)


def run_cmd(cmd, log, timeout=None) -> subprocess.CompletedProcess:
    log("RUN: " + " ".join(str(x) for x in cmd))
    p = subprocess.run(
        cmd,
        cwd=str(BASE),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if p.stdout.strip():
        log(p.stdout.strip()[-2500:])
    if p.stderr.strip():
        log("ERR: " + p.stderr.strip()[-2500:])
    if p.returncode != 0:
        raise RuntimeError(f"command failed: {p.returncode}")
    return p


def latest_report() -> Path | None:
    files = list(SCOUT_DATA.rglob("report.md"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def read_text(path: Path, limit: int = 18000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def make_chatgpt_brief(workdir: Path) -> Path:
    ideas = read_text(workdir / "content_ideas.md", limit=16000)
    report = read_text(workdir / "report.md", limit=6000)
    url = read_text(workdir / "input_url.txt", limit=2000).strip()
    brief = f"""[CHEONOK SOCIAL SIGNAL SCOUT RESULT]

URL:
{url}

REQUEST TO CHATGPT:
아래 SNS/웹 분석 결과를 정본 기준으로 다시 판단해줘.
특히 다음을 보고해줘:
1. 핵심 신호
2. 사람들이 반응한 원초적 욕망
3. 과장/위험 요소
4. CHEONOK 홈페이지/콘텐츠/상품에 어떻게 반영할지
5. PASS / HOLD / BLOCK
6. 다음 실행 3개

=== CONTENT IDEAS ===
{ideas}

=== RAW REPORT SUMMARY ===
{report}
"""
    out = workdir / "chatgpt_brief.txt"
    out.write_text(brief, encoding="utf-8")
    return out


def open_file(path: Path) -> None:
    if path.exists():
        os.startfile(str(path))


def grab_clipboard_image():
    try:
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if img is None:
            return None
        # If clipboard has file list, ImageGrab can return list. Ignore list here.
        if isinstance(img, list):
            return None
        return img
    except Exception:
        return None


class AutoWatchApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("CHEONOK AUTO Social Signal Scout")
        root.geometry("900x640")
        root.configure(bg="#07111f")
        self.enabled = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="AUTO ON — Copy any SNS/web link. Image copy will be detected separately.")
        self.processing = False
        self.processed_urls: set[str] = set()
        self.last_image_notice_at = 0.0
        self.last_brief_path: Path | None = None

        title = tk.Label(root, text="CHEONOK UNIVERSAL AUTO WATCH", fg="#bbf7d0", bg="#07111f", font=("Arial", 18, "bold"))
        title.pack(pady=(18, 4))
        sub = tk.Label(root, text="URL → auto analyze / Image → paste directly into ChatGPT", fg="#cbd5e1", bg="#07111f", font=("Arial", 11))
        sub.pack(pady=(0, 14))

        top = tk.Frame(root, bg="#07111f")
        top.pack(fill="x", padx=22)
        self.toggle = tk.Checkbutton(top, text="AUTO WATCH ON", variable=self.enabled, bg="#07111f", fg="#fde68a", selectcolor="#1e293b", font=("Arial", 12, "bold"), activebackground="#07111f", activeforeground="#fde68a")
        self.toggle.pack(side="left")
        tk.Button(top, text="Copy Last Brief", command=self.copy_last_brief, bg="#facc15", fg="#111827", bd=0, padx=14, pady=9).pack(side="left", padx=8)
        tk.Button(top, text="Open Index", command=self.open_index, bg="#1e293b", fg="white", bd=0, padx=14, pady=9).pack(side="left", padx=8)
        tk.Button(top, text="Open Data", command=self.open_data, bg="#1e293b", fg="white", bd=0, padx=14, pady=9).pack(side="left", padx=8)

        self.status = tk.Label(root, textvariable=self.status_var, fg="#e0f2fe", bg="#07111f", anchor="w")
        self.status.pack(fill="x", padx=22, pady=12)

        self.logbox = tk.Text(root, bg="#020617", fg="#e5e7eb", insertbackground="#e5e7eb", font=("Consolas", 10), wrap="word")
        self.logbox.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        ensure_dirs()
        self.log("UNIVERSAL AUTO WATCH READY")
        self.root.after(1000, self.poll_clipboard)

    def log(self, msg: str) -> None:
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")

    def async_log(self, msg: str) -> None:
        self.root.after(0, lambda: self.log(msg))

    def set_status(self, msg: str) -> None:
        self.root.after(0, lambda: self.status_var.set(msg))

    def set_clipboard(self, text: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def get_clipboard(self) -> str:
        try:
            return self.root.clipboard_get()
        except Exception:
            return ""

    def find_url(self, text: str) -> str | None:
        if not text or len(text) > 5000:
            return None
        m = URL_RE.search(text)
        if not m:
            return None
        url = m.group(0).strip().rstrip(").,;]")
        return url

    def poll_clipboard(self):
        try:
            if self.enabled.get() and not self.processing:
                txt = self.get_clipboard()
                url = self.find_url(txt)
                if url and url not in self.processed_urls:
                    self.processed_urls.add(url)
                    self.processing = True
                    self.log("DETECTED URL: " + url)
                    threading.Thread(target=self.process_url, args=(url,), daemon=True).start()
                elif not url:
                    self.check_clipboard_image()
        finally:
            self.root.after(1500, self.poll_clipboard)

    def check_clipboard_image(self):
        import time
        now = time.time()
        if now - self.last_image_notice_at < 10:
            return
        img = grab_clipboard_image()
        if img is None:
            return
        self.last_image_notice_at = now
        ensure_dirs()
        path = IMAGE_DIR / (datetime.now().strftime("clipboard_%Y%m%d_%H%M%S.png"))
        try:
            img.save(path)
            self.log("DETECTED IMAGE CLIPBOARD: " + str(path))
            self.set_status("IMAGE detected. Paste it directly into ChatGPT, or upload saved image from Open Data.")
            # Do not overwrite image clipboard with text. User can paste the image directly into ChatGPT.
        except Exception as e:
            self.log("IMAGE_SAVE_ERROR: " + str(e))

    def process_url(self, url: str) -> None:
        try:
            self.set_status("Processing detected link...")
            download_scripts(self.async_log)
            run_cmd([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], self.async_log, timeout=600)

            run_cmd([sys.executable, str(TOOLS / "social_signal_universal_v01.py"), url], self.async_log, timeout=1800)

            rep = latest_report()
            if not rep:
                raise RuntimeError("report.md not found")
            workdir = rep.parent
            self.async_log(f"WORKDIR: {workdir}")

            run_cmd([sys.executable, str(TOOLS / "social_signal_scout_v04_db.py"), str(workdir)], self.async_log, timeout=600)

            brief_path = make_chatgpt_brief(workdir)
            self.last_brief_path = brief_path
            brief = read_text(brief_path, limit=24000)
            self.root.after(0, lambda: self.set_clipboard(brief))
            self.set_status("DONE — ChatGPT brief copied. Go to ChatGPT and press Ctrl+V.")
            self.async_log("DONE — brief copied to clipboard")
            ideas = workdir / "content_ideas.md"
            if ideas.exists():
                open_file(ideas)
        except Exception as e:
            self.set_status("ERROR")
            self.async_log("ERROR: " + str(e))
            self.root.after(0, lambda: messagebox.showerror("CHEONOK AUTO WATCH", str(e)))
        finally:
            self.processing = False

    def copy_last_brief(self):
        if not self.last_brief_path or not self.last_brief_path.exists():
            files = list(SCOUT_DATA.rglob("chatgpt_brief.txt"))
            if not files:
                messagebox.showinfo("No file", "No chatgpt_brief.txt yet.")
                return
            self.last_brief_path = max(files, key=lambda p: p.stat().st_mtime)
        self.set_clipboard(read_text(self.last_brief_path, limit=24000))
        self.set_status("Last brief copied. Go to ChatGPT and press Ctrl+V.")

    def open_index(self):
        open_file(SCOUT_DATA / "social_signal_index.md")

    def open_data(self):
        os.startfile(str(SCOUT_DATA))


def main():
    ensure_dirs()
    root = tk.Tk()
    AutoWatchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
