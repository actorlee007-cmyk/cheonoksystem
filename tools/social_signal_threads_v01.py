# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal Threads Reader v0.1
----------------------------------------
Purpose:
- Read a single public Threads link if available on web.
- Extract title/meta/visible text from HTML.
- Create report.md + content_ideas.md in the same format as Social Signal Scout.

Usage:
python tools/social_signal_threads_v01.py "https://www.threads.com/@user/post/..."
python tools/social_signal_threads_v01.py "https://www.threads.net/@user/post/..."

Rule:
- Single-link analysis only.
- No login bypass.
- No mass crawling.
"""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "social_signal_scout"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_name(text: str) -> str:
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-zA-Z0-9가-힣_.-]+", "_", text)
    return text[:90].strip("_") or "threads_signal"


def fetch_html(url: str) -> tuple[str, str | None]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode("utf-8", errors="replace")
        return data, None
    except Exception as e:
        return "", str(e)


def extract_meta(raw: str) -> dict:
    def meta_prop(prop: str) -> str:
        patterns = [
            rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\'](.*?)["\']',
            rf'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']{re.escape(prop)}["\']',
            rf'<meta[^>]+name=["\']{re.escape(prop)}["\'][^>]+content=["\'](.*?)["\']',
        ]
        for p in patterns:
            m = re.search(p, raw, flags=re.I | re.S)
            if m:
                return html.unescape(m.group(1)).strip()
        return ""

    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
    if m:
        title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()

    return {
        "title": meta_prop("og:title") or title,
        "description": meta_prop("og:description") or meta_prop("description"),
        "site_name": meta_prop("og:site_name"),
        "image": meta_prop("og:image"),
        "url": meta_prop("og:url"),
    }


def strip_html(raw: str) -> str:
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_signals(text: str):
    low = (text or "").lower()
    rules = [
        ("AI/자동화", ["ai", "automation", "자동화", "인공지능", "agent", "에이전트"]),
        ("현금흐름/수익", ["money", "revenue", "income", "earn", "수익", "돈", "매출", "달러", "$"]),
        ("창업/비즈니스", ["startup", "founder", "business", "사업", "창업", "스타트업"]),
        ("콘텐츠/유입", ["content", "creator", "youtube", "shorts", "threads", "콘텐츠", "유입"]),
        ("도구/소프트웨어", ["tool", "software", "github", "open source", "도구", "프로그램"]),
        ("사람 가치/동반성장", ["human", "value", "성실", "사람", "가치", "성장"]),
        ("불편함/문제", ["problem", "pain", "friction", "불편", "문제", "귀찮", "어렵"]),
    ]
    found = []
    for name, keys in rules:
        if any(k in low for k in keys):
            found.append(name)
    return found


def make_content_ideas(url: str, meta: dict, text: str, signals: list[str], workdir: Path) -> Path:
    verdict = "PASS as social text signal" if signals else "HOLD — weak signal"
    desc = meta.get("description") or ""
    title = meta.get("title") or "Threads post"
    preview = (desc + "\n" + text)[:3500]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = f"""# CHEONOK Threads Signal Report v0.1

생성시각: {now}

## 1. 원본 요약

- URL: {url}
- title: {title}
- description: {desc}

## 2. 정본 판정

판정: **{verdict}**

감지 신호:

{chr(10).join(['- ' + s for s in signals]) if signals else '- 감지 신호 부족'}

## 3. 본문/메타 텍스트 미리보기

```text
{preview}
```

## 4. CHEONOK식 해석 질문

```text
1. 이 글은 어떤 불편함/욕망을 건드리는가?
2. 이 신호가 현금흐름·유입·콘텐츠·도구·사람 가치 중 어디에 연결되는가?
3. 그대로 따라 하면 위험한 부분은 무엇인가?
4. CHEONOK 홈페이지/콘텐츠/상품으로 어떻게 바꿀 것인가?
5. PASS / HOLD / BLOCK 최종 판정은 무엇인가?
```

## 5. 콘텐츠 아이디어 초안

1. 이 Threads 글에서 드러난 불편함을 해결하는 방법
2. 사람들이 저장/공유하는 문장의 공통점
3. CHEONOK은 이 문제를 어떻게 시스템으로 바꾸는가

## 6. 정본 원칙

```text
Threads 글은 대중 심리와 문장 후킹 신호로 사용한다.
증거가 아니라 신호다.
무단 대량 수집은 하지 않는다.
단건 링크 기반으로 분석한다.
```
"""
    out = workdir / "content_ideas.md"
    out.write_text(md, encoding="utf-8")
    return out


def make_report(url: str, meta: dict, text: str, html_err: str | None, signals: list[str], workdir: Path) -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"""# CHEONOK Threads Signal Scout Report v0.1

생성시각: {now}

## 1. 입력 링크

{url}

## 2. 수집 상태

- html_fetch: {'OK' if not html_err else 'FAILED'}
- html_error: {html_err or '-'}

## 3. 메타데이터

```json
{json.dumps(meta, ensure_ascii=False, indent=2)}
```

## 4. 텍스트 미리보기

```text
{text[:5000] if text else 'NO TEXT'}
```

## 5. 정본 신호

{chr(10).join(['- ' + s for s in signals]) if signals else '- 감지 신호 부족'}
"""
    out = workdir / "report.md"
    out.write_text(report, encoding="utf-8")
    return out


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/social_signal_threads_v01.py <Threads URL>")
        sys.exit(1)

    url = sys.argv[1].strip()
    name = datetime.now().strftime("%Y%m%d_%H%M%S_") + safe_name(urlparse(url).netloc + "_" + url)
    workdir = OUT_DIR / name
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "input_url.txt").write_text(url, encoding="utf-8")

    raw, err = fetch_html(url)
    (workdir / "raw.html").write_text(raw, encoding="utf-8", errors="replace")
    meta = extract_meta(raw) if raw else {}
    text = strip_html(raw) if raw else ""
    signals = detect_signals(" ".join([meta.get("title", ""), meta.get("description", ""), text]))

    metadata = {
        "title": meta.get("title") or "Threads post",
        "description": meta.get("description") or "",
        "uploader": "Threads",
        "duration": "",
        "view_count": "",
        "like_count": "",
        "tags": ["Threads", "SocialSignal"],
        "webpage_url": url,
    }
    (workdir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    make_report(url, meta, text, err, signals, workdir)
    make_content_ideas(url, meta, text, signals, workdir)

    print("CHEONOK Threads Signal Scout v0.1 DONE")
    print("workdir:", workdir)
    print("report:", workdir / "report.md")
    print("content:", workdir / "content_ideas.md")


if __name__ == "__main__":
    main()
