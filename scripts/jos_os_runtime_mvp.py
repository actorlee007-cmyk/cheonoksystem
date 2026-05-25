#!/usr/bin/env python3
"""JOS top-1-first canon ingestion runtime MVP.

Flow: scout external excellence -> extract essence -> map to JOS canon ->
organic council review -> Final Veto -> JSONL ledger.
"""
from __future__ import annotations

import argparse, json, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

KST = timezone(timedelta(hours=9))
BUSINESS_LINES = {
    "paper": "PAPER_CAPITAL_INTELLIGENCE",
    "market": "PAPER_CAPITAL_INTELLIGENCE",
    "주식": "PAPER_CAPITAL_INTELLIGENCE",
    "youtube": "YOUTUBE_CHANNEL_OPERATION",
    "ranking": "YOUTUBE_CHANNEL_OPERATION",
    "유튜브": "YOUTUBE_CHANNEL_OPERATION",
    "랭킹": "YOUTUBE_CHANNEL_OPERATION",
    "automation": "AI_AUTOMATION_SYSTEM_SALES",
    "ai": "AI_AUTOMATION_SYSTEM_SALES",
    "자동화": "AI_AUTOMATION_SYSTEM_SALES",
    "affiliate": "ADSENSE_AFFILIATE_REVENUE",
    "adsense": "ADSENSE_AFFILIATE_REVENUE",
    "광고": "ADSENSE_AFFILIATE_REVENUE",
    "어필": "ADSENSE_AFFILIATE_REVENUE",
    "subscription": "WEB_SUBSCRIPTION_SERVICE",
    "member": "WEB_SUBSCRIPTION_SERVICE",
    "구독": "WEB_SUBSCRIPTION_SERVICE",
}
LEDGER_BY_LINE = {
    "PAPER_CAPITAL_INTELLIGENCE": ["PAPER_SIGNALS", "REPORTS"],
    "YOUTUBE_CHANNEL_OPERATION": ["CONTENT_ASSETS", "TASK_QUEUE"],
    "AI_AUTOMATION_SYSTEM_SALES": ["TASK_QUEUE", "REPORTS"],
    "ADSENSE_AFFILIATE_REVENUE": ["CONTENT_ASSETS", "METRICS_DAILY"],
    "WEB_SUBSCRIPTION_SERVICE": ["REPORTS", "METRICS_DAILY"],
}
VETO_TERMS = {
    "market_execution": "Market execution path is blocked.",
    "broker_execution_gate": "Broker execution gate is blocked.",
    "capital_expansion": "Capital expansion is blocked.",
    "unverified performance claim": "Unverified performance claim is blocked.",
    "sensitive data": "Sensitive data exposure is blocked.",
    "core_patch_without_review": "Unreviewed core patch is blocked.",
}
CANON_LAYERS = [
    "GLOBAL_FIRST",
    "KOREA_THEME_TRANSLATION",
    "REAL_DATA_BRIDGE",
    "SUBSCRIPTION_REPORT",
    "CEO_REPORT_BOOK",
    "GOD_HYBRID_MIND_ENGINE",
    "ESSENCE_COLLISION_TRANSCEND_MEMORY",
    "AUTO_REVIEW_PATCH_COUNCIL",
    "FINAL_VETO",
    "NON_REGRESSION_MEMORY",
]


def now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def unique(items):
    return list(dict.fromkeys(items))


def extract_essence(case: dict) -> dict:
    text = (case.get("title", "") + " " + case.get("observed_pattern", "")).lower()
    if "ranking" in text or "랭킹" in text:
        return {
            "why_it_works": "Compresses many options into fast judgment.",
            "reusable_mechanism": "Ranking engine -> script -> affiliate/subscription/report funnel.",
            "user_pain": "Users do not want to manually research everything.",
        }
    if "affiliate" in text or "어필" in text or "adsense" in text:
        return {
            "why_it_works": "Turns purchase-intent content into tracked revenue.",
            "reusable_mechanism": "Content asset -> offer mapping -> revenue attribution ledger.",
            "user_pain": "Users need pre-purchase filtering and trust.",
        }
    if "automation" in text or "ai" in text or "자동화" in text:
        return {
            "why_it_works": "Reduces repeated operator work and decision fatigue.",
            "reusable_mechanism": "Diagnosis -> proposal -> delivery -> monthly operating report.",
            "user_pain": "Operators lose time to repeated coordination and reporting.",
        }
    return {
        "why_it_works": "Potentially reusable top-1 pattern.",
        "reusable_mechanism": "Scout -> essence -> canon mapping -> patch council.",
        "user_pain": "Needs mapping evidence.",
    }


def map_to_canon(case: dict, essence: dict) -> dict:
    text = " ".join([case.get("title", ""), case.get("source_type", ""), case.get("observed_pattern", ""), " ".join(case.get("tags", []))]).lower()
    lines = unique(line for key, line in BUSINESS_LINES.items() if key in text)
    ledgers = ["EVIDENCE", "PATCH_COUNCIL"]
    for line in lines:
        ledgers.extend(LEDGER_BY_LINE.get(line, []))
    conflicts = []
    if not lines:
        conflicts.append("No clear routing to the five business lines.")
    if "copy" in text or "clone" in text or "그대로" in text:
        conflicts.append("Needs JOS essence translation before adoption.")
    return {
        "business_lines": lines,
        "canon_layers": CANON_LAYERS,
        "ledgers": unique(ledgers),
        "strengths": [essence["reusable_mechanism"]],
        "conflicts": conflicts,
    }


def final_veto(case: dict) -> list[str]:
    text = " ".join([case.get("title", ""), case.get("observed_pattern", ""), " ".join(case.get("risks", [])), " ".join(case.get("tags", []))]).lower()
    return unique(reason for term, reason in VETO_TERMS.items() if term in text)


def council_loop(case: dict, mapping: dict) -> list[dict]:
    lines = ", ".join(mapping["business_lines"]) or "UNMAPPED"
    conflicts = "; ".join(mapping["conflicts"]) or "No hard conflict detected."
    return [
        {"agent": "ProblemSolver", "q": "What is being upgraded?", "a": case.get("title", "")},
        {"agent": "EssenceExtractor", "q": "Why does it work?", "a": extract_essence(case)["why_it_works"]},
        {"agent": "CanonMapper", "q": "Which business line is strengthened?", "a": lines},
        {"agent": "ConflictDetector", "q": "What conflict exists?", "a": conflicts},
        {"agent": "ProgrammerCouncil", "q": "Smallest safe patch?", "a": "Ledger-backed task before production automation."},
        {"agent": "EvidenceAgent", "q": "What evidence is required?", "a": "Source, mapping, output artifact, ledger row, veto result."},
    ]


def decide(case: dict) -> dict:
    essence = extract_essence(case)
    mapping = map_to_canon(case, essence)
    veto = final_veto(case)
    if veto:
        decision = "BLOCK"
    elif mapping["conflicts"] and not mapping["business_lines"]:
        decision = "HOLD"
    elif mapping["conflicts"]:
        decision = "PATCH_CANDIDATE"
    elif not case.get("proof_hint"):
        decision = "HOLD"
    else:
        decision = "PATCH_CANDIDATE"
    return {
        "run_id": "jos-" + uuid4().hex[:12],
        "date_kst": now_kst(),
        "title": case.get("title"),
        "decision": decision,
        "summary": f"Top-1 case first; JOS canon absorption result: {decision}.",
        "essence": essence,
        "mapping": mapping,
        "veto_reasons": veto,
        "council_loop": council_loop(case, mapping),
        "next_actions": next_actions(decision),
    }


def next_actions(decision: str) -> list[str]:
    if decision == "BLOCK":
        return ["Write BLOCKED_LOG and do not implement."]
    if decision == "HOLD":
        return ["Collect evidence and clarify business-line routing."]
    return ["Create TASK_QUEUE item.", "Create output artifact.", "Re-run Final Veto with implementation evidence."]


def write_ledger(root: Path, result: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in [result["decision"].lower(), "evidence"]:
        with (root / f"{name}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")


def demo_cases() -> list[dict]:
    return [
        {"title": "Ranking-style YouTube affiliate channel", "source_type": "youtube", "observed_pattern": "Ranking videos compress choices and route users to affiliate/subscription CTAs.", "proof_hint": "CEO observation; source URL to attach.", "tags": ["youtube", "ranking", "affiliate", "subscription"]},
        {"title": "AI automation retainer model", "source_type": "business", "observed_pattern": "AI automation diagnosis leads to build projects and monthly operator retainers.", "proof_hint": "Market pattern; source examples needed.", "tags": ["ai", "automation", "b2b", "subscription"]},
        {"title": "Unsafe market signal offer", "source_type": "blocked", "observed_pattern": "Promotes market_execution and unverified performance claim.", "risks": ["market_execution", "unverified performance claim"], "tags": ["paper"]},
    ]


def run(cases: list[dict], ledger_root: Path) -> list[dict]:
    results = [decide(case) for case in cases]
    for result in results:
        write_ledger(ledger_root, result)
    return results


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        results = run(demo_cases(), Path(tmp))
        assert results[0]["decision"] == "PATCH_CANDIDATE"
        assert "YOUTUBE_CHANNEL_OPERATION" in results[0]["mapping"]["business_lines"]
        assert "ADSENSE_AFFILIATE_REVENUE" in results[0]["mapping"]["business_lines"]
        assert results[1]["decision"] == "PATCH_CANDIDATE"
        assert "AI_AUTOMATION_SYSTEM_SALES" in results[1]["mapping"]["business_lines"]
        assert results[2]["decision"] == "BLOCK"
        assert results[2]["veto_reasons"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger-root", default="runtime/ledgers")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("SELF_TEST_PASS")
        return 0
    print(json.dumps(run(demo_cases(), Path(args.ledger_root)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
