# -*- coding: utf-8 -*-
"""
CHEONOK Social Signal Universal Reader v0.1
------------------------------------------
Purpose:
- One module for SNS/social links.
- If media platform: try existing yt-dlp based pipeline v02 + v03.
- If text/web platform: fetch HTML/meta/visible text.
- Always create report.md + content_ideas.md + metadata.json.

Supported best-effort domains:
- TikTok, YouTube, Instagram/Reels: media pipeline first
- Threads, X/Twitter, Reddit, Facebook public, LinkedIn public, Naver Blog/Post, Brunch, Medium, Tistory: text fallback
- Unknown URLs: generic HTML fallback

Rule:
- Single-link analysis only.
- No login bypass.
- No mass crawling.
- If a platform blocks content, save BLOCKED/HOLD report instead of forcing access.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
OUT_DIR = ROOT / "data" / "social_signal_scout"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MEDIA_DOMAINS = [
    "tiktok.com",
    "vt.tiktok.com",
    "youtube.com",
    "m.youtube.com",
    "youtu.be",
    "instagram.com/reel",
    "instagram.com/p/",
]

SOCIAL_DOMAINS = [
    "threads.net",
    "threads.com",
    "x.com",
    "twitter.com",
    "reddit.com",
    "facebook.com",
    "linkedin.com",
    "blog.naver.com",
    "m.blog.naver.com",
    "post.naver.com",
    "brunch.co.kr",
    "medium.com",
    "tistory.com",
    "instagram.com",
]

SIGNAL_RULES = [
    ("AI/자동화", ["ai", "automation", "자동화", "인공지능", "agent", "에이전트", "claude", "chatgpt", "cursor"]),
    ("현금흐름/수익", ["money", "revenue", "income", "earn", "수익", "돈", "매출", "달러", "$", "profit"]),
    ("창업/비즈니스", ["startup", "founder", "business", "사업", "창업", "스타트업", "ceo", "operator"]),
    ("콘텐츠/유입", ["content", "creator", "youtube", "shorts", "reels", "threads", "콘텐츠", "유입", "조회수"]),
    ("도구/소프트웨어", ["tool", "software", "github", "open source", "도구", "프로그램", "app", "앱"]),
    ("사람 가치/동반성장", ["human", "value", "성실", "사람", "가치", "성장", "동반"]),
    ("불편함/문제", ["problem", "pain", "friction", "불편", "문제", "귀찮", "어렵", "힘들"]),
    ("작은 팀/레버리지", ["small team", "solo", "1 person", "leverage", "작은 팀", "혼자", "1인"]),
    ("니치/포맷", ["niche", "format", "니치", "포맷"]),
]


def safe_name(text: str) -> str:
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"[^a-zA-Z0-9가-힣_.-]+", "_", text)
    return text[:90].strip("_") or "social_signal"


def run_cmd(cmd, timeout=1800):
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return p.returncode, p.stdout, p.stderr


def is_media_url(url: str) -> bool:
    low = url.lower()
    return any(d in low for d in MEDIA_DOMAINS)


def platform_name(url: str) -> str:
    low = url.lower()
    if "tiktok" in low:
        return "TikTok"
    if "youtube" in low or "youtu.be" in low:
        return "YouTube"
    if "instagram" in low:
        return "Instagram"
    if "threads" in low:
        return "Threads"
    if "x.com" in low or "twitter" in low:
        return "X/Twitter"
    if "reddit" in low:
        return "Reddit"
    if "facebook" in low:
        return "Facebook"
    if "linkedin" in low:
        return "LinkedIn"
    if "naver" in low:
        return "Naver"
    if "brunch" in low:
        return "Brunch"
    if "medium" in low:
        return "Medium"
    if "tistory" in low:
        return "Tistory"
    return urlparse(url).netloc or "Unknown"


def latest_report() -> Path | None:
    files = list(OUT_DIR.rglob("report.md"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def run_media_pipeline(url: str) -> tuple[Path | None, str | None]:
    v02 = TOOLS / "social_signal_scout_v02.py"
    v03 = TOOLS / "social_signal_scout_v03_analyze.py"
    if not v02.exists() or not v03.exists():
        return None, "MEDIA_PIPELINE_SCRIPT_NOT_FOUND"

    before = latest_report()
    code, out, err = run_cmd([sys.executable, str(v02), url], timeout=1800)
    if code != 0:
        return None, err or out or f"v02 exit {code}"

    rep = latest_report()
    if not rep or rep == before:
        # Still accept latest if only one exists.
        rep = latest_report()
    if not rep:
        return None, "REPORT_NOT_FOUND_AFTER_V02"

    workdir = rep.parent
    code, out, err = run_cmd([sys.executable, str(v03), str(workdir)], timeout=600)
    if code != 0:
        return None, err or out or f"v03 exit {code}"
    return workdir, None


def fetch_html(url: str) -> tuple[str, str | None]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123 Safari/537.36",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=35) as r:
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
            rf'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']{re.escape(prop)}["\']',
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

    # JSON-LD rough extraction
    jsonld_texts = []
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', raw, flags=re.I | re.S):
        s = html.unescape(m.group(1)).strip()
        jsonld_texts.append(s[:5000])

    return {
        "title": meta_prop("og:title") or meta_prop("twitter:title") or title,
        "description": meta_prop("og:description") or meta_prop("twitter:description") or meta_prop("description"),
        "site_name": meta_prop("og:site_name"),
        "image": meta_prop("og:image") or meta_prop("twitter:image"),
        "url": meta_prop("og:url"),
        "jsonld_preview": "\n".join(jsonld_texts)[:8000],
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
    found = []
    for name, keys in SIGNAL_RULES:
        if any(k in low for k in keys):
            found.append(name)
    return found


def infer_desires(signals: list[str]) -> list[str]:
    out = []
    if "불편함/문제" in signals:
        out.append("불편함을 빠르게 해결하고 싶다")
    if "현금흐름/수익" in signals:
        out.append("지금 돈이 도는 구조를 만들고 싶다")
    if "AI/자동화" in signals:
        out.append("반복 작업을 AI와 시스템에 맡기고 싶다")
    if "콘텐츠/유입" in signals:
        out.append("콘텐츠를 통해 유입과 신뢰를 만들고 싶다")
    if "작은 팀/레버리지" in signals:
        out.append("작은 팀이나 혼자서도 큰 결과를 만들고 싶다")
    if "사람 가치/동반성장" in signals:
        out.append("사람의 경험과 가치를 시스템으로 키우고 싶다")
    if not out:
        out.append("새로운 기회와 신호를 빨리 포착하고 싶다")
    return out


def write_text_pipeline(url: str, platform: str, raw: str, fetch_err: str | None) -> Path:
    name = datetime.now().strftime("%Y%m%d_%H%M%S_") + safe_name(platform + "_" + url)
    workdir = OUT_DIR / name
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "input_url.txt").write_text(url, encoding="utf-8")
    (workdir / "raw.html").write_text(raw or "", encoding="utf-8", errors="replace")

    meta = extract_meta(raw) if raw else {}
    visible = strip_html(raw) if raw else ""
    combined = "\n".join([meta.get("title", ""), meta.get("description", ""), meta.get("jsonld_preview", ""), visible])
    signals = detect_signals(combined)
    desires = infer_desires(signals)
    verdict = "PASS as social/web signal" if signals else "HOLD — weak or blocked signal"

    metadata = {
        "title": meta.get("title") or f"{platform} link",
        "description": meta.get("description") or "",
        "uploader": platform,
        "duration": "",
        "view_count": "",
        "like_count": "",
        "tags": [platform, "SocialSignal"],
        "webpage_url": url,
    }
    (workdir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"""# CHEONOK Universal Social Signal Report v0.1

생성시각: {now}

## 1. 입력 링크

{url}

## 2. 플랫폼

{platform}

## 3. 수집 상태

- html_fetch: {'OK' if raw else 'FAILED'}
- html_error: {fetch_err or '-'}

## 4. 메타데이터

```json
{json.dumps(meta, ensure_ascii=False, indent=2)}
```

## 5. 텍스트 미리보기

```text
{combined[:6000] if combined else 'NO TEXT'}
```

## 6. 정본 신호

{chr(10).join(['- ' + s for s in signals]) if signals else '- 감지 신호 부족'}
"""
    (workdir / "report.md").write_text(report, encoding="utf-8")

    content = f"""# CHEONOK Universal Social Signal v0.1 — Content Conversion Report

생성시각: {now}

## 1. 원본 요약

- platform: {platform}
- url: {url}
- title: {metadata['title']}
- description: {metadata['description']}

## 2. 정본 판정

판정: **{verdict}**

감지 신호:

{chr(10).join(['- ' + s for s in signals]) if signals else '- 감지 신호 부족'}

## 3. 사람들이 반응하는 원초적 욕망

{chr(10).join(['- ' + d for d in desires])}

## 4. 위험/검증 포인트

- 플랫폼이 로그인/차단/동적 렌더링을 요구하면 본문이 일부만 수집될 수 있음
- 공개 링크 단건 분석만 사용
- 신호는 PASS 가능하나 증거로 쓰기 전 검증 필요

## 5. CHEONOK식 해석

```text
이 링크는 단순 정보가 아니라 대중이 저장·공유·반응하는 욕망 신호로 본다.
CHEONOK은 이를 그대로 베끼지 않고,
불편함 해소·현실 현금흐름·콘텐츠 유입·사람 가치 증폭 구조로 변환한다.
```

## 6. 콘텐츠 아이디어 초안

1. 이 신호에서 드러난 불편함을 해결하는 방법
2. 이 문장/영상이 사람들에게 먹히는 이유
3. CHEONOK은 이 신호를 어떤 도구·콘텐츠·상품으로 바꿀 수 있는가

## 7. 다음 행동

```text
1. 같은 유형 신호 3~5개 추가 수집
2. 반복 신호를 Social Signal Index에서 확인
3. 홈페이지/콘텐츠/상품 문구로 변환
```
"""
    (workdir / "content_ideas.md").write_text(content, encoding="utf-8")
    return workdir


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/social_signal_universal_v01.py <SNS URL>")
        sys.exit(1)

    url = sys.argv[1].strip()
    platform = platform_name(url)

    if is_media_url(url):
        workdir, err = run_media_pipeline(url)
        if workdir:
            print("CHEONOK Universal Reader used MEDIA pipeline")
            print("workdir:", workdir)
            sys.exit(0)
        else:
            # fallback to text fetch
            raw, ferr = fetch_html(url)
            workdir = write_text_pipeline(url, platform, raw, f"media_failed: {err}; html: {ferr}")
            print("CHEONOK Universal Reader MEDIA failed, used TEXT fallback")
            print("workdir:", workdir)
            sys.exit(0)

    raw, err = fetch_html(url)
    workdir = write_text_pipeline(url, platform, raw, err)
    print("CHEONOK Universal Reader used TEXT pipeline")
    print("workdir:", workdir)
    print("report:", workdir / "report.md")
    print("content:", workdir / "content_ideas.md")


if __name__ == "__main__":
    main()
