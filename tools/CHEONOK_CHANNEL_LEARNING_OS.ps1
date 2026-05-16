# CHEONOK CHANNEL LEARNING OS v0.1
# One-file installer/runner.
# Purpose:
# - Paste a YouTube channel/playlist URL.
# - Collect channel video map using yt-dlp flat playlist.
# - Score videos by CHEONOK categories.
# - Generate Channel Intelligence Report.
# - Optionally deep analyze top N videos through existing Social Signal pipeline.
#
# Usage:
# powershell -ExecutionPolicy Bypass -File tools\CHEONOK_CHANNEL_LEARNING_OS.ps1
# powershell -ExecutionPolicy Bypass -File tools\CHEONOK_CHANNEL_LEARNING_OS.ps1 -ChannelUrl "https://www.youtube.com/@channel" -Limit 80 -DeepAnalyze 3

param(
    [string]$ChannelUrl = "",
    [int]$Limit = 80,
    [int]$DeepAnalyze = 0
)

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Base = Join-Path $Desktop "CHEONOK_SOCIAL_SCOUT"
$Tools = Join-Path $Base "tools"
$Data = Join-Path $Base "data"
$ChannelData = Join-Path $Data "channel_learning"
$RawBase = "https://raw.githubusercontent.com/actorlee007-cmyk/cheonoksystem/main/tools"

New-Item -ItemType Directory -Force -Path $Tools | Out-Null
New-Item -ItemType Directory -Force -Path $ChannelData | Out-Null

Write-Host "============================================================" -ForegroundColor Green
Write-Host "CHEONOK CHANNEL LEARNING OS v0.1" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Base:" $Base -ForegroundColor Yellow
Write-Host "Output:" $ChannelData -ForegroundColor Yellow

Write-Host "[1/5] Install/update yt-dlp" -ForegroundColor Cyan
python -m pip install --upgrade yt-dlp

Write-Host "[2/5] Download supporting Social Signal scripts" -ForegroundColor Cyan
try { Invoke-WebRequest -Uri "$RawBase/social_signal_universal_v01.py" -OutFile (Join-Path $Tools "social_signal_universal_v01.py") } catch {}
try { Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v02.py" -OutFile (Join-Path $Tools "social_signal_scout_v02.py") } catch {}
try { Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v03_analyze.py" -OutFile (Join-Path $Tools "social_signal_scout_v03_analyze.py") } catch {}
try { Invoke-WebRequest -Uri "$RawBase/social_signal_scout_v04_db.py" -OutFile (Join-Path $Tools "social_signal_scout_v04_db.py") } catch {}

$PyPath = Join-Path $Tools "cheonok_channel_learning_os.py"

Write-Host "[3/5] Create/Update Python engine" -ForegroundColor Cyan
$Py = @'
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
DATA = ROOT / "data"
CHANNEL_DATA = DATA / "channel_learning"
SOCIAL_DATA = DATA / "social_signal_scout"
CHANNEL_DATA.mkdir(parents=True, exist_ok=True)

CATEGORY_RULES = {
    "AI_AGENT_RUNTIME": ["claude", "cursor", "agent", "에이전트", "automation", "자동화", "runtime", "워크플로우", "업무 자동화", "vibe coding", "코딩"],
    "LLM_INTERNALS_EDUCATION": ["llm", "gpt", "transformer", "트랜스포머", "tokenizer", "토크나이저", "pytorch", "nanogpt", "from scratch", "학습", "강의", "워크숍"],
    "PAIN_TO_PRODUCT": ["불편", "문제", "귀찮", "해결", "pain", "problem", "friction", "아이템", "상품화"],
    "PROVEN_SYSTEM_REVERSE": ["성공", "복제", "2등", "3등", "benchmark", "case study", "사례", "역추적", "비즈니스 모델"],
    "SUBSCRIPTION_BUSINESS": ["구독", "subscription", "saas", "멤버십", "가격", "결제", "pricing", "유료화"],
    "CONTENT_GROWTH": ["유튜브", "쇼츠", "콘텐츠", "조회수", "알고리즘", "shorts", "creator", "카피라이팅", "후킹"],
    "MARKET_INVESTING": ["주식", "투자", "시장", "금리", "환율", "테마", "매크로", "트레이딩", "증권"],
    "TOOL_DISCOVERY": ["github", "오픈소스", "open source", "tool", "도구", "앱", "software", "소프트웨어"],
}

WEIGHTS = {
    "AI_AGENT_RUNTIME": 22,
    "LLM_INTERNALS_EDUCATION": 18,
    "PAIN_TO_PRODUCT": 24,
    "PROVEN_SYSTEM_REVERSE": 24,
    "SUBSCRIPTION_BUSINESS": 20,
    "CONTENT_GROWTH": 16,
    "MARKET_INVESTING": 16,
    "TOOL_DISCOVERY": 14,
}


def run_cmd(cmd, timeout=900):
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def safe_name(text: str) -> str:
    text = re.sub(r"https?://", "", text or "")
    text = re.sub(r"[^a-zA-Z0-9가-힣_.-]+", "_", text)
    return text[:90].strip("_") or "channel"


def normalize_url(item: dict) -> str:
    url = item.get("url") or item.get("webpage_url") or item.get("original_url") or ""
    if isinstance(url, str) and url.startswith("http"):
        return url
    vid = item.get("id")
    if vid:
        return f"https://www.youtube.com/watch?v={vid}"
    return ""


def fetch_channel_items(url: str, limit: int):
    # flat playlist avoids mass video downloads.
    cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--playlist-end", str(limit), url]
    code, out, err = run_cmd(cmd, timeout=1200)
    items = []
    if code != 0:
        return items, err or out
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except Exception:
            pass
    return items, None


def detect_categories(text: str):
    low = (text or "").lower()
    cats = []
    for cat, keys in CATEGORY_RULES.items():
        if any(k.lower() in low for k in keys):
            cats.append(cat)
    return cats


def score_item(item: dict):
    title = item.get("title") or ""
    desc = item.get("description") or ""
    text = f"{title}\n{desc}"
    cats = detect_categories(text)
    score = sum(WEIGHTS.get(c, 10) for c in cats)
    title_low = title.lower()
    # High-intent modifiers
    for k in ["상위", "0.1%", "비결", "숨은", "처음부터", "from scratch", "실전", "핵심", "완벽", "정리"]:
        if k.lower() in title_low:
            score += 5
    # If no category, keep as low score rather than discard.
    if not cats:
        score += 1
    return score, cats


def run_deep_analysis(url: str):
    universal = TOOLS / "social_signal_universal_v01.py"
    db = TOOLS / "social_signal_scout_v04_db.py"
    if not universal.exists():
        return False, "universal reader not found"
    code, out, err = run_cmd([sys.executable, str(universal), url], timeout=2400)
    if code != 0:
        return False, (err or out)[:1000]
    reports = list(SOCIAL_DATA.rglob("report.md"))
    if not reports:
        return False, "report.md not found"
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    workdir = latest.parent
    if db.exists():
        run_cmd([sys.executable, str(db), str(workdir)], timeout=600)
    return True, str(workdir)


def build_report(channel_url: str, items: list[dict], rows: list[dict], deep_results: list[dict], outdir: Path):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cat_counter = Counter()
    word_counter = Counter()
    for r in rows:
        for c in r["categories"]:
            cat_counter[c] += 1
        for w in re.findall(r"[A-Za-z가-힣0-9]{2,}", r["title"]):
            if len(w) >= 2:
                word_counter[w.lower()] += 1

    top_rows = sorted(rows, key=lambda x: x["score"], reverse=True)
    md = []
    md.append("# CHEONOK Channel Intelligence Report v0.1")
    md.append("")
    md.append(f"생성시각: {now}")
    md.append(f"채널/플레이리스트 URL: {channel_url}")
    md.append(f"수집 영상 수: {len(items)}")
    md.append("")

    md.append("## 1. 정본 판정")
    md.append("")
    md.append("```text")
    md.append("채널 지도화: PASS")
    md.append("무차별 전체 다운로드: BLOCK")
    md.append("상위 후보 선별 후 심층 분석: PASS")
    md.append("채널 지식의 CHEONOK식 흡수: PASS")
    md.append("대본/문구 그대로 복제: BLOCK")
    md.append("```")
    md.append("")

    md.append("## 2. 채널 핵심 카테고리")
    md.append("")
    if cat_counter:
        for cat, n in cat_counter.most_common():
            md.append(f"- {cat}: {n}")
    else:
        md.append("- 강한 카테고리 신호 부족")
    md.append("")

    md.append("## 3. 반복 키워드")
    md.append("")
    for w, n in word_counter.most_common(30):
        md.append(f"- {w}: {n}")
    md.append("")

    md.append("## 4. 우선 분석 영상 TOP 20")
    md.append("")
    for i, r in enumerate(top_rows[:20], 1):
        md.append(f"### {i}. {r['title']}")
        md.append(f"- Score: {r['score']}")
        md.append(f"- Categories: {', '.join(r['categories']) if r['categories'] else '-'}")
        md.append(f"- URL: {r['url']}")
        md.append("")

    md.append("## 5. CHEONOK 흡수 포인트")
    md.append("")
    md.append("```text")
    md.append("1. 많이 반복되는 주제는 구독자가 이미 궁금해하는 주제다.")
    md.append("2. 조회/후킹이 강한 제목은 대중 욕망과 불편함을 드러낸다.")
    md.append("3. 그대로 따라 하지 말고, 불편함 해결 구조·학습 구조·운영 루프만 흡수한다.")
    md.append("4. 채널별 철학은 CHEONOK 정본과 충돌시켜 PASS/HOLD/BLOCK으로 분류한다.")
    md.append("```")
    md.append("")

    md.append("## 6. 홈페이지/구독제 반영 후보")
    md.append("")
    if cat_counter.get("AI_AGENT_RUNTIME") or cat_counter.get("LLM_INTERNALS_EDUCATION"):
        md.append("- AI를 많이 쓰는 것보다, AI가 일하는 구조를 이해하고 운영하는 사람이 앞서갑니다.")
        md.append("- CHEONOK은 AI 도구를 나열하지 않고 수집·분석·검증·보고 루프를 만듭니다.")
    if cat_counter.get("PAIN_TO_PRODUCT"):
        md.append("- 사람들은 반복되는 불편함이 사라질 때 돈을 냅니다.")
    if cat_counter.get("PROVEN_SYSTEM_REVERSE"):
        md.append("- 이미 성공한 시스템의 겉모습이 아니라 작동 구조를 역추적합니다.")
    if not cat_counter:
        md.append("- 이 채널은 추가 샘플 분석 후 홈페이지 반영 여부를 판단한다.")
    md.append("")

    md.append("## 7. 심층 분석 결과")
    md.append("")
    if deep_results:
        for r in deep_results:
            md.append(f"- {'PASS' if r['ok'] else 'FAIL'}: {r['url']} -> {r['info']}")
    else:
        md.append("- 이번 실행에서는 심층 분석을 수행하지 않음")
    md.append("")

    md.append("## 8. 다음 실행 3개")
    md.append("")
    md.append("```text")
    md.append("1. TOP 10 중 CHEONOK 핵심과 가장 겹치는 영상 3개를 심층 분석한다.")
    md.append("2. 채널별 반복 카테고리를 Channel Memory DB에 누적한다.")
    md.append("3. 홈페이지/광고/구독자 교육에 반영할 문구와 상품 모듈을 분리한다.")
    md.append("```")
    md.append("")
    md.append("현재 상태: 자율 학습 및 PAPER 데이터 축적 상태 / 실전 주문·자본 확대·자동 주문 차단.")

    out = outdir / "channel_intelligence_report.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("channel_url")
    ap.add_argument("--limit", type=int, default=80)
    ap.add_argument("--deep", type=int, default=0)
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = CHANNEL_DATA / f"channel_{stamp}_{safe_name(args.channel_url)}"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "input_url.txt").write_text(args.channel_url, encoding="utf-8")

    print("[ChannelScout] collecting metadata...")
    items, err = fetch_channel_items(args.channel_url, args.limit)
    if err:
        (outdir / "error.txt").write_text(err, encoding="utf-8")
        print("ERROR:", err[:2000])
    (outdir / "raw_items.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = []
    for item in items:
        title = item.get("title") or ""
        url = normalize_url(item)
        score, cats = score_item(item)
        rows.append({
            "title": title,
            "url": url,
            "score": score,
            "categories": cats,
            "id": item.get("id") or "",
            "duration": item.get("duration") or "",
        })

    rows_sorted = sorted(rows, key=lambda x: x["score"], reverse=True)
    csv_path = outdir / "channel_video_rank.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["score", "categories", "title", "url", "id", "duration"])
        for r in rows_sorted:
            w.writerow([r["score"], " | ".join(r["categories"]), r["title"], r["url"], r["id"], r["duration"]])

    deep_results = []
    if args.deep > 0:
        for r in rows_sorted[:args.deep]:
            if not r["url"]:
                continue
            print("[ChannelScout] deep analyze:", r["url"])
            ok, info = run_deep_analysis(r["url"])
            deep_results.append({"url": r["url"], "ok": ok, "info": info})

    report = build_report(args.channel_url, items, rows_sorted, deep_results, outdir)
    print("CHEONOK Channel Learning OS DONE")
    print("report:", report)
    print("csv:", csv_path)


if __name__ == "__main__":
    main()
'@
Set-Content -Path $PyPath -Value $Py -Encoding UTF8

if ([string]::IsNullOrWhiteSpace($ChannelUrl)) {
    Write-Host "[4/5] Channel URL input" -ForegroundColor Cyan
    $ChannelUrl = Read-Host "Paste YouTube channel or playlist URL"
}

if ([string]::IsNullOrWhiteSpace($ChannelUrl)) {
    Write-Host "[ERROR] Channel URL is empty." -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[5/5] Run Channel Learning OS" -ForegroundColor Cyan
Set-Location -LiteralPath $Base
python "tools\cheonok_channel_learning_os.py" "$ChannelUrl" --limit $Limit --deep $DeepAnalyze

$Latest = Get-ChildItem -Path $ChannelData -Filter "channel_intelligence_report.md" -Recurse -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($Latest) {
    Write-Host "[DONE] Report:" $Latest.FullName -ForegroundColor Green
    notepad $Latest.FullName
}
pause
