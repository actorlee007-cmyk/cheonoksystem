# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal Scout v0.4 DB Appender
--------------------------------------------
Purpose:
- Read the latest Social Signal Scout workdir.
- Append a row to social_signal_index.csv.
- Append a human-readable index entry to social_signal_index.md.

Usage:
python tools/social_signal_scout_v04_db.py "C:/.../workdir"
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def read_text(path: Path, limit: int = 50000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def extract_verdict(text: str) -> str:
    m = re.search(r"판정:\s*\*\*(.*?)\*\*", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"판정:\s*(.+)", text)
    if m:
        return m.group(1).strip()
    return "UNKNOWN"


def extract_section_bullets(text: str, section_title: str, max_items=12):
    # Simple markdown section parser.
    pattern = rf"##\s+[^\n]*{re.escape(section_title)}[^\n]*\n(.*?)(?=\n##\s+|\Z)"
    m = re.search(pattern, text, flags=re.S)
    if not m:
        return []
    block = m.group(1)
    items = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("-"):
            items.append(line.lstrip("- ").strip())
        if len(items) >= max_items:
            break
    return items


def safe_join(items):
    return " | ".join([str(x).replace("\n", " ").strip() for x in items if str(x).strip()])


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/social_signal_scout_v04_db.py <workdir>")
        sys.exit(1)

    workdir = Path(sys.argv[1]).resolve()
    if not workdir.exists():
        print("WORKDIR_NOT_FOUND", workdir)
        sys.exit(2)

    data_root = workdir.parents[0]
    db_csv = data_root / "social_signal_index.csv"
    db_md = data_root / "social_signal_index.md"

    meta = load_json(workdir / "metadata.json")
    input_url = read_text(workdir / "input_url.txt", 2000).strip()
    report = read_text(workdir / "report.md")
    ideas = read_text(workdir / "content_ideas.md")

    title = meta.get("title") or ""
    uploader = meta.get("uploader") or meta.get("channel") or ""
    view_count = meta.get("view_count") or ""
    like_count = meta.get("like_count") or ""
    duration = meta.get("duration") or ""
    tags = meta.get("tags") or []
    if isinstance(tags, list):
        tags_txt = safe_join(tags)
    else:
        tags_txt = str(tags)

    verdict = extract_verdict(ideas) if ideas else extract_verdict(report)
    signals = extract_section_bullets(ideas, "감지 신호") or extract_section_bullets(report, "정본 신호")
    desires = extract_section_bullets(ideas, "원초적 욕망")
    risks = extract_section_bullets(ideas, "위험")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "created_at": now,
        "url": input_url,
        "title": title,
        "uploader": uploader,
        "duration": duration,
        "view_count": view_count,
        "like_count": like_count,
        "tags": tags_txt,
        "verdict": verdict,
        "signals": safe_join(signals),
        "desires": safe_join(desires),
        "risks": safe_join(risks),
        "workdir": str(workdir),
    }

    fieldnames = list(row.keys())
    write_header = not db_csv.exists()
    with db_csv.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    if not db_md.exists():
        db_md.write_text("# CHEONOK Social Signal Index\n\n", encoding="utf-8")

    entry = f"""
## {now} — {title or 'Untitled'}

- URL: {input_url}
- Uploader: {uploader}
- Views: {view_count}
- Likes: {like_count}
- Tags: {tags_txt}
- Verdict: **{verdict}**
- Signals: {safe_join(signals) or '-'}
- Desires: {safe_join(desires) or '-'}
- Risks: {safe_join(risks) or '-'}
- Workdir: `{workdir}`

"""
    with db_md.open("a", encoding="utf-8") as f:
        f.write(entry)

    print("CHEONOK Social Signal Scout v0.4 DB DONE")
    print("csv:", db_csv)
    print("md:", db_md)


if __name__ == "__main__":
    main()
