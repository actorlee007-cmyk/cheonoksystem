# -*- coding: utf-8 -*-
"""
CHEONOK Next Action Engine v0.1
-------------------------------
Purpose:
- Remove user confusion after analysis.
- Read latest Social Signal outputs.
- Generate a simple 'what to do next' report.

Rule:
- User should not hunt files or decide from scratch.
- System proposes next action first.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "social_signal_scout"
OUT = DATA / "next_actions"
OUT.mkdir(parents=True, exist_ok=True)


def read_text(path: Path, limit: int = 50000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def latest_files(name: str, limit: int = 10):
    files = list(DATA.rglob(name))
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


def detect_category(text: str) -> str:
    low = text.lower()
    if "ai_agent_runtime" in low or "ai 에이전트" in low or "claude code" in low or "작은 팀" in low:
        return "AI_AGENT_RUNTIME"
    if "proven_system_reverse" in low or "성공 시스템" in low or "2등" in low or "3등" in low:
        return "PROVEN_SYSTEM_REVERSE"
    if "pain_to_product" in low or "불편함" in low or "행동 수" in low:
        return "PAIN_TO_PRODUCT"
    if "faceless" in low or "얼굴 없이" in low or "유튜브 자동화" in low:
        return "FACELESS_CONTENT_ENGINE"
    if "github" in low or "open source" in low or "도구" in low:
        return "TOOL_DISCOVERY"
    return "GENERAL"


def extract_verdict(text: str) -> str:
    if "block" in text.lower():
        return "BLOCK/HOLD CHECK"
    if "pass" in text.lower():
        return "PASS"
    if "hold" in text.lower():
        return "HOLD"
    return "UNCLASSIFIED"


def action_set(category: str):
    if category == "AI_AGENT_RUNTIME":
        return {
            "primary": "CHEONOK Runtime Architecture 문서에 AI Agent Work Loop 섹션 추가",
            "secondary": [
                "Claude Code / Cursor / AI Agent 사례 5개 추가 수집",
                "작업 지시-검증-롤백-보고 루프를 도식화",
                "현재 도구 중 반복 수동 단계 1개를 자동화 후보로 지정",
            ],
            "product": "작은 팀을 위한 AI Runtime 진단 리포트",
        }
    if category == "PROVEN_SYSTEM_REVERSE":
        return {
            "primary": "성공한 유사 서비스 10개를 찾아 불편함·가격·유입·결제 구조 분해",
            "secondary": [
                "겉모습 복제 금지 / 구조 복제 허용 기준 문서화",
                "2등·3등 진입 후보 3개 선정",
                "가장 작은 MVP 1개 설계",
            ],
            "product": "성공 시스템 역추적 리포트",
        }
    if category == "PAIN_TO_PRODUCT":
        return {
            "primary": "불편함 점수표 작성: 빈도×대중성×긴급성÷행동 수",
            "secondary": [
                "사용자가 반복하는 행동 수 측정",
                "1클릭/공유 1회로 줄일 수 있는 지점 찾기",
                "구독자가 돈 낼 만한 해결 문장 3개 작성",
            ],
            "product": "불편함 해소 상품화 진단",
        }
    if category == "FACELESS_CONTENT_ENGINE":
        return {
            "primary": "얼굴 없는 콘텐츠 운영 루프를 무료진단 CTA와 연결",
            "secondary": [
                "유사 쇼츠 5개 추가 수집",
                "니치/포맷/후킹 문장 반복 패턴 추출",
                "쇼츠 대본 3개를 홈페이지/구독 유입에 연결",
            ],
            "product": "얼굴 없는 콘텐츠 자산화 리포트",
        }
    return {
        "primary": "신호를 Social Signal DB에 저장하고 유사 신호 3개 추가 수집",
        "secondary": [
            "PASS/HOLD/BLOCK 재검토",
            "홈페이지 문구 후보 1개 작성",
            "구독자에게 줄 다음 행동 3개 정리",
        ],
        "product": "소셜 신호 요약 리포트",
    }


def main():
    files = latest_files("content_ideas.md", 10)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for f in files:
        text = read_text(f)
        category = detect_category(text)
        verdict = extract_verdict(text)
        actions = action_set(category)
        title = ""
        m = re.search(r"- title:\s*(.+)", text)
        if m:
            title = m.group(1).strip()
        rows.append({
            "file": str(f),
            "title": title or f.parent.name,
            "category": category,
            "verdict": verdict,
            "primary": actions["primary"],
            "product": actions["product"],
            "secondary": actions["secondary"],
        })

    md = ["# CHEONOK Next Action Report v0.1", "", f"생성시각: {now}", ""]
    md.append("## 1. 결론")
    md.append("")
    if rows:
        md.append(f"최신 분석 {len(rows)}개 기준, 다음에 할 일은 아래 순서로 진행한다.")
    else:
        md.append("아직 분석 결과가 없다. 먼저 CHEONOK_SOCIAL_INPUT 또는 TELEGRAM_INBOX로 링크를 넣는다.")
    md.append("")

    for i, r in enumerate(rows, 1):
        md.append(f"## {i}. {r['title']}")
        md.append(f"- Category: {r['category']}")
        md.append(f"- Verdict: {r['verdict']}")
        md.append(f"- Primary Next Action: {r['primary']}")
        md.append(f"- Product Angle: {r['product']}")
        md.append("- Secondary Actions:")
        for s in r["secondary"]:
            md.append(f"  - {s}")
        md.append(f"- Source: {r['file']}")
        md.append("")

    md.append("## 운영 원칙")
    md.append("")
    md.append("```text")
    md.append("구독자가 다음 행동을 고민하게 만들면 실패다.")
    md.append("시스템이 다음 행동을 먼저 제안하고, 사용자는 승인만 한다.")
    md.append("불편함 해소가 상품 가치다.")
    md.append("```")

    out_md = OUT / "latest_next_actions.md"
    out_md.write_text("\n".join(md), encoding="utf-8")

    out_csv = OUT / "latest_next_actions.csv"
    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["title", "category", "verdict", "primary", "product", "file"])
        for r in rows:
            w.writerow([r["title"], r["category"], r["verdict"], r["primary"], r["product"], r["file"]])

    print("CHEONOK Next Action Engine DONE")
    print("md:", out_md)
    print("csv:", out_csv)


if __name__ == "__main__":
    main()
