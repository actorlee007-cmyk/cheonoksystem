#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHEONOK YouTube Runtime Engine v2

정본 방향:
- YouTube API가 정상일 때: 실제 메타데이터 수집 → 패턴 추출 → 매출 자산 생성
- YouTube API가 막혔을 때: 멈추지 않음 → API_BLOCKED로 증거 기록 → 오프라인 레퍼런스 기반 SEND_READY 매출 자산 생성
- 절대 금지: API 실패를 PASS로 보고하지 않음
- 안전장치: PAPER_ONLY, LIVE_TRADE 차단
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

REFERENCE_CHANNELS = [
    {"name": "Dan Martell", "handle": "@danmartell", "lane": "Founder Operator / SaaS / Delegation"},
    {"name": "TTJ", "handle": "@ttj", "lane": "Coding Monetization / Korean Developer Creator"},
    {"name": "진바이브", "handle": "@진바이브", "lane": "Storytelling / Human Emotion"},
    {"name": "QJC", "handle": "@qjc_qjc", "lane": "Belief Shift / Premium Community"},
    {"name": "CONNECT AI LAB", "handle": "@CONNECT-AI-LAB", "lane": "AI Automation / B2B Practical"},
    {"name": "머스크의 모든것", "handle": "@머스크의모든것", "lane": "Musk First Principles / Speed / Deletion"},
]

REFERENCE_CLAIMS = [
    {
        "source": "TikTok youtubemstery",
        "claim": "Faceless AI YouTube automation made $1.2M in 3 months",
        "verdict": "UNVERIFIED_INCOME_CLAIM",
        "adapter": "수익 인증은 사실로 쓰지 않고, workflow/niche/tool/CTA 구조만 추출한다.",
    },
    {
        "source": "Michael Jackson Humanism Adapter",
        "claim": "Human pain before product",
        "verdict": "PRINCIPLE_ONLY",
        "adapter": "가사/음악/초상/안무 복제 없이, 인간의 아픔→희망→안전한 행동 원리만 사용한다.",
    },
]

OFFLINE_SIGNALS = [
    {
        "channel": "CHEONOK Offline Pattern Lab",
        "title": "Why AI Tools Do Not Make Money Until They Become a Revenue System",
        "views": 0,
        "lane": "AI Business Automation",
        "angle": "AI 도구가 아니라 노출→리드→결제→납품 루프를 닫아야 매출이 난다.",
        "cash_chain": "Exposure -> Lead -> Payment",
        "risk_veto": "수익 보장 금지 / 허위 인증 금지",
    },
    {
        "channel": "CHEONOK Offline Pattern Lab",
        "title": "Faceless YouTube Should Be a Lead Engine, Not an AdSense Lottery",
        "views": 0,
        "lane": "Faceless YouTube Revenue Lab",
        "angle": "유튜브를 광고수익 대기실이 아니라 무료진단 리드 생성 엔진으로 설계한다.",
        "cash_chain": "Exposure -> Lead",
        "risk_veto": "재사용 콘텐츠/AI 대량 저품질 금지",
    },
    {
        "channel": "CHEONOK Offline Pattern Lab",
        "title": "The Elon Musk Algorithm for a Broken Small Business Funnel",
        "views": 0,
        "lane": "First Principles Runtime",
        "angle": "질문→삭제→단순화→가속→자동화로 매출 병목을 제거한다.",
        "cash_chain": "Lead -> Payment -> Delivery",
        "risk_veto": "유명인 IP/브랜드 모방 금지",
    },
]


@dataclasses.dataclass
class RuntimeSignal:
    source: str
    title: str
    url: str
    views: int
    hook_score: float
    revenue_score: float
    cheonok_angle: str
    cash_chain: str
    risk_veto: str
    mode: str


def now_kst() -> dt.datetime:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=9)))


def mask_secret(value: str) -> str:
    if not value:
        return ""
    return value[:4] + "..." + value[-4:] if len(value) > 10 else "***"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    raw = path.read_text(encoding="utf-8-sig")
    for line in raw.splitlines():
        line = line.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().lstrip("\ufeff")
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def parse_google_error(text: str) -> str:
    low = text.lower()
    if "api_key_service_blocked" in low or "requests to this api" in low or "permission_denied" in low:
        return "API_KEY_SERVICE_BLOCKED: YouTube Data API v3가 현재 키/프로젝트에서 허용되지 않음"
    if "apikey" in low or "api key not valid" in low:
        return "INVALID_API_KEY"
    if "quota" in low:
        return "QUOTA_BLOCKED"
    return text[:300].replace("\n", " ")


def youtube_get(path: str, params: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        r = requests.get(f"{YOUTUBE_API_BASE}/{path}", params=params, timeout=20)
        if r.status_code >= 400:
            return None, f"YouTube API {r.status_code}: {parse_google_error(r.text)}"
        return r.json(), None
    except Exception as e:
        return None, f"NETWORK_OR_RUNTIME_ERROR: {e}"


def youtube_health_check(api_key: str) -> Tuple[bool, str]:
    # 가장 작은 사전검사. 이것이 막히면 전체 수집을 멈추고 오프라인 매출 자산 생성으로 우회한다.
    data, err = youtube_get("videos", {"part": "id", "id": "dQw4w9WgXcQ", "key": api_key})
    if err:
        return False, err
    return True, "YOUTUBE_API_READY"


def score_title(title: str, views: int = 0) -> Tuple[float, float]:
    t = title.lower()
    hook = 0.0
    revenue = 0.0
    if re.search(r"\b(how|why|what|mistake|build|system|framework|secret)\b", t):
        hook += 2
    if re.search(r"\d+|\$", title):
        hook += 1
    if any(x in t for x in ["ai", "automation", "agent", "chatgpt", "gpt"]):
        hook += 2
        revenue += 2
    if any(x in t for x in ["money", "revenue", "business", "sales", "profit", "million", "매출", "수익", "돈"]):
        revenue += 3
    if any(x in t for x in ["musk", "elon", "mrbeast", "billionaire", "jobs", "bezos"]):
        hook += 1.5
        revenue += 1
    if views > 100000:
        hook += 3
    elif views > 10000:
        hook += 1
    return round(hook, 2), round(revenue, 2)


def offline_signals() -> List[RuntimeSignal]:
    out: List[RuntimeSignal] = []
    for s in OFFLINE_SIGNALS:
        h, r = score_title(s["title"], 0)
        out.append(RuntimeSignal(
            source=s["channel"],
            title=s["title"],
            url="",
            views=0,
            hook_score=h,
            revenue_score=r,
            cheonok_angle=s["angle"],
            cash_chain=s["cash_chain"],
            risk_veto=s["risk_veto"],
            mode="OFFLINE_FALLBACK",
        ))
    return out


def collect_youtube_signals(api_key: str, max_videos: int) -> Tuple[List[RuntimeSignal], List[str], List[Dict[str, Any]]]:
    signals: List[RuntimeSignal] = []
    blockers: List[str] = []
    summaries: List[Dict[str, Any]] = []

    for ref in REFERENCE_CHANNELS:
        handle = ref["handle"].lstrip("@")
        channel_data, err = youtube_get(
            "channels",
            {"part": "snippet,statistics,contentDetails", "forHandle": handle, "key": api_key},
        )
        if err or not channel_data or not channel_data.get("items"):
            blockers.append(f"{ref['name']}: channel lookup blocked or empty: {err or 'NO_ITEMS'}")
            continue

        ch = channel_data["items"][0]
        uploads = ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        stats = ch.get("statistics", {})
        summaries.append({
            "name": ch.get("snippet", {}).get("title", ref["name"]),
            "handle": ref["handle"],
            "channel_id": ch.get("id"),
            "subscriber_count": int(stats.get("subscriberCount", 0)) if stats.get("subscriberCount") else 0,
            "view_count": int(stats.get("viewCount", 0)) if stats.get("viewCount") else 0,
            "video_count": int(stats.get("videoCount", 0)) if stats.get("videoCount") else 0,
            "lane": ref["lane"],
        })
        if not uploads:
            blockers.append(f"{ref['name']}: uploads playlist missing")
            continue

        playlist_data, err = youtube_get(
            "playlistItems",
            {"part": "snippet,contentDetails", "playlistId": uploads, "maxResults": min(max_videos, 50), "key": api_key},
        )
        if err:
            blockers.append(f"{ref['name']}: playlistItems blocked: {err}")
            continue
        ids = [x.get("contentDetails", {}).get("videoId") for x in playlist_data.get("items", [])]
        ids = [x for x in ids if x]
        if not ids:
            continue

        video_data, err = youtube_get(
            "videos",
            {"part": "snippet,statistics,contentDetails", "id": ",".join(ids), "key": api_key},
        )
        if err:
            blockers.append(f"{ref['name']}: videos blocked: {err}")
            continue
        for v in video_data.get("items", []):
            title = v.get("snippet", {}).get("title", "")
            views = int(v.get("statistics", {}).get("viewCount", 0)) if v.get("statistics", {}).get("viewCount") else 0
            h, r = score_title(title, views)
            signals.append(RuntimeSignal(
                source=ch.get("snippet", {}).get("title", ref["name"]),
                title=title,
                url=f"https://www.youtube.com/watch?v={v.get('id', '')}",
                views=views,
                hook_score=h,
                revenue_score=r,
                cheonok_angle="레퍼런스 패턴을 CHEONOK 무료진단→30만원 실행진단→100만원 설계로 변환",
                cash_chain="Exposure -> Lead -> Payment",
                risk_veto="저작권 재사용/허위 수익 주장 금지",
                mode="YOUTUBE_API",
            ))
    return signals, blockers, summaries


def generate_assets(signals: List[RuntimeSignal], site_url: str) -> Tuple[List[Dict[str, str]], Dict[str, Any], List[Dict[str, str]]]:
    ordered = sorted(signals, key=lambda x: (x.hook_score + x.revenue_score, x.views), reverse=True)
    seeds = ordered[:3] or offline_signals()[:3]

    shorts: List[Dict[str, str]] = []
    for i, seed in enumerate(seeds, 1):
        shorts.append({
            "asset_type": "SHORTS_SCRIPT",
            "title": f"{i}. AI를 써도 매출이 안 나는 진짜 이유",
            "hook": "열심히 만들었는데 문의가 없다면, 당신이 부족한 게 아니라 고객이 다음 행동을 못 찾는 겁니다.",
            "body": (
                f"레퍼런스 신호: {seed.title}\n"
                "대부분은 콘텐츠 양이 아니라 흐름이 끊긴 문제입니다.\n"
                "사람은 이해받고, 믿고, 위험이 낮고, 결제가 쉬울 때 움직입니다.\n"
                "AI는 더 많이 만드는 도구가 아니라, 끊긴 매출 루프를 이어주는 운영자가 되어야 합니다."
            ),
            "cta": f"링크 하나 보내면 막힌 지점 1개를 무료로 봅니다. {site_url}",
            "cash_chain": "Exposure -> Lead",
            "risk_veto": seed.risk_veto,
        })

    longform = {
        "asset_type": "LONGFORM_OUTLINE",
        "title": "I Built an AI Operator That Finds Why Your Business Is Not Making Money",
        "opening_5_seconds": "You are not lazy. Your system may be losing people before they trust you.",
        "structure": [
            "0:00 인간의 상처: 열심히 해도 문의가 없는 상태",
            "0:30 병목 정의: 노출, 리드, 결제 중 어디가 끊겼는지",
            "2:00 사례: 홈페이지는 있는데 전환이 없는 구조",
            "4:00 AI Operator 구조: 콘텐츠, 챗봇, 결제, 납품 연결",
            "6:00 Faceless YouTube를 AdSense가 아니라 리드 엔진으로 쓰는 방식",
            "8:00 무료진단 CTA와 30만원 실행진단",
        ],
        "cta": f"Send one link. We will find one revenue bottleneck for free: {site_url}",
        "cash_chain": "Exposure -> Lead -> Payment",
        "risk_veto": "수익 보장/허위 인증/저작권 재사용 금지",
    }

    posts = [
        {
            "channel": "Threads/X",
            "text": "조회수는 있는데 문의가 없다면 콘텐츠 문제가 아닐 수 있습니다.\n\n대부분은 ‘다음 행동’이 안 보이는 구조 문제입니다.\n첫 문장, 신뢰, 상품, 결제 버튼 중 하나가 끊기면 사람은 보고도 지나갑니다.\n\n링크 하나 보내면 막힌 지점 1개를 무료로 봅니다.\n" + site_url,
        },
        {
            "channel": "Naver Blog/Cafe",
            "text": "제목: 홈페이지는 있는데 문의가 없는 이유\n\n홈페이지가 있어도 문의가 없다면 디자인보다 흐름을 봐야 합니다. 방문자는 예쁜 페이지를 결제하지 않습니다. 자기 문제가 이해받고, 결과물이 선명하고, 위험이 낮고, 다음 행동이 쉬울 때 움직입니다.\n\n링크 하나만 보내주시면 막힌 지점 1개를 무료로 진단합니다.\n" + site_url,
        },
        {
            "channel": "B2B DM Draft",
            "text": "안녕하세요. 천옥시스템입니다.\n\n홈페이지/채널/상품 페이지를 운영 중인데 문의나 결제로 이어지지 않는 경우, 대부분은 디자인보다 고객의 다음 행동이 끊긴 구조에서 문제가 생깁니다.\n\n링크 하나만 주시면 매출 병목 1개와 바로 고칠 행동 1개를 무료로 정리해드리겠습니다.",
        },
    ]
    return shorts, longform, posts


def write_outputs(
    output_dir: Path,
    runtime_status: str,
    api_status: str,
    signals: List[RuntimeSignal],
    blockers: List[str],
    summaries: List[Dict[str, Any]],
    shorts: List[Dict[str, str]],
    longform: Dict[str, Any],
    posts: List[Dict[str, str]],
    site_url: str,
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "generated_at_kst": now_kst().isoformat(),
        "runtime_status": runtime_status,
        "api_status": api_status,
        "mode": "PAPER_ONLY",
        "site_url": site_url,
        "reference_channels": REFERENCE_CHANNELS,
        "reference_claims": REFERENCE_CLAIMS,
        "channel_summaries": summaries,
        "signals": [dataclasses.asdict(x) for x in signals],
        "shorts": shorts,
        "longform": longform,
        "posts": posts,
        "blockers": blockers,
        "final_veto": {"LIVE_TRADE": "BLOCKED", "CAPITAL_SCALE": "BLOCKED", "KIS_ORDER_GATE": "BLOCKED", "PAPER_ONLY": True},
    }
    json_path = output_dir / "youtube_intelligence.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = output_dir / "content_queue.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Status", "Asset Type", "Title", "Hook", "Body", "CTA", "Cash Chain", "Risk Veto", "Source", "Revenue Link"])
        writer.writeheader()
        for s in shorts:
            writer.writerow({"Status": "SEND_READY", "Asset Type": s["asset_type"], "Title": s["title"], "Hook": s["hook"], "Body": s["body"], "CTA": s["cta"], "Cash Chain": s["cash_chain"], "Risk Veto": s["risk_veto"], "Source": "CHEONOK Runtime", "Revenue Link": site_url})
        writer.writerow({"Status": "READY", "Asset Type": longform["asset_type"], "Title": longform["title"], "Hook": longform["opening_5_seconds"], "Body": "\n".join(longform["structure"]), "CTA": longform["cta"], "Cash Chain": longform["cash_chain"], "Risk Veto": longform["risk_veto"], "Source": "CHEONOK Runtime", "Revenue Link": site_url})
        for p in posts:
            writer.writerow({"Status": "SEND_READY", "Asset Type": p["channel"], "Title": f"{p['channel']} revenue post", "Hook": p["text"].splitlines()[0], "Body": p["text"], "CTA": site_url, "Cash Chain": "Exposure -> Lead", "Risk Veto": "외부 대량 발송은 대표 승인 필요", "Source": "5M Revenue Sprint", "Revenue Link": site_url})

    posts_path = output_dir / "SEND_READY_POSTS.md"
    posts_path.write_text("# SEND READY POSTS\n\n" + "\n\n---\n\n".join([f"## {p['channel']}\n\n{p['text']}" for p in posts]) + "\n", encoding="utf-8")

    report = [
        "# CHEONOK YouTube Runtime CEO Report",
        "",
        f"TIME_KST: {now_kst().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## VERDICT",
        f"- Runtime: {runtime_status}",
        f"- YouTube API: {api_status}",
        "- Revenue Assets: GENERATED",
        "- API 실패를 PASS로 보고하지 않음. API가 막히면 오프라인 레퍼런스 기반 매출 자산을 생성함.",
        "",
        "## CASH CHAIN",
        "- Exposure: 쇼츠/게시문/롱폼 생성",
        f"- Lead: {site_url}",
        "- Payment: 300,000 KRW AI 매출 병목 실행진단",
        "- Delivery: 진단 리포트 납품",
        "- Exit Ledger: JSON/CSV/Markdown 기록",
        "",
        "## PROOF",
        f"- Signals: {len(signals)}",
        f"- Shorts: {len(shorts)}",
        "- Longform: 1",
        f"- Posts: {len(posts)}",
        f"- Output: {output_dir}",
        "",
        "## BLOCKERS",
    ]
    if blockers:
        report.extend([f"- {b}" for b in blockers])
    else:
        report.append("- None")
    report.extend(["", "## FINAL VETO", "- LIVE_TRADE: BLOCKED", "- CAPITAL_SCALE: BLOCKED", "- KIS_ORDER_GATE: BLOCKED", "- PAPER_ONLY: TRUE"])

    report_path = output_dir / "CEO_REPORT.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    return {"report": str(report_path), "csv": str(csv_path), "posts": str(posts_path), "json": str(json_path)}


def run_once(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    load_dotenv(root / ".env")
    load_dotenv(Path(".env").resolve())

    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    site_url = os.getenv("CHEONOK_SITE_URL", "https://cheonoksystem.com/cta-5m.html").strip()
    output_base = Path(os.getenv("CHEONOK_OUTPUT_DIR", str(root / "_RUNTIME_OUTPUTS"))).resolve()

    blockers: List[str] = []
    summaries: List[Dict[str, Any]] = []
    runtime_status = "RUNNING"

    if not api_key:
        api_status = "NO_API_KEY"
        blockers.append("YOUTUBE_API_KEY missing. Offline revenue assets generated instead.")
        signals = offline_signals()
    else:
        print(f"CHEONOK_RUNTIME=START YOUTUBE_API_KEY={mask_secret(api_key)} PAPER_ONLY=TRUE")
        ok, api_status = youtube_health_check(api_key)
        if ok:
            signals, api_blockers, summaries = collect_youtube_signals(api_key, args.max_videos)
            blockers.extend(api_blockers)
            if not signals:
                blockers.append("YouTube API ready but no usable signals collected. Offline fallback added.")
                signals = offline_signals()
                runtime_status = "API_READY_WITH_OFFLINE_FALLBACK"
            else:
                runtime_status = "API_COLLECTION_SUCCESS"
        else:
            blockers.append(api_status)
            signals = offline_signals()
            runtime_status = "API_BLOCKED_OFFLINE_REVENUE_ASSETS_GENERATED"

    shorts, longform, posts = generate_assets(signals, site_url)
    output_dir = output_base / now_kst().strftime("%Y%m%d_%H%M%S")
    paths = write_outputs(output_dir, runtime_status, api_status, signals, blockers, summaries, shorts, longform, posts, site_url)

    print("CHEONOK_RUNTIME=COMPLETE")
    print(f"RUNTIME_STATUS={runtime_status}")
    print(f"YOUTUBE_API_STATUS={api_status}")
    print(f"REPORT={paths['report']}")
    print(f"CONTENT_QUEUE={paths['csv']}")
    print(f"SEND_READY_POSTS={paths['posts']}")
    if blockers:
        print("BLOCKERS:")
        for b in blockers:
            print(f"- {b}")
    print("FINAL_VETO: LIVE_TRADE=BLOCKED / CAPITAL_SCALE=BLOCKED / KIS_ORDER_GATE=BLOCKED / PAPER_ONLY=TRUE")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CHEONOK YouTube Runtime Engine v2")
    p.add_argument("--root", default=".")
    p.add_argument("--max-videos", type=int, default=10)
    p.add_argument("--loop-minutes", type=int, default=0)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.loop_minutes and args.loop_minutes > 0:
        while True:
            code = run_once(args)
            print(f"NEXT_RUN_MINUTES={args.loop_minutes} LAST_EXIT={code}")
            time.sleep(args.loop_minutes * 60)
    return run_once(args)


if __name__ == "__main__":
    raise SystemExit(main())
