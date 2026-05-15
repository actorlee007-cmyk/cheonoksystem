# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal INPUT GUI
-------------------------------
Manual explicit mode.

No clipboard watching.
No auto-detection confusion.

Workflow:
1. Paste SNS/web URL into the input box.
2. Click Analyze.
3. Universal reader processes media/text/fallback.
4. DB appender stores result.
5. ChatGPT-ready brief is copied to clipboard.

Supported by universal reader:
TikTok, YouTube, Shorts, Instagram/Reels, Threads, X/Twitter, Reddit,
Naver Blog/Post, Brunch, Medium, Tistory, general web pages.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

DESKTOP = Path(os.path.expandvars(r"%USERPROFILE%")) / "Desktop"
# Actual GUI launcher may live on OneDrive Desktop. Data location stays simple and stable.
BASE = DESKTOP / "CHEONOK_SOCIAL_SCOUT"
TOOLS = BASE / "tools"
DATA = BASE / "data"
SCOUT_DATA = DATA / "social_signal_scout"
RAW_BASE = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"
SCRIPTS = {
    "social_signal_scout_v02.py": f"{RAW_BASE}/social_signal_scout_v02.py",
    "social_signal_scout_v03_analyze.py": f"{RAW_BASE}/social_signal_scout_v03_analyze.py",
    "social_signal_scout_v04_db.py": f"{RAW_BASE}/social_signal_scout_v04_db.py",
    "social_signal_universal_v01.py": f"{RAW_BASE}/social_signal_universal_v01.py",
}

URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)


def ensure_dirs() -> None:
    TOOLS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    SCOUT_DATA.mkdir(parents=True, exist_ok=True)


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
        log(p.stdout.strip()[-3000:])
    if p.stderr.strip():
        log("ERR: " + p.stderr.strip()[-3000:])
    if p.returncode != 0:
        raise RuntimeError(f"command failed: {p.returncode}")
    return p


def latest_report() -> Path | None:
    files = list(SCOUT_DATA.rglob("report.md"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def read_text(path: Path, limit: int = 22000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def make_chatgpt_brief(workdir: Path) -> Path:
    ideas = read_text(workdir / "content_ideas.md", limit=16000)
    report = read_text(workdir / "report.md", limit=7000)
    url = read_text(workdir / "input_url.txt", limit=3000).strip()
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
7. 이 신호를 시스템 업그레이드에 반영할 패치 포인트

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


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(str(path))


def normalize_input(raw: str) -> str:
    raw = (raw or "").strip()
    m = URL_RE.search(raw)
    if m:
        return m.group(0).strip().rstrip(").,;]")
    return raw


class InputGui:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("CHEONOK Social Signal Input")
        root.geometry("900x650")
        root.configure(bg="#07111f")
        self.status_var = tk.StringVar(value="Paste a SNS/web URL and click Analyze.")
        self.last_brief_path: Path | None = None

        title = tk.Label(root, text="CHEONOK SOCIAL SIGNAL INPUT", fg="#bbf7d0", bg="#07111f", font=("Arial", 18, "bold"))
        title.pack(pady=(18, 4))
        sub = tk.Label(root, text="Manual explicit mode: paste link → Analyze → ChatGPT brief copied", fg="#cbd5e1", bg="#07111f", font=("Arial", 11))
        sub.pack(pady=(0, 14))

        box_frame = tk.Frame(root, bg="#07111f")
        box_frame.pack(fill="x", padx=22)

        self.input = tk.Text(box_frame, height=4, bg="#f8fafc", fg="#020617", font=("Arial", 12), wrap="word")
        self.input.pack(fill="x", expand=True, side="left")

        button_col = tk.Frame(box_frame, bg="#07111f")
        button_col.pack(side="left", padx=(10, 0), fill="y")

        self.analyze_btn = tk.Button(button_col, text="Analyze", command=self.start_analysis, bg="#86efac", fg="#052e16", font=("Arial", 12, "bold"), bd=0, padx=20, pady=12)
        self.analyze_btn.pack(fill="x", pady=(0, 8))
        tk.Button(button_col, text="Paste", command=self.paste_from_clipboard, bg="#facc15", fg="#111827", bd=0, padx=20, pady=9).pack(fill="x", pady=(0, 8))
        tk.Button(button_col, text="Clear", command=lambda: self.input.delete("1.0", "end"), bg="#334155", fg="white", bd=0, padx=20, pady=9).pack(fill="x")

        action = tk.Frame(root, bg="#07111f")
        action.pack(fill="x", padx=22, pady=14)
        tk.Button(action, text="Copy Last Brief", command=self.copy_last_brief, bg="#facc15", fg="#111827", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))
        tk.Button(action, text="Open Latest Ideas", command=self.open_latest_ideas, bg="#1e293b", fg="white", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))
        tk.Button(action, text="Open Index", command=self.open_index, bg="#1e293b", fg="white", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))
        tk.Button(action, text="Open Data Folder", command=lambda: open_folder(SCOUT_DATA), bg="#1e293b", fg="white", bd=0, padx=12, pady=8).pack(side="left")

        self.status = tk.Label(root, textvariable=self.status_var, fg="#e0f2fe", bg="#07111f", anchor="w")
        self.status.pack(fill="x", padx=22, pady=(0, 8))

        self.logbox = tk.Text(root, bg="#020617", fg="#e5e7eb", insertbackground="#e5e7eb", font=("Consolas", 10), wrap="word")
        self.logbox.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        ensure_dirs()
        self.log("INPUT GUI READY")

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

    def paste_from_clipboard(self):
        try:
            txt = self.root.clipboard_get()
        except Exception:
            txt = ""
        if txt:
            self.input.delete("1.0", "end")
            self.input.insert("1.0", txt)

    def start_analysis(self) -> None:
        raw = self.input.get("1.0", "end").strip()
        value = normalize_input(raw)
        if not value or not value.startswith("http"):
            messagebox.showwarning("URL required", "Paste a valid SNS/web URL first.")
            return
        self.analyze_btn.config(state="disabled")
        self.logbox.delete("1.0", "end")
        threading.Thread(target=self.analyze, args=(value,), daemon=True).start()

    def analyze(self, url: str) -> None:
        try:
            self.set_status("Updating scripts...")
            download_scripts(self.async_log)
            self.set_status("Installing/updating yt-dlp...")
            run_cmd([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], self.async_log, timeout=600)

            self.set_status("Analyzing URL...")
            run_cmd([sys.executable, str(TOOLS / "social_signal_universal_v01.py"), url], self.async_log, timeout=1800)

            rep = latest_report()
            if not rep:
                raise RuntimeError("report.md not found")
            workdir = rep.parent
            self.async_log(f"WORKDIR: {workdir}")

            self.set_status("Appending index...")
            run_cmd([sys.executable, str(TOOLS / "social_signal_scout_v04_db.py"), str(workdir)], self.async_log, timeout=600)

            brief_path = make_chatgpt_brief(workdir)
            self.last_brief_path = brief_path
            brief = read_text(brief_path, limit=26000)
            self.root.after(0, lambda: self.set_clipboard(brief))

            self.set_status("DONE — ChatGPT brief copied. Paste into ChatGPT with Ctrl+V.")
            self.async_log("DONE — chatgpt_brief.txt copied to clipboard")
            ideas = workdir / "content_ideas.md"
            if ideas.exists():
                open_file(ideas)
        except Exception as e:
            self.set_status("ERROR")
            self.async_log("ERROR: " + str(e))
            self.root.after(0, lambda: messagebox.showerror("CHEONOK INPUT", str(e)))
        finally:
            self.root.after(0, lambda: self.analyze_btn.config(state="normal"))

    def copy_last_brief(self):
        if not self.last_brief_path or not self.last_brief_path.exists():
            files = list(SCOUT_DATA.rglob("chatgpt_brief.txt"))
            if not files:
                messagebox.showinfo("No file", "No chatgpt_brief.txt yet.")
                return
            self.last_brief_path = max(files, key=lambda p: p.stat().st_mtime)
        self.set_clipboard(read_text(self.last_brief_path, limit=26000))
        self.set_status("Last brief copied. Paste into ChatGPT with Ctrl+V.")

    def open_latest_ideas(self):
        files = list(SCOUT_DATA.rglob("content_ideas.md"))
        if not files:
            messagebox.showinfo("No file", "No content_ideas.md yet.")
            return
        open_file(max(files, key=lambda p: p.stat().st_mtime))

    def open_index(self):
        open_file(SCOUT_DATA / "social_signal_index.md")


def main():
    ensure_dirs()
    root = tk.Tk()
    InputGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
