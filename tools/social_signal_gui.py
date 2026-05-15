# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal Scout GUI
-------------------------------
A small Windows GUI tool.
Paste a TikTok/Shorts/Reels URL, click Analyze, then it runs:
- social_signal_scout_v02.py
- social_signal_scout_v03_analyze.py
- social_signal_scout_v04_db.py

Output:
- content_ideas.md
- social_signal_index.md
- social_signal_index.csv
- chatgpt_brief.txt copied to clipboard automatically
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

BASE = Path.home() / "Desktop" / "CHEONOK_SOCIAL_SCOUT"
TOOLS = BASE / "tools"
DATA = BASE / "data"
SCOUT_DATA = DATA / "social_signal_scout"
RAW_BASE = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"
SCRIPTS = {
    "social_signal_scout_v02.py": f"{RAW_BASE}/social_signal_scout_v02.py",
    "social_signal_scout_v03_analyze.py": f"{RAW_BASE}/social_signal_scout_v03_analyze.py",
    "social_signal_scout_v04_db.py": f"{RAW_BASE}/social_signal_scout_v04_db.py",
}


def ensure_dirs() -> None:
    TOOLS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    SCOUT_DATA.mkdir(parents=True, exist_ok=True)


def download_scripts(log) -> None:
    ensure_dirs()
    for name, url in SCRIPTS.items():
        out = TOOLS / name
        log(f"Download {name}")
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


def open_file(path: Path) -> None:
    if path.exists():
        os.startfile(str(path))


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(str(path))


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
아래 TikTok/Shorts/Reels 분석 결과를 정본 기준으로 다시 판단해줘.
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


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("CHEONOK Social Signal Scout")
        root.geometry("820x620")
        root.configure(bg="#0f172a")
        self.last_brief_path: Path | None = None

        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Paste a URL and click Analyze. Result will be copied for ChatGPT automatically.")

        title = tk.Label(root, text="CHEONOK Social Signal Scout", fg="#d1fae5", bg="#0f172a", font=("Arial", 18, "bold"))
        title.pack(pady=(18, 6))

        sub = tk.Label(root, text="Link → collect → analyze → DB index → copy ChatGPT brief", fg="#cbd5e1", bg="#0f172a", font=("Arial", 10))
        sub.pack(pady=(0, 14))

        frame = tk.Frame(root, bg="#0f172a")
        frame.pack(fill="x", padx=22)

        self.entry = tk.Entry(frame, textvariable=self.url_var, font=("Arial", 12), bd=0, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))

        self.btn = tk.Button(frame, text="Analyze + Copy", command=self.start_analysis, bg="#86efac", fg="#052e16", font=("Arial", 11, "bold"), bd=0, padx=18, pady=10)
        self.btn.pack(side="left")

        action = tk.Frame(root, bg="#0f172a")
        action.pack(fill="x", padx=22, pady=14)

        tk.Button(action, text="Copy Last Brief", command=self.copy_last_brief, bg="#facc15", fg="#111827", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))
        tk.Button(action, text="Open Latest Ideas", command=self.open_latest_ideas, bg="#1e293b", fg="white", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))
        tk.Button(action, text="Open Index", command=self.open_index, bg="#1e293b", fg="white", bd=0, padx=12, pady=8).pack(side="left", padx=(0, 8))
        tk.Button(action, text="Open Data Folder", command=lambda: open_folder(SCOUT_DATA), bg="#1e293b", fg="white", bd=0, padx=12, pady=8).pack(side="left")

        self.status = tk.Label(root, textvariable=self.status_var, fg="#fef3c7", bg="#0f172a", anchor="w")
        self.status.pack(fill="x", padx=22, pady=(0, 8))

        self.logbox = tk.Text(root, bg="#020617", fg="#e5e7eb", insertbackground="#e5e7eb", font=("Consolas", 10), wrap="word")
        self.logbox.pack(fill="both", expand=True, padx=22, pady=(0, 22))

    def log(self, msg: str) -> None:
        def _append():
            self.logbox.insert("end", msg + "\n")
            self.logbox.see("end")
        self.root.after(0, _append)

    def set_status(self, msg: str) -> None:
        self.root.after(0, lambda: self.status_var.set(msg))

    def set_clipboard(self, text: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def start_analysis(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL required", "Paste a URL first.")
            return
        self.btn.config(state="disabled")
        self.logbox.delete("1.0", "end")
        t = threading.Thread(target=self.analyze, args=(url,), daemon=True)
        t.start()

    def analyze(self, url: str) -> None:
        try:
            self.set_status("Preparing...")
            ensure_dirs()
            download_scripts(self.log)

            self.set_status("Installing/updating yt-dlp...")
            run_cmd([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], self.log, timeout=600)

            self.set_status("Collecting social signal...")
            run_cmd([sys.executable, str(TOOLS / "social_signal_scout_v02.py"), url], self.log, timeout=1800)

            rep = latest_report()
            if not rep:
                raise RuntimeError("report.md not found")
            workdir = rep.parent
            self.log(f"WORKDIR: {workdir}")

            self.set_status("Generating content ideas...")
            run_cmd([sys.executable, str(TOOLS / "social_signal_scout_v03_analyze.py"), str(workdir)], self.log, timeout=600)

            self.set_status("Appending DB index...")
            run_cmd([sys.executable, str(TOOLS / "social_signal_scout_v04_db.py"), str(workdir)], self.log, timeout=600)

            brief_path = make_chatgpt_brief(workdir)
            brief_text = read_text(brief_path, limit=24000)
            self.last_brief_path = brief_path
            self.root.after(0, lambda: self.set_clipboard(brief_text))

            ideas = workdir / "content_ideas.md"
            index = SCOUT_DATA / "social_signal_index.md"
            self.set_status("DONE — ChatGPT brief copied. Paste into ChatGPT with Ctrl+V.")
            self.log("DONE — chatgpt_brief.txt copied to clipboard")
            if ideas.exists():
                open_file(ideas)
            if index.exists():
                open_file(index)
        except Exception as e:
            self.set_status("ERROR")
            self.log("ERROR: " + str(e))
            messagebox.showerror("CHEONOK Social Signal Scout", str(e))
        finally:
            self.root.after(0, lambda: self.btn.config(state="normal"))

    def copy_last_brief(self) -> None:
        if not self.last_brief_path or not self.last_brief_path.exists():
            files = list(SCOUT_DATA.rglob("chatgpt_brief.txt"))
            if not files:
                messagebox.showinfo("No file", "No chatgpt_brief.txt yet.")
                return
            self.last_brief_path = max(files, key=lambda p: p.stat().st_mtime)
        text = read_text(self.last_brief_path, limit=24000)
        self.set_clipboard(text)
        self.set_status("Last ChatGPT brief copied. Paste into ChatGPT with Ctrl+V.")

    def open_latest_ideas(self) -> None:
        files = list(SCOUT_DATA.rglob("content_ideas.md"))
        if not files:
            messagebox.showinfo("No file", "No content_ideas.md yet.")
            return
        open_file(max(files, key=lambda p: p.stat().st_mtime))

    def open_index(self) -> None:
        open_file(SCOUT_DATA / "social_signal_index.md")


def main():
    ensure_dirs()
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
