#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHEONOK Blog Runtime Engine v1

정본 방향:
- Naver Search API가 정상일 때: 실제 상위노출 제목을 수집 -> 경쟁 신호로 활용
- API가 막혔을 때: 멈추지 않음 -> API_BLOCKED로 증거 기록 -> 오프라인 레퍼런스
  기반 SEND_READY 포스팅 초안을 생성
- 절대 금지: API 실패를 PASS로 보고하지 않음, 수익/승인 보장 표현 금지
- 안전장치: PAPER_ONLY, 대량 어뷰징/스팸성 포스팅 금지

이 런타임은 노션 북마크 분류
(docs/JOS_NOTION_BOOKMARK_CLASSIFICATION_2026-06-11.md) 의
- D3 "일기10개로 네이버광고승인" (네이버 애드포스트)
- C5 "Tistory365Blog AI자동화 블로그" (구글 애드센스)
두 항목을 시스템화한 것이다. 수익/승인을 보장하지 않으며, 원칙(꾸준한
실제 기록 기반 포스팅, SEO 구조, CTA 배치)만 채택한다.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import datetime as dt
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

NAVER_API_BASE = "https://openapi.naver.com/v1/search"

REFERENCE_NICHES: List[Dict[str, str]] = [
    {
        "id": "ops_journal",
        "title": "AI 자동화 운영일지",
        "platform": "Naver Blog",
        "monetization": "네이버 애드포스트(AdPost)",
        "seed_keyword": "AI 자동화 후기",
        "source_note": "Notion: 일기10개로 네이버광고승인",
        "angle": "매일의 실제 작업을 일반인이 이해하는 운영일지로 기록 -> 꾸준한 포스팅 빈도가 애드포스트 승인/품질 신호에 유리",
        "cash_chain": "Exposure -> Subscription (누적 트래픽 자산)",
        "risk_veto": "수익/승인 보장 표현 금지. 실제로 수행한 작업만 기록.",
    },
    {
        "id": "automation_tutorial",
        "title": "노코드 AI 자동화 튜토리얼",
        "platform": "Tistory",
        "monetization": "구글 애드센스(AdSense)",
        "seed_keyword": "n8n 자동화 튜토리얼",
        "source_note": "Notion: Tistory365Blog AI자동화 블로그",
        "angle": "n8n/Claude Code로 만든 워크플로를 따라하기 쉬운 튜토리얼로 변환 -> 검색 유입(SEO) + 애드센스 + CHEONOK 리드",
        "cash_chain": "Exposure -> Lead -> Payment",
        "risk_veto": "과장된 결과(매출 보장) 금지. 제휴/추천 시 광고 표시 의무.",
    },
    {
        "id": "paper_trading_recap",
        "title": "AI 페이퍼 트레이딩 리포트 해설",
        "platform": "Naver Blog",
        "monetization": "네이버 애드포스트(AdPost) + 구독 리포트 리드",
        "seed_keyword": "AI 모의투자 리포트",
        "source_note": "automation/python_paper_capital_runtime/JOS_MASTER.py 일일 리포트",
        "angle": "PAPER_ONLY 모의투자 결과를 교육 콘텐츠로 재구성 (투자자문 아님 고지)",
        "cash_chain": "Exposure -> Lead (구독 리포트 안내)",
        "risk_veto": "투자자문 아님 고지 필수. 수익률 보장/특정 종목 매수 권유 금지.",
    },
    {
        "id": "side_project_review",
        "title": "AI 자동화 부업 시스템 후기",
        "platform": "Tistory",
        "monetization": "구글 애드센스(AdSense) + CHEONOK 리드",
        "seed_keyword": "AI 자동화 부업 후기",
        "source_note": "Notion D1 수익모델 카탈로그",
        "angle": "CHEONOK 자체 구축 경험을 검증/미검증으로 구분해 솔직하게 공유 -> 신뢰 기반 리드",
        "cash_chain": "Exposure -> Lead -> Payment",
        "risk_veto": "미검증 수익 주장 금지. 본인 사례만 사용.",
    },
]

REFERENCE_CLAIMS = [
    {
        "source": "Notion: Tistory365Blog AI자동화 블로그",
        "claim": "AI로 티스토리 블로그를 자동화해서 애드센스 수익화",
        "verdict": "PRINCIPLE_ONLY",
        "adapter": "수익 인증은 사실로 쓰지 않고, 포스팅 빈도/SEO 구조/CTA 배치 원칙만 추출한다.",
    },
    {
        "source": "Notion: 일기10개로 네이버광고승인",
        "claim": "꾸준한 일기형 포스팅 10개로 네이버 애드포스트 승인",
        "verdict": "PRINCIPLE_ONLY",
        "adapter": "승인을 보장하지 않되, '꾸준한 실제 기록 기반 포스팅'이라는 구조 원칙만 채택한다.",
    },
    {
        "source": "YouTube 바이브 코딩 (otIIrG2GQZg)",
        "claim": "전문 CS 용어로 정확히 지시하면 결과 품질이 약 45%에서 98%로 상승",
        "verdict": "METHODOLOGY",
        "adapter": "이 런타임의 함수/필드명을 명확한 용어(API_HEALTH_CHECK, CASH_CHAIN, RISK_VETO 등)로 통일해 재사용성과 정확도를 높인다.",
    },
]


@dataclasses.dataclass
class RuntimeSignal:
    source: str
    title: str
    url: str
    hook_score: float
    seo_score: float
    platform: str
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
        line = line.strip().lstrip("﻿")
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().lstrip("﻿")
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def naver_get(endpoint: str, params: Dict[str, Any], client_id: str, client_secret: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        r = requests.get(
            f"{NAVER_API_BASE}/{endpoint}.json",
            params=params,
            headers={"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret},
            timeout=20,
        )
        if r.status_code >= 400:
            return None, f"Naver API {r.status_code}: {r.text[:200].replace(chr(10), ' ')}"
        return r.json(), None
    except Exception as e:
        return None, f"NETWORK_OR_RUNTIME_ERROR: {e}"


def naver_health_check(client_id: str, client_secret: str) -> Tuple[bool, str]:
    # 가장 작은 사전검사. 이것이 막히면 전체 수집을 멈추고 오프라인 포스팅 초안 생성으로 우회한다.
    data, err = naver_get("blog", {"query": "테스트", "display": 1}, client_id, client_secret)
    if err:
        return False, err
    return True, "NAVER_API_READY"


def score_topic(title: str) -> Tuple[float, float]:
    hook = 0.0
    seo = 0.0
    if re.search(r"방법|후기|비교|추천|총정리|정리|가이드", title):
        hook += 2
    if re.search(r"\d+", title):
        hook += 1
    if "무료" in title:
        hook += 1
    low = title.lower()
    if any(x in low for x in ["ai", "자동화", "n8n", "claude", "agent", "에이전트"]):
        seo += 3
    if any(x in title for x in ["부업", "수익", "재테크", "투자", "광고", "애드센스", "애드포스트"]):
        seo += 2
    return round(hook, 2), round(seo, 2)


def offline_signals() -> List[RuntimeSignal]:
    out: List[RuntimeSignal] = []
    for n in REFERENCE_NICHES:
        h, s = score_topic(n["title"])
        out.append(RuntimeSignal(
            source=n["title"],
            title=n["title"],
            url="",
            hook_score=h,
            seo_score=s,
            platform=n["platform"],
            cheonok_angle=n["angle"],
            cash_chain=n["cash_chain"],
            risk_veto=n["risk_veto"],
            mode="OFFLINE_FALLBACK",
        ))
    return out


def collect_naver_signals(client_id: str, client_secret: str, max_results: int) -> Tuple[List[RuntimeSignal], List[str]]:
    signals: List[RuntimeSignal] = []
    blockers: List[str] = []

    for niche in REFERENCE_NICHES:
        data, err = naver_get(
            "blog",
            {"query": niche["seed_keyword"], "display": min(max_results, 10), "sort": "sim"},
            client_id,
            client_secret,
        )
        if err:
            blockers.append(f"{niche['title']}: blog search blocked: {err}")
            continue
        for item in data.get("items", []):
            title = re.sub(r"</?b>", "", item.get("title", ""))
            h, s = score_topic(title)
            signals.append(RuntimeSignal(
                source=niche["title"],
                title=title,
                url=item.get("link", ""),
                hook_score=h,
                seo_score=s,
                platform=niche["platform"],
                cheonok_angle=niche["angle"],
                cash_chain=niche["cash_chain"],
                risk_veto=niche["risk_veto"],
                mode="NAVER_API",
            ))
    return signals, blockers


def build_post_draft(niche: Dict[str, str], top_signal_title: Optional[str], site_url: str) -> Dict[str, Any]:
    nid = niche["id"]
    if nid == "ops_journal":
        title = "혼자서 AI 자동화 시스템 만들기 - 오늘 작업 기록"
        intro = "오늘은 자동화 시스템에서 겪은 문제 하나를 어떻게 풀었는지 기록합니다. 거창한 결과가 아니라 실제로 무엇을 했고 왜 필요했는지를 남깁니다."
        body_outline = [
            "1. 오늘 무엇을 만들었는지 (한 줄 요약)",
            "2. 왜 필요했는지 (어떤 문제가 있었는지)",
            "3. 어떻게 풀었는지 (전문 용어는 풀어서 설명)",
            "4. 결과와 다음에 할 일",
            "5. 같은 고민을 하는 분께 도움될 팁 1개",
        ]
        cta = f"비슷한 자동화가 필요하면 천옥시스템에서 무료로 막힌 부분 1개를 진단받아보세요. {site_url}"
    elif nid == "automation_tutorial":
        title = "n8n + Claude Code로 반복 업무 자동화하는 법 (입문)"
        intro = "이 글은 매일 반복하는 업무 하나를 n8n과 Claude Code로 자동화하는 과정을 처음부터 끝까지 보여줍니다."
        body_outline = [
            "1. 이 자동화가 해결하는 문제",
            "2. 준비물 (계정, API 키 - 코드/공개 저장소에 절대 노출 금지)",
            "3. 단계별 설정 (워크플로 구성)",
            "4. 자주 발생하는 오류와 해결 방법",
            "5. 다음 단계로 확장하는 아이디어",
        ]
        cta = f"더 복잡한 업무 자동화가 필요하면 천옥시스템에서 무료 진단을 받아보세요. {site_url}"
    elif nid == "paper_trading_recap":
        title = "AI가 매일 시뮬레이션하는 모의투자 리포트 해설"
        intro = "이 글은 실제 매매가 아닌 모의투자(Paper Trading) 결과를 바탕으로, AI가 어떤 기준으로 후보를 검토하는지 설명합니다. 투자 권유가 아닙니다."
        body_outline = [
            "1. 오늘의 모의투자 요약 (실거래 아님 고지)",
            "2. 점수/확률 기반 후보 선정 기준 (일반 원리 설명)",
            "3. 오늘 결과와 이유 (손익비/리스크 관리 관점)",
            "4. 내일 관전 포인트",
            "5. 면책 고지: 투자자문 아님, 손실 가능성 있음",
        ]
        cta = f"매일 업데이트되는 리포트가 궁금하다면 구독 안내를 확인하세요. {site_url}"
    else:  # side_project_review
        title = "본업 외에 AI 자동화 시스템 만들어본 솔직한 후기"
        intro = "이 글은 AI 자동화 시스템을 직접 만들면서 겪은 일을, 검증된 부분과 아직 검증되지 않은 부분으로 나누어 솔직하게 정리합니다."
        body_outline = [
            "1. 시작한 계기",
            "2. 실제로 한 일 (검증 가능한 것만)",
            "3. 잘 안 된 부분 (정직하게)",
            "4. 배운 점",
            "5. 관심 있다면? (CTA)",
        ]
        cta = f"같은 고민이 있다면 천옥시스템에서 무료로 1개 진단을 받아보세요. {site_url}"

    return {
        "platform": niche["platform"],
        "monetization": niche["monetization"],
        "title": title,
        "intro": intro,
        "body_outline": body_outline,
        "cta": cta,
        "competitive_reference": top_signal_title or "(오프라인 모드 - 상위노출 제목 미수집)",
        "cash_chain": niche["cash_chain"],
        "risk_veto": niche["risk_veto"],
        "source_note": niche["source_note"],
    }


def generate_assets(signals: List[RuntimeSignal], site_url: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    by_niche: Dict[str, List[RuntimeSignal]] = {}
    for s in signals:
        by_niche.setdefault(s.source, []).append(s)

    posts: List[Dict[str, Any]] = []
    for niche in REFERENCE_NICHES:
        niche_signals = sorted(
            (s for s in by_niche.get(niche["title"], []) if s.mode == "NAVER_API"),
            key=lambda x: x.hook_score + x.seo_score,
            reverse=True,
        )
        top_title = niche_signals[0].title if niche_signals else None
        posts.append(build_post_draft(niche, top_title, site_url))

    posting_schedule = [
        {"day": "Mon/Thu", "platform": "Naver Blog", "niche": "AI 자동화 운영일지"},
        {"day": "Tue/Fri", "platform": "Tistory", "niche": "노코드 AI 자동화 튜토리얼"},
        {"day": "Wed", "platform": "Naver Blog", "niche": "AI 페이퍼 트레이딩 리포트 해설"},
        {"day": "Sat", "platform": "Tistory", "niche": "AI 자동화 부업 시스템 후기"},
    ]
    return posts, posting_schedule


def write_outputs(
    output_dir: Path,
    runtime_status: str,
    api_status: str,
    signals: List[RuntimeSignal],
    blockers: List[str],
    posts: List[Dict[str, Any]],
    posting_schedule: List[Dict[str, str]],
    site_url: str,
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "generated_at_kst": now_kst().isoformat(),
        "runtime_status": runtime_status,
        "api_status": api_status,
        "mode": "PAPER_ONLY",
        "site_url": site_url,
        "reference_niches": REFERENCE_NICHES,
        "reference_claims": REFERENCE_CLAIMS,
        "signals": [dataclasses.asdict(x) for x in signals],
        "posts": posts,
        "posting_schedule": posting_schedule,
        "blockers": blockers,
        "final_veto": {"LIVE_TRADE": "BLOCKED", "CAPITAL_SCALE": "BLOCKED", "KIS_ORDER_GATE": "BLOCKED", "PAPER_ONLY": True},
    }
    json_path = output_dir / "blog_intelligence.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = output_dir / "content_queue.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Status", "Platform", "Monetization", "Title", "Intro", "Body Outline",
            "CTA", "Cash Chain", "Risk Veto", "Source Note", "Competitive Reference", "Revenue Link",
        ])
        writer.writeheader()
        for p in posts:
            writer.writerow({
                "Status": "SEND_READY",
                "Platform": p["platform"],
                "Monetization": p["monetization"],
                "Title": p["title"],
                "Intro": p["intro"],
                "Body Outline": "\n".join(p["body_outline"]),
                "CTA": p["cta"],
                "Cash Chain": p["cash_chain"],
                "Risk Veto": p["risk_veto"],
                "Source Note": p["source_note"],
                "Competitive Reference": p["competitive_reference"],
                "Revenue Link": site_url,
            })

    posts_md = ["# SEND READY BLOG POSTS", ""]
    for p in posts:
        posts_md.append(f"## [{p['platform']}] {p['title']}")
        posts_md.append("")
        posts_md.append(f"수익화: {p['monetization']}")
        posts_md.append("")
        posts_md.append(p["intro"])
        posts_md.append("")
        posts_md.append("### 구성")
        posts_md.extend(p["body_outline"])
        posts_md.append("")
        posts_md.append(f"CTA: {p['cta']}")
        posts_md.append("")
        posts_md.append(f"참고 상위노출 제목: {p['competitive_reference']}")
        posts_md.append("")
        posts_md.append(f"Risk Veto: {p['risk_veto']}")
        posts_md.append("")
        posts_md.append(f"출처: {p['source_note']}")
        posts_md.append("")
        posts_md.append("---")
        posts_md.append("")
    posts_path = output_dir / "SEND_READY_POSTS.md"
    posts_path.write_text("\n".join(posts_md), encoding="utf-8")

    report = [
        "# CHEONOK Blog Runtime CEO Report",
        "",
        f"TIME_KST: {now_kst().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## VERDICT",
        f"- Runtime: {runtime_status}",
        f"- Naver API: {api_status}",
        "- Revenue Assets: GENERATED",
        "- API 실패를 PASS로 보고하지 않음. API가 막히면 오프라인 레퍼런스 기반 포스팅 초안을 생성함.",
        "",
        "## CASH CHAIN",
        "- Exposure: Naver Blog / Tistory 포스팅 초안",
        f"- Lead: {site_url}",
        "- Payment: 300,000 KRW AI 매출 병목 실행진단 (CTA 경유)",
        "- Subscription: 애드포스트/애드센스 누적 트래픽 자산",
        "- Exit Ledger: JSON/CSV/Markdown 기록",
        "",
        "## POSTING SCHEDULE",
    ]
    for sch in posting_schedule:
        report.append(f"- {sch['day']}: [{sch['platform']}] {sch['niche']}")
    report.extend([
        "",
        "## PROOF",
        f"- Signals: {len(signals)}",
        f"- Posts drafted: {len(posts)}",
        f"- Output: {output_dir}",
        "",
        "## BLOCKERS",
    ])
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

    client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    site_url = os.getenv("CHEONOK_SITE_URL", "https://cheonoksystem.com/cta-5m.html").strip()
    output_base = Path(os.getenv("CHEONOK_OUTPUT_DIR", str(root / "_RUNTIME_OUTPUTS"))).resolve()

    blockers: List[str] = []
    runtime_status = "RUNNING"

    if not client_id or not client_secret:
        api_status = "NO_API_KEY"
        blockers.append("NAVER_CLIENT_ID/NAVER_CLIENT_SECRET missing. Offline blog post drafts generated instead.")
        signals = offline_signals()
        runtime_status = "API_BLOCKED_OFFLINE_REVENUE_ASSETS_GENERATED"
    else:
        print(f"CHEONOK_RUNTIME=START NAVER_CLIENT_ID={mask_secret(client_id)} PAPER_ONLY=TRUE")
        ok, api_status = naver_health_check(client_id, client_secret)
        if ok:
            signals, api_blockers = collect_naver_signals(client_id, client_secret, args.max_results)
            blockers.extend(api_blockers)
            if not signals:
                blockers.append("Naver API ready but no usable signals collected. Offline fallback added.")
                signals = offline_signals()
                runtime_status = "API_READY_WITH_OFFLINE_FALLBACK"
            else:
                runtime_status = "API_COLLECTION_SUCCESS"
        else:
            blockers.append(api_status)
            signals = offline_signals()
            runtime_status = "API_BLOCKED_OFFLINE_REVENUE_ASSETS_GENERATED"

    posts, posting_schedule = generate_assets(signals, site_url)
    output_dir = output_base / now_kst().strftime("%Y%m%d_%H%M%S")
    paths = write_outputs(output_dir, runtime_status, api_status, signals, blockers, posts, posting_schedule, site_url)

    print("CHEONOK_RUNTIME=COMPLETE")
    print(f"RUNTIME_STATUS={runtime_status}")
    print(f"NAVER_API_STATUS={api_status}")
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
    p = argparse.ArgumentParser(description="CHEONOK Blog Runtime Engine v1")
    p.add_argument("--root", default=".")
    p.add_argument("--max-results", type=int, default=5)
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
