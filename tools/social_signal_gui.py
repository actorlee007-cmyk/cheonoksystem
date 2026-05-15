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
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
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


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("CHEONOK Social Signal Scout")
        root.geometry("760x560")
        root.configure(bg="#0f172a")

        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Paste a TikTok / Shorts / Reels URL and click Analyze.")

        title = tk.Label(root, text="CHEONOK Social Signal Scout", fg="#d1fae5", bg="#0f172a", font=("Arial", 18, "bold"))
        title.pack(pady=(18, 6))

        sub = tk.Label(root, text="Link → collect → analyze → content ideas → DB index", fg="#cbd5e1", bg="#0f172a", font=("Arial", 10))
        sub.pack(pady=(0, 14))

        frame = tk.Frame(root, bg="#0f172a")
        frame.pack(fill="x", padx=22)

        self.entry = tk.Entry(frame, textvariable=self.url_var, font=("Arial", 12), bd=0, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))

        self.btn = tk.Button(frame, text="Analyze", command=self.start_analysis, bg="#86efac", fg="#052e16", font=("Arial", 11, "bold"), bd=0, padx=18, pady=10)
        self.btn.pack(side="left")

        action = tk.Frame(root, bg="#0f172a")
        action.pack(fill="x", padx=22, pady=14)

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

            ideas = workdir / "content_ideas.md"
            index = SCOUT_DATA / "social_signal_index.md"
            self.set_status("DONE")
            self.log("DONE")
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
