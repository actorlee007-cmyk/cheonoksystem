#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHEONOK YouTube Runtime Engine
- YouTube reference intelligence collector
- Faceless AI YouTube production asset generator
- 5M revenue sprint content queue generator
- PAPER_ONLY safe runtime
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

DEFAULT_CHANNELS = [
    {"name": "Dan Martell", "handle": "@danmartell", "lane": "Founder Operator / SaaS / Delegation"},
    {"name": "TTJ", "handle": "@ttj", "lane": "Coding Monetization / Korean Developer Creator"},
    {"name": "진바이브", "handle": "@진바이브", "lane": "Storytelling / Human Emotion"},
    {"name": "QJC", "handle": "@qjc_qjc", "lane": "Belief Shift / Premium Community"},
    {"name": "CONNECT AI LAB", "handle": "@CONNECT-AI-LAB", "lane": "AI Automation / B2B Practical"},
    {"name": "머스크의 모든것", "handle": "@머스크의모든것", "lane": "Musk First Principles / Speed / Deletion"},
]

DEFAULT_SINGLE_VIDEOS = [
    {"name": "Reference YouTube Video", "video_id": "2-szlpczvtk", "lane": "Single Video Tactical Extraction"},
]

DEFAULT_EXTERNAL_REFERENCES = [
    {
        "name": "TikTok youtubemstery Faceless AI YouTube Claim",
        "url": "https://www.tiktok.com/@youtubemstery/video/7638066799283637526",
        "claim": "Faceless AI YouTube automation made $1.2M in 3 months",
        "verdict": "UNVERIFIED_INCOME_CLAIM",
    }
]


@dataclasses.dataclass
class VideoSignal:
    channel_name: str
    channel_id: str
    video_id: str
    title: str
    description: str
    published_at: str
    views: int
    likes: int
    comments: int
    duration: str
    url: str
    hook_score: float
    revenue_score: float
    cheonok_angle: str
    cash_chain: str
    risk_veto: str


def now_kst() -> dt.datetime:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=9)))


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 10:
        return "***"
    return value[:4] + "..." + value[-4:]


def http_get(path: str, params: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    url = f"{YOUTUBE_API_BASE}/{path}"
    response = requests.get(url, params=params, timeout=timeout)
    if response.status_code >= 400:
        raise RuntimeError(f"YouTube API error {response.status_code}: {response.text[:500]}")
    return response.json()


def normalize_handle(handle: str) -> str:
    return handle[1:] if handle.startswith("@") else handle


def resolve_channel(api_key: str, handle: str, name: str = "") -> Optional[Dict[str, Any]]:
    clean = normalize_handle(handle)

    try:
        data = http_get(
            "channels",
            {"part": "snippet,statistics,contentDetails", "forHandle": clean, "key": api_key},
        )
        items = data.get("items", [])
        if items:
            return items[0]
    except Exception:
        pass

    query = handle or name
    data = http_get(
        "search",
        {"part": "snippet", "type": "channel", "q": query, "maxResults": 1, "key": api_key},
    )
    items = data.get("items", [])
    if not items:
        return None
    channel_id = items[0]["snippet"]["channelId"]
    detail = http_get(
        "channels",
        {"part": "snippet,statistics,contentDetails", "id": channel_id, "key": api_key},
    )
    detail_items = detail.get("items", [])
    return detail_items[0] if detail_items else None


def get_latest_video_ids(api_key: str, uploads_playlist_id: str, max_results: int) -> List[str]:
    data = http_get(
        "playlistItems",
        {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": max(1, min(max_results, 50)),
            "key": api_key,
        },
    )
    ids = []
    for item in data.get("items", []):
        video_id = item.get("contentDetails", {}).get("videoId")
        if video_id:
            ids.append(video_id)
    return ids


def get_video_details(api_key: str, video_ids: List[str]) -> List[Dict[str, Any]]:
    if not video_ids:
        return []
    out = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        data = http_get(
            "videos",
            {"part": "snippet,statistics,contentDetails", "id": ",".join(chunk), "key": api_key},
        )
        out.extend(data.get("items", []))
    return out


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def days_old(published_at: str) -> float:
    try:
        pub = dt.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        age = dt.datetime.now(dt.timezone.utc) - pub
        return max(age.total_seconds() / 86400, 1.0)
    except Exception:
        return 999.0


def score_title(title: str, views: int, published_at: str) -> Tuple[float, float]:
    t = title.lower()
    hook = 0.0
    revenue = 0.0

    if re.search(r"\b(how|why|what|secret|mistake|build|system|framework)\b", t):
        hook += 2
    if re.search(r"\d+", title):
        hook += 1
    if any(x in t for x in ["ai", "automation", "agent", "chatgpt", "gpt"]):
        hook += 2
        revenue += 2
    if any(x in t for x in ["money", "revenue", "business", "sales", "profit", "million", "$", "매출", "수익", "돈"]):
        revenue += 3
    if any(x in t for x in ["mistake", "fail", "problem", "broken", "막힌", "실패", "문제"]):
        hook += 1.5
    if any(x in t for x in ["musk", "elon", "bezos", "jobs", "mrbeast", "billionaire"]):
        hook += 1.5
        revenue += 1

    velocity = views / days_old(published_at)
    if velocity > 100000:
        hook += 4
    elif velocity > 30000:
        hook += 3
    elif velocity > 10000:
        hook += 2
    elif velocity > 3000:
        hook += 1

    return round(hook, 2), round(revenue, 2)


def classify_angle(title: str, lane: str) -> Tuple[str, str, str]:
    t = title.lower()
    if any(x in t for x in ["ai", "automation", "agent", "chatgpt", "gpt"]):
        return (
            "AI 자동화가 고객의 막힌 지점을 어떻게 해결하는지 CHEONOK 무료진단 CTA로 변환",
            "Exposure -> Lead",
            "AI 대량생산/허위 수익 주장 금지",
        )
    if any(x in t for x in ["money", "revenue", "sales", "profit", "$", "매출", "수익", "돈"]):
        return (
            "수익 주장 검증 후 30만원 매출 병목 진단 상품으로 변환",
            "Lead -> Payment",
            "검증 불가 수익 인증을 사실처럼 사용 금지",
        )
    if any(x in t for x in ["musk", "elon", "first principle", "tesla", "spacex"]):
        return (
            "Musk Algorithm: 질문-삭제-단순화-가속-자동화를 CHEONOK Runtime 병목 제거에 적용",
            "Exit Ledger",
            "유명인 초상/목소리/브랜드 모방 금지",
        )
    if any(x in lane.lower() for x in ["human", "story", "emotion"]):
        return (
            "사람의 고통을 먼저 말하고 안전한 다음 행동으로 연결",
            "Exposure -> Lead",
            "감정 조작/저작권 자산 사용 금지",
        )
    return (
        "상위 1% 패턴을 CHEONOK 콘텐츠/랜딩/챗봇/상품 루프로 변환",
        "Exposure",
        "원리만 흡수, 자산/IP 복제 금지",
    )


def build_video_signal(channel: Dict[str, Any], video: Dict[str, Any], lane: str) -> VideoSignal:
    snippet = video.get("snippet", {})
    stats = video.get("statistics", {})
    details = video.get("contentDetails", {})
    title = snippet.get("title", "")
    published = snippet.get("publishedAt", "")
    views = safe_int(stats.get("viewCount"))
    likes = safe_int(stats.get("likeCount"))
    comments = safe_int(stats.get("commentCount"))
    hook, revenue = score_title(title, views, published)
    angle, cash_chain, veto = classify_angle(title, lane)
    return VideoSignal(
        channel_name=channel.get("snippet", {}).get("title", ""),
        channel_id=channel.get("id", ""),
        video_id=video.get("id", ""),
        title=title,
        description=snippet.get("description", "")[:500],
        published_at=published,
        views=views,
        likes=likes,
        comments=comments,
        duration=details.get("duration", ""),
        url=f"https://www.youtube.com/watch?v={video.get('id', '')}",
        hook_score=hook,
        revenue_score=revenue,
        cheonok_angle=angle,
        cash_chain=cash_chain,
        risk_veto=veto,
    )


def generate_shorts(signals: List[VideoSignal], site_url: str) -> List[Dict[str, str]]:
    seeds = sorted(signals, key=lambda x: (x.hook_score + x.revenue_score, x.views), reverse=True)[:6]
    if not seeds:
        seeds = [
            VideoSignal(
                channel_name="CHEONOK",
                channel_id="",
                video_id="",
                title="Why AI tools do not make money by themselves",
                description="",
                published_at="",
                views=0,
                likes=0,
                comments=0,
                duration="",
                url="",
                hook_score=1,
                revenue_score=1,
                cheonok_angle="AI 도구가 아니라 매출 루프가 필요하다",
                cash_chain="Exposure -> Lead",
                risk_veto="허위 수익 주장 금지",
            )
        ]

    templates = []
    for idx, seed in enumerate(seeds[:3], 1):
        templates.append(
            {
                "asset_type": "SHORTS_SCRIPT",
                "title": f"{idx}. AI 도구를 써도 매출이 안 나는 이유",
                "hook": "열심히 만들었는데 아무도 문의하지 않는다면, 당신이 부족한 게 아니라 시스템의 한 지점이 끊긴 겁니다.",
                "body": (
                    f"레퍼런스 패턴: {seed.title}\n"
                    "문제는 조회수가 아니라 다음 행동입니다.\n"
                    "고객은 이해받고, 신뢰하고, 위험이 낮고, 결제가 쉬울 때 움직입니다.\n"
                    "AI는 영상이나 글을 많이 만드는 도구가 아니라, 이 끊긴 흐름을 이어주는 운영자가 되어야 합니다."
                ),
                "cta": f"링크 하나 보내면 막힌 지점 1개를 무료로 봅니다. {site_url}",
                "cash_chain": "Exposure -> Lead",
                "risk_veto": seed.risk_veto,
            }
        )
    return templates


def generate_longform(signals: List[VideoSignal], site_url: str) -> Dict[str, Any]:
    top = sorted(signals, key=lambda x: (x.hook_score + x.revenue_score, x.views), reverse=True)[:5]
    source_titles = [x.title for x in top]
    return {
        "asset_type": "LONGFORM_OUTLINE",
        "title": "I Built an AI Operator That Finds Why Your Business Is Not Making Money",
        "promise": "AI 도구가 아니라 매출 병목을 찾아 리드와 결제로 연결하는 운영체제 설명",
        "opening_5_seconds": "You are not lazy. Your system may be losing people before they trust you.",
        "structure": [
            "0:00 인간의 상처: 열심히 해도 문의가 없는 상태",
            "0:30 병목 정의: Exposure, Lead, Payment 중 어디가 끊겼는지",
            "2:00 사례: 홈페이지는 있는데 전환이 없는 구조",
            "4:00 AI Operator 구조: 콘텐츠, 챗봇, 결제, 납품 연결",
            "6:00 Faceless YouTube를 AdSense가 아니라 리드 엔진으로 쓰는 방식",
            "8:00 무료진단 CTA와 30만원 실행진단",
        ],
        "source_titles": source_titles,
        "cta": f"Send one link. We will find one revenue bottleneck for free: {site_url}",
        "cash_chain": "Exposure -> Lead -> Payment",
        "risk_veto": "수익 보장/허위 인증/저작권 재사용 금지",
    }


def generate_posts(site_url: str) -> List[Dict[str, str]]:
    return [
        {
            "channel": "Threads/X",
            "text": (
                "조회수는 있는데 문의가 없다면 콘텐츠 문제가 아닐 수 있습니다.\n\n"
                "대부분은 ‘다음 행동’이 안 보이는 구조 문제입니다.\n"
                "첫 문장, 신뢰, 상품, 결제 버튼 중 하나가 끊기면 사람은 보고도 지나갑니다.\n\n"
                f"링크 하나 보내면 막힌 지점 1개를 무료로 봅니다.\n{site_url}"
            ),
        },
        {
            "channel": "Naver Blog/Cafe",
            "text": (
                "제목: 홈페이지는 있는데 문의가 없는 이유\n\n"
                "홈페이지가 있어도 문의가 없다면 디자인보다 흐름을 봐야 합니다.\n"
                "방문자는 예쁜 페이지를 결제하지 않습니다.\n"
                "자기 문제가 이해받고, 결과물이 선명하고, 위험이 낮고, 다음 행동이 쉬울 때 움직입니다.\n\n"
                f"링크 하나만 보내주시면 막힌 지점 1개를 무료로 진단합니다.\n{site_url}"
            ),
        },
        {
            "channel": "B2B DM Draft",
            "text": (
                "안녕하세요. 천옥시스템입니다.\n\n"
                "홈페이지/채널/상품 페이지를 운영 중인데 문의나 결제로 이어지지 않는 경우, "
                "대부분은 디자인보다 고객의 다음 행동이 끊긴 구조에서 문제가 생깁니다.\n\n"
                "링크 하나만 주시면 매출 병목 1개와 바로 고칠 행동 1개를 무료로 정리해드리겠습니다.\n"
                "필요하시면 이후 유료 실행진단/자동화 설계까지 이어갈 수 있습니다."
            ),
        },
    ]


def write_outputs(
    output_dir: Path,
    signals: List[VideoSignal],
    shorts: List[Dict[str, str]],
    longform: Dict[str, Any],
    posts: List[Dict[str, str]],
    channels_summary: List[Dict[str, Any]],
    external_refs: List[Dict[str, Any]],
    errors: List[str],
    site_url: str,
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "generated_at_kst": now_kst().isoformat(),
        "mode": "PAPER_ONLY",
        "site_url": site_url,
        "channels_summary": channels_summary,
        "external_references": external_refs,
        "signals": [dataclasses.asdict(x) for x in signals],
        "shorts": shorts,
        "longform": longform,
        "posts": posts,
        "errors": errors,
        "final_veto": {
            "LIVE_TRADE": "BLOCKED",
            "CAPITAL_SCALE": "BLOCKED",
            "KIS_ORDER_GATE": "BLOCKED",
            "PAPER_ONLY": True,
        },
    }

    json_path = output_dir / "youtube_intelligence.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = output_dir / "content_queue.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Status", "Asset Type", "Title", "Hook", "Body", "CTA", "Cash Chain", "Risk Veto", "Source", "Revenue Link",
            ],
        )
        writer.writeheader()
        for item in shorts:
            writer.writerow({
                "Status": "READY", "Asset Type": item["asset_type"], "Title": item["title"], "Hook": item["hook"],
                "Body": item["body"], "CTA": item["cta"], "Cash Chain": item["cash_chain"], "Risk Veto": item["risk_veto"],
                "Source": "YouTube Intelligence Runtime", "Revenue Link": site_url,
            })
        writer.writerow({
            "Status": "READY", "Asset Type": longform["asset_type"], "Title": longform["title"],
            "Hook": longform["opening_5_seconds"], "Body": "\n".join(longform["structure"]), "CTA": longform["cta"],
            "Cash Chain": longform["cash_chain"], "Risk Veto": longform["risk_veto"],
            "Source": "YouTube Intelligence Runtime", "Revenue Link": site_url,
        })
        for post in posts:
            writer.writerow({
                "Status": "SEND_READY", "Asset Type": post["channel"], "Title": f"{post['channel']} revenue post",
                "Hook": post["text"].splitlines()[0], "Body": post["text"], "CTA": site_url,
                "Cash Chain": "Exposure -> Lead", "Risk Veto": "외부 대량 발송은 대표 승인 필요",
                "Source": "5M Revenue Sprint", "Revenue Link": site_url,
            })

    posts_path = output_dir / "SEND_READY_POSTS.md"
    posts_path.write_text("# SEND READY POSTS\n\n" + "\n\n---\n\n".join([f"## {p['channel']}\n\n{p['text']}" for p in posts]) + "\n", encoding="utf-8")

    report_lines = [
        "# CHEONOK YouTube Runtime CEO Report", "", f"TIME_KST: {now_kst().strftime('%Y-%m-%d %H:%M:%S')}", "",
        "## EXECUTIVE VERDICT", "", "Python Runtime이 YouTube 레퍼런스를 수집하고, CHEONOK 쇼츠/롱폼/게시문/CTA 자산을 생성했다.", "",
        "## CASH CHAIN", "", "- Exposure: YouTube 레퍼런스 수집 및 후킹 추출", "- Lead: cta-5m.html 무료진단 CTA 생성",
        "- Payment: 30만원 AI 매출 병목 실행진단 연결", "- Delivery: 진단 리포트 납품 구조 유지",
        "- Exit Ledger: JSON/CSV/Markdown 증거 저장", "", "## PROOF", "",
        f"- 분석 영상 수: {len(signals)}", f"- 생성 쇼츠: {len(shorts)}", "- 생성 롱폼: 1", f"- 생성 게시문: {len(posts)}", f"- 출력 폴더: {output_dir}", "", "## TOP SIGNALS", "",
    ]

    for s in sorted(signals, key=lambda x: (x.hook_score + x.revenue_score, x.views), reverse=True)[:10]:
        report_lines.append(f"- [{s.channel_name}] {s.title} | views={s.views} | score={s.hook_score + s.revenue_score} | {s.url}")

    if errors:
        report_lines.extend(["", "## BLOCKERS"])
        for e in errors:
            report_lines.append(f"- {e}")

    report_lines.extend(["", "## FINAL VETO", "", "- LIVE_TRADE: BLOCKED", "- CAPITAL_SCALE: BLOCKED", "- KIS_ORDER_GATE: BLOCKED", "- PAPER_ONLY: TRUE"])

    report_path = output_dir / "CEO_REPORT.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {"json": str(json_path), "csv": str(csv_path), "posts": str(posts_path), "report": str(report_path)}


def push_to_airtable_if_configured(csv_path: Path) -> Optional[str]:
    api_key = os.getenv("AIRTABLE_API_KEY", "").strip()
    base_id = os.getenv("AIRTABLE_BASE_ID", "").strip()
    table_name = os.getenv("AIRTABLE_CONTENT_TABLE", "Content Queue").strip()
    if not api_key or not base_id:
        return None

    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    records = []
    with csv_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({"fields": row})

    sent = 0
    for i in range(0, len(records), 10):
        batch = records[i : i + 10]
        response = requests.post(url, headers=headers, json={"records": batch, "typecast": True}, timeout=20)
        if response.status_code >= 400:
            raise RuntimeError(f"Airtable push failed {response.status_code}: {response.text[:500]}")
        sent += len(batch)
    return f"Airtable pushed records={sent} table={table_name}"


def run_once(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    load_dotenv(root / ".env")
    load_dotenv(Path(".env").resolve())

    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    site_url = os.getenv("CHEONOK_SITE_URL", "https://cheonoksystem.com/cta-5m.html").strip()
    output_base = Path(os.getenv("CHEONOK_OUTPUT_DIR", str(root / "outputs"))).resolve()

    if not api_key:
        print("BLOCK: YOUTUBE_API_KEY is missing. Store it in local .env or environment variable.", file=sys.stderr)
        return 2

    print(f"CHEONOK_RUNTIME=START YOUTUBE_API_KEY={mask_secret(api_key)} PAPER_ONLY=TRUE")

    signals: List[VideoSignal] = []
    errors: List[str] = []
    channel_summaries: List[Dict[str, Any]] = []

    for ref in DEFAULT_CHANNELS:
        try:
            channel = resolve_channel(api_key, ref["handle"], ref["name"])
            if not channel:
                errors.append(f"Channel not found: {ref['name']} {ref['handle']}")
                continue

            uploads = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", "")
            stats = channel.get("statistics", {})
            channel_summaries.append({
                "name": channel.get("snippet", {}).get("title", ref["name"]), "handle": ref["handle"], "channel_id": channel.get("id"),
                "subscriber_count": safe_int(stats.get("subscriberCount")), "view_count": safe_int(stats.get("viewCount")),
                "video_count": safe_int(stats.get("videoCount")), "lane": ref["lane"],
            })

            if uploads:
                video_ids = get_latest_video_ids(api_key, uploads, args.max_videos)
                details = get_video_details(api_key, video_ids)
                for video in details:
                    signals.append(build_video_signal(channel, video, ref["lane"]))
        except Exception as exc:
            errors.append(f"{ref['name']}: {exc}")

    for single in DEFAULT_SINGLE_VIDEOS:
        try:
            details = get_video_details(api_key, [single["video_id"]])
            for video in details:
                pseudo_channel = {"id": video.get("snippet", {}).get("channelId", ""), "snippet": {"title": video.get("snippet", {}).get("channelTitle", single["name"])}}
                signals.append(build_video_signal(pseudo_channel, video, single["lane"]))
        except Exception as exc:
            errors.append(f"{single['name']}: {exc}")

    shorts = generate_shorts(signals, site_url)
    longform = generate_longform(signals, site_url)
    posts = generate_posts(site_url)

    stamp = now_kst().strftime("%Y%m%d_%H%M%S")
    output_dir = output_base / stamp
    paths = write_outputs(output_dir, signals, shorts, longform, posts, channel_summaries, DEFAULT_EXTERNAL_REFERENCES, errors, site_url)

    airtable_status = None
    if args.push_airtable:
        try:
            airtable_status = push_to_airtable_if_configured(Path(paths["csv"]))
        except Exception as exc:
            errors.append(f"Airtable push blocked: {exc}")

    print("CHEONOK_RUNTIME=COMPLETE")
    print(f"REPORT={paths['report']}")
    print(f"CONTENT_QUEUE={paths['csv']}")
    print(f"SEND_READY_POSTS={paths['posts']}")
    if airtable_status:
        print(airtable_status)
    if errors:
        print("BLOCKERS:")
        for err in errors:
            print(f"- {err}")
    return 0 if signals else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CHEONOK YouTube Intelligence Runtime")
    parser.add_argument("--root", default=".", help="Runtime root directory containing .env and outputs")
    parser.add_argument("--max-videos", type=int, default=10, help="Latest videos per channel")
    parser.add_argument("--loop-minutes", type=int, default=0, help="Run forever every N minutes. 0 means run once.")
    parser.add_argument("--push-airtable", action="store_true", help="Push content_queue.csv rows to Airtable if env is configured")
    return parser.parse_args()


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
