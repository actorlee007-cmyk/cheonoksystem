# -*- coding: utf-8 -*-
"""
CHEONOK Canon Decision Gate v0.1
--------------------------------
Purpose:
- Enforce CHEONOK canon before any report/product/system proposal is accepted.
- Filter outputs by friction removal, next-action presence, subscription usability, safety, and START_HERE integration.

This is not a generic analyzer.
It is a veto gate.

Core rule:
If the output creates confusion, manual file hunting, repeated commands, or no next action, it is HOLD/BLOCK.

Usage:
python tools/cheonok_canon_decision_gate.py "path/to/report.md"
python tools/cheonok_canon_decision_gate.py --latest

Output:
- data/canon_gate/latest_canon_gate_report.md
- data/canon_gate/latest_canon_gate_report.json
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "canon_gate"
SOCIAL = DATA / "social_signal_scout"
CHANNEL = DATA / "channel_learning"
OUT.mkdir(parents=True, exist_ok=True)


@dataclass
class GateResult:
    verdict: str
    score: int
    title: str
    source: str
    flags: list[str]
    missing: list[str]
    required_patches: list[str]
    next_actions: list[str]


def read_text(path: Path, limit: int = 100000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def latest_candidate() -> Path | None:
    names = ["content_ideas.md", "channel_intelligence_report.md", "latest_next_actions.md", "chatgpt_brief.txt"]
    files = []
    for base in [SOCIAL, CHANNEL, DATA]:
        if base.exists():
            for name in names:
                files.extend(base.rglob(name))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def has_any(text: str, keys: list[str]) -> bool:
    low = text.lower()
    return any(k.lower() in low for k in keys)


def count_action_friction(text: str) -> int:
    low = text.lower()
    friction_words = [
        "powershell", "명령어", "직접 실행", "파일을 열", "경로", "붙여넣", "ctrl+v",
        "복사", "다운로드", "설치", "다시 실행", "확인", "수동", "notepad",
        "copy", "paste", "manual", "command", "path", "open file",
    ]
    return sum(low.count(w.lower()) for w in friction_words)


def extract_title(text: str, fallback: str) -> str:
    patterns = [r"^- title:\s*(.+)$", r"^#\s+(.+)$", r"title\":\s*\"([^\"]+)\"", r"제목[:：]\s*(.+)"]
    for p in patterns:
        m = re.search(p, text, flags=re.M)
        if m:
            return m.group(1).strip()[:160]
    return fallback


def evaluate(path: Path) -> GateResult:
    text = read_text(path)
    low = text.lower()
    flags: list[str] = []
    missing: list[str] = []
    patches: list[str] = []
    next_actions: list[str] = []
    score = 100

    title = extract_title(text, path.parent.name)

    # 1. Friction removal gate
    friction_count = count_action_friction(text)
    if friction_count >= 8:
        flags.append("FRICTION_HIGH: manual commands/files/copy-paste steps appear too often")
        patches.append("Turn the workflow into CHEONOK_START_HERE menu or one-click launcher")
        score -= 25
    elif friction_count >= 3:
        flags.append("FRICTION_MEDIUM: manual steps detected")
        patches.append("Reduce manual steps to one purpose selection")
        score -= 12

    if has_any(text, ["powershell", "python tools", "파일을 열", "경로", "수동"]):
        flags.append("USER_BURDEN_DETECTED: output may push work back to user")
        patches.append("Replace command/path instructions with Start Here launcher path")
        score -= 15

    # 2. Next action gate
    if not has_any(text, ["다음 행동", "next action", "다음 실행", "primary next action", "실행 3개"]):
        missing.append("NEXT_ACTION_MISSING")
        patches.append("Add mandatory next action: primary + 3 secondary actions")
        score -= 25

    # 3. Pain to Product gate
    if not has_any(text, ["불편", "행동 수", "pain", "friction", "반복", "문제 해결"]):
        missing.append("PAIN_TO_PRODUCT_FILTER_MISSING")
        patches.append("Add pain/friction interpretation before product proposal")
        score -= 18

    # 4. Subscription usability gate
    if has_any(text, ["구독", "상품", "홈페이지", "광고", "결제"]):
        if not has_any(text, ["사용법", "무료진단", "cta", "결제", "온보딩", "처음", "샘플"]):
            missing.append("SUBSCRIPTION_ONBOARDING_MISSING")
            patches.append("Add onboarding: what user sends, what user receives, how payment/free diagnosis works")
            score -= 15

    # 5. Proven reverse / legal safety gate
    if has_any(text, ["복제", "성공한 시스템", "2등", "3등", "reverse"]):
        if not has_any(text, ["겉모습", "상표", "저작권", "구조", "block"]):
            missing.append("REVERSE_SAFETY_MISSING")
            patches.append("Add rule: copy structure only, never copy trademark/design/text")
            score -= 15

    # 6. Trading safety gate
    if has_any(text, ["주식", "매매", "투자", "증권", "trading"]):
        if not has_any(text, ["paper_only", "live_trade", "blocked", "실전 주문", "자본"]):
            missing.append("TRADING_SAFETY_MISSING")
            patches.append("Add PAPER_ONLY and blocked live trading gates")
            score -= 20

    # 7. Evidence quality gate
    if has_any(text, ["failed/none", "no transcript", "no subtitle", "전사 실패", "자막 실패"]):
        flags.append("EVIDENCE_LIMITATION_DETECTED")
        patches.append("Downgrade content-proof to HOLD when transcript/subtitle is missing")
        score -= 15

    # 8. START_HERE integration gate
    if has_any(text, ["도구", "모듈", "실행", "설치", "업데이트"]):
        if not has_any(text, ["cheonok_start_here", "start here", "원클릭", "목적 선택"]):
            missing.append("START_HERE_INTEGRATION_MISSING")
            patches.append("Add to CHEONOK_START_HERE and one-click setup")
            score -= 15

    # Build next actions from patches
    if patches:
        next_actions = [
            "Apply Canon Decision Gate patch before accepting this output",
            "Convert manual workflow into Start Here / one-click flow",
            "Regenerate report with pain, next action, subscription/onboarding, and safety sections",
        ]
    else:
        next_actions = [
            "Accept as canon-compatible report",
            "Store in Social/Channel/Subscription memory DB",
            "Use for homepage, product, or system patch candidate",
        ]

    if score >= 80 and not missing:
        verdict = "PASS"
    elif score >= 55:
        verdict = "HOLD_REWRITE_REQUIRED"
    else:
        verdict = "BLOCK_OR_MAJOR_REWRITE"

    return GateResult(
        verdict=verdict,
        score=max(0, score),
        title=title,
        source=str(path),
        flags=flags,
        missing=missing,
        required_patches=patches,
        next_actions=next_actions,
    )


def write_report(result: GateResult) -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = []
    md.append("# CHEONOK Canon Decision Gate Report v0.1")
    md.append("")
    md.append(f"생성시각: {now}")
    md.append(f"Source: {result.source}")
    md.append("")
    md.append("## 1. 최종 판정")
    md.append("")
    md.append("```text")
    md.append(f"VERDICT: {result.verdict}")
    md.append(f"SCORE: {result.score}/100")
    md.append("```")
    md.append("")
    md.append("## 2. 제목")
    md.append("")
    md.append(result.title)
    md.append("")
    md.append("## 3. 감지된 문제")
    md.append("")
    if result.flags:
        for x in result.flags:
            md.append(f"- {x}")
    else:
        md.append("- 없음")
    md.append("")
    md.append("## 4. 누락된 정본 필터")
    md.append("")
    if result.missing:
        for x in result.missing:
            md.append(f"- {x}")
    else:
        md.append("- 없음")
    md.append("")
    md.append("## 5. 필수 패치")
    md.append("")
    if result.required_patches:
        for i, x in enumerate(result.required_patches, 1):
            md.append(f"{i}. {x}")
    else:
        md.append("- 패치 필요 없음")
    md.append("")
    md.append("## 6. 다음 행동")
    md.append("")
    for i, x in enumerate(result.next_actions, 1):
        md.append(f"{i}. {x}")
    md.append("")
    md.append("## 7. 정본 기준")
    md.append("")
    md.append("```text")
    md.append("불편함을 줄이지 못하면 HOLD.")
    md.append("다음 행동이 없으면 HOLD.")
    md.append("사용자가 경로/파일/명령어를 찾게 만들면 HOLD.")
    md.append("구독자가 처음 10초 안에 사용법을 이해하지 못하면 HOLD.")
    md.append("실전 주문·자본 확대·자동 주문은 BLOCK.")
    md.append("원클릭/Start Here/공유 1회로 끝나면 PASS.")
    md.append("```")

    out_md = OUT / "latest_canon_gate_report.md"
    out_json = OUT / "latest_canon_gate_report.json"
    out_md.write_text("\n".join(md), encoding="utf-8")
    out_json.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    return out_md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="")
    ap.add_argument("--latest", action="store_true")
    args = ap.parse_args()

    if args.latest or not args.path:
        path = latest_candidate()
        if not path:
            raise SystemExit("NO_REPORT_FOUND")
    else:
        path = Path(args.path).resolve()

    result = evaluate(path)
    out = write_report(result)
    print("CHEONOK Canon Decision Gate DONE")
    print("verdict:", result.verdict)
    print("score:", result.score)
    print("report:", out)


if __name__ == "__main__":
    main()
