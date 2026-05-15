# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal Discovery v0.5
------------------------------------
Purpose:
- System finds social signal candidates by itself.
- Start with YouTube/Shorts search using yt-dlp ytsearch.
- Score candidates by CHEONOK canon signals.
- Optionally run existing Social Signal Scout pipeline on top candidates.

Rule:
- This is search-based candidate discovery, not mass crawling.
- TikTok mass discovery stays HOLD. TikTok links remain single-link analysis.

Usage:
python tools/social_signal_discovery_v05.py --limit 5 --analyze 2
python tools/social_signal_discovery_v05.py --query "Claude Code AI agent startup" --limit 10 --analyze 3
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
DATA = ROOT / "data" / "social_signal_scout"
DISCOVERY = DATA / "discovery"
DISCOVERY.mkdir(parents=True, exist_ok=True)

DEFAULT_QUERIES = [
    "Claude Code AI agents startup automation",
    "AI coding agent small team automation",
    "AI agent workflow automation founder",
    "faceless YouTube AI niche no editing",
    "AI YouTube automation niche strategy shorts",
    "AI tools make money content automation",
    "solo founder AI automation system",
    "AI agents replace team startup",
    "open source AI tools content automation",
    "small team beats big company AI automation",
]

SIGNAL_RULES = [
    ("AI_AGENT_RUNTIME", ["claude code", "ai agent", "agents", "agentic", "autonomous", "cursor", "coding agent"]),
    ("AUTOMATION", ["automation", "automate", "자동화", "workflow"]),
    ("SMALL_TEAM_LEVERAGE", ["small team", "solo founder", "one person", "1 person", "startup", "founder"]),
    ("MONEY_FLOW", ["money", "revenue", "income", "earn", "$", "수익", "돈", "매출"]),
    ("FACELESS_CONTENT", ["faceless", "no face", "without showing", "얼굴"]),
    ("YOUTUBE_NICHE", ["youtube", "shorts", "niche", "니치"]),
    ("TOOL_DISCOVERY", ["tool", "tools", "software", "github", "open source", "도구", "프로그램"]),
    ("FAST_RESULT", ["90 days", "30 days", "in a day", "fast", "quick", "하루", "90일", "30일"]),
    ("HUMAN_VALUE", ["creator", "story", "meaning", "human", "성실", "사람", "가치"]),
]


def run_cmd(cmd, timeout=240):
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return p.returncode, p.stdout, p.stderr


def yt_search(query: str, limit: int):
    target = f"ytsearch{limit}:{query}"
    cmd = ["yt-dlp", "--dump-json", "--skip-download", target]
    code, out, err = run_cmd(cmd, timeout=300)
    results = []
    if code != 0:
        return results, err
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            results.append(data)
        except Exception:
            pass
    return results, None


def detect_signals(text: str):
    low = (text or "").lower()
    found = []
    for name, keys in SIGNAL_RULES:
        if any(k in low for k in keys):
            found.append(name)
    return found


def score_item(item: dict):
    title = item.get("title") or ""
    desc = item.get("description") or ""
    tags = item.get("tags") or []
    if isinstance(tags, list):
        tag_text = " ".join(str(x) for x in tags)
    else:
        tag_text = str(tags)
    text = " ".join([title, desc, tag_text])
    signals = detect_signals(text)
    score = len(signals) * 10
    vc = item.get("view_count") or 0
    lc = item.get("like_count") or 0
    try:
        if vc:
            score += min(int(vc) // 10000, 20)
        if lc:
            score += min(int(lc) // 1000, 10)
    except Exception:
        pass
    if "AI_AGENT_RUNTIME" in signals:
        score += 15
    if "SMALL_TEAM_LEVERAGE" in signals:
        score += 10
    if "MONEY_FLOW" in signals:
        score += 8
    return score, signals


def normalize_url(item: dict):
    url = item.get("webpage_url") or item.get("original_url") or item.get("url") or ""
    if url and url.startswith("http"):
        return url
    vid = item.get("id")
    if vid:
        return f"https://www.youtube.com/watch?v={vid}"
    return ""


def run_pipeline(url: str):
    v02 = TOOLS / "social_signal_scout_v02.py"
    v03 = TOOLS / "social_signal_scout_v03_analyze.py"
    v04 = TOOLS / "social_signal_scout_v04_db.py"
    if not v02.exists() or not v03.exists() or not v04.exists():
        return False, "Scout pipeline scripts not found"
    code, out, err = run_cmd([sys.executable, str(v02), url], timeout=1800)
    if code != 0:
        return False, err or out
    reports = list(DATA.rglob("report.md"))
    if not reports:
        return False, "report.md not found"
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    workdir = latest.parent
    code, out2, err2 = run_cmd([sys.executable, str(v03), str(workdir)], timeout=600)
    if code != 0:
        return False, err2 or out2
    code, out3, err3 = run_cmd([sys.executable, str(v04), str(workdir)], timeout=600)
    if code != 0:
        return False, err3 or out3
    return True, str(workdir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="", help="single query override")
    ap.add_argument("--limit", type=int, default=5, help="results per query")
    ap.add_argument("--analyze", type=int, default=0, help="analyze top N candidates")
    args = ap.parse_args()

    queries = [args.query] if args.query.strip() else DEFAULT_QUERIES
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = DISCOVERY / f"discovery_{now}"
    outdir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    seen = set()
    errors = []

    for q in queries:
        print("SEARCH:", q)
        items, err = yt_search(q, args.limit)
        if err:
            errors.append(f"{q}: {err[:500]}")
        for item in items:
            url = normalize_url(item)
            if not url or url in seen:
                continue
            seen.add(url)
            score, signals = score_item(item)
            row = {
                "query": q,
                "score": score,
                "signals": " | ".join(signals),
                "title": item.get("title") or "",
                "url": url,
                "uploader": item.get("uploader") or item.get("channel") or "",
                "duration": item.get("duration") or "",
                "view_count": item.get("view_count") or "",
                "like_count": item.get("like_count") or "",
            }
            all_rows.append(row)

    all_rows.sort(key=lambda r: int(r.get("score") or 0), reverse=True)

    csv_path = outdir / "discovered_candidates.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["score", "signals", "title", "url", "uploader", "duration", "view_count", "like_count", "query"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    md_path = outdir / "discovered_candidates.md"
    md = ["# CHEONOK Social Signal Discovery v0.5", "", f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    md.append("## Top Candidates")
    md.append("")
    for i, r in enumerate(all_rows[:50], 1):
        md.append(f"### {i}. {r['title']}")
        md.append(f"- Score: {r['score']}")
        md.append(f"- Signals: {r['signals']}")
        md.append(f"- URL: {r['url']}")
        md.append(f"- Uploader: {r['uploader']}")
        md.append(f"- Views: {r['view_count']}")
        md.append(f"- Query: {r['query']}")
        md.append("")

    if errors:
        md.append("## Errors")
        for e in errors:
            md.append(f"- {e}")

    analyzed = []
    if args.analyze > 0:
        md.append("## Auto Analyzed")
        for r in all_rows[: args.analyze]:
            print("ANALYZE:", r["url"])
            ok, info = run_pipeline(r["url"])
            analyzed.append((r["url"], ok, info))
            md.append(f"- {'OK' if ok else 'FAIL'}: {r['url']} -> {info}")

    md_path.write_text("\n".join(md), encoding="utf-8")

    print("CHEONOK Social Signal Discovery v0.5 DONE")
    print("md:", md_path)
    print("csv:", csv_path)


if __name__ == "__main__":
    main()
