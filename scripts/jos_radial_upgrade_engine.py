#!/usr/bin/env python3
"""JOS Radial Upgrade Engine MVP.

One input is treated as a seed. The engine expands it into essence,
business-line applications, tool chain, revenue loops, readiness gaps,
patch candidates, risk flags, council questions, and CEO report summary.
"""
from __future__ import annotations

import argparse, json
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))

BUSINESS_LINES = [
    "PAPER_CAPITAL_INTELLIGENCE",
    "YOUTUBE_CHANNEL_OPERATION",
    "AI_AUTOMATION_SYSTEM_SALES",
    "ADSENSE_AFFILIATE_REVENUE",
    "WEB_SUBSCRIPTION_SERVICE",
]

CANON_LAYERS = [
    "GLOBAL_FIRST",
    "KOREA_THEME_TRANSLATION",
    "REAL_DATA_BRIDGE",
    "THEME_CLUSTER",
    "LEADER_ROTATION",
    "PAPER_VALIDATION",
    "SUBSCRIPTION_REPORT",
    "CEO_REPORT_BOOK",
    "GOD_HYBRID_MIND_ENGINE",
    "ESSENCE_COLLISION_TRANSCEND_MEMORY",
    "AUTO_REVIEW_PATCH_COUNCIL",
    "FINAL_VETO",
    "NON_REGRESSION_MEMORY",
]

TOOL_EXPANSIONS = {
    "canva": {
        "essence": "Visual leverage: convert research and offers into fast-understood assets.",
        "tool_chain": ["Canva", "Airtable Content Calendar", "Google Drive Asset Archive", "Vercel Content Pages"],
        "applications": {
            "YOUTUBE_CHANNEL_OPERATION": ["thumbnail templates", "ranking video cards", "shorts cover system"],
            "AI_AUTOMATION_SYSTEM_SALES": ["proposal templates", "diagnostic report covers", "client before/after visuals"],
            "ADSENSE_AFFILIATE_REVENUE": ["affiliate comparison cards", "product ranking graphics"],
            "WEB_SUBSCRIPTION_SERVICE": ["paid report covers", "subscriber dashboard visuals"],
            "PAPER_CAPITAL_INTELLIGENCE": ["market report visuals", "theme heatmap cards"],
        },
        "readiness": ["Canva account", "brand kit", "reusable template folder", "content asset ledger"],
    },
    "figma": {
        "essence": "System design leverage: turn operating logic into reusable diagrams, UI, and design systems.",
        "tool_chain": ["Figma", "GitHub", "Vercel", "Canva"],
        "applications": {
            "YOUTUBE_CHANNEL_OPERATION": ["channel brand system", "visual explanation diagrams"],
            "AI_AUTOMATION_SYSTEM_SALES": ["client workflow diagrams", "automation architecture maps"],
            "WEB_SUBSCRIPTION_SERVICE": ["subscription portal UI", "report archive UI"],
            "PAPER_CAPITAL_INTELLIGENCE": ["PAPER engine diagram", "risk dashboard mockup"],
            "ADSENSE_AFFILIATE_REVENUE": ["comparison page wireframes"],
        },
        "readiness": ["Figma account", "design file", "design system library", "handoff rule"],
    },
    "airtable": {
        "essence": "Operational ledger leverage: turn scattered activity into queryable business memory.",
        "tool_chain": ["Airtable", "Gmail", "Stripe or PayPal", "Vercel API", "Daily CEO Report"],
        "applications": {
            "AI_AUTOMATION_SYSTEM_SALES": ["CRM", "lead status pipeline", "delivery ledger"],
            "YOUTUBE_CHANNEL_OPERATION": ["content calendar", "topic backlog", "asset tracker"],
            "ADSENSE_AFFILIATE_REVENUE": ["affiliate offer ledger", "conversion tracking table"],
            "WEB_SUBSCRIPTION_SERVICE": ["subscriber ledger MVP", "report access status"],
            "PAPER_CAPITAL_INTELLIGENCE": ["PAPER signal ledger", "simulation result log"],
        },
        "readiness": ["Airtable base", "tables", "field schema", "write permission", "backup/export rule"],
    },
    "stripe": {
        "essence": "Revenue verification leverage: make payments, subscriptions, customers, and invoices auditable.",
        "tool_chain": ["Stripe", "Vercel webhook", "Airtable or DB", "Gmail delivery", "CEO revenue report"],
        "applications": {
            "WEB_SUBSCRIPTION_SERVICE": ["subscription billing", "customer portal", "subscriber status"],
            "AI_AUTOMATION_SYSTEM_SALES": ["diagnostic payment", "project invoice", "retainer billing"],
            "ADSENSE_AFFILIATE_REVENUE": ["paid affiliate report upsell"],
            "YOUTUBE_CHANNEL_OPERATION": ["paid guide checkout"],
            "PAPER_CAPITAL_INTELLIGENCE": ["paid research report checkout with safety wording"],
        },
        "readiness": ["Stripe account", "products", "prices", "payment links", "webhook", "refund policy"],
    },
    "youtube": {
        "essence": "Attention leverage: convert top-1 patterns into repeatable discovery and trust assets.",
        "tool_chain": ["YouTube Data API", "Canva", "Airtable", "Vercel", "Affiliate Ledger"],
        "applications": {
            "YOUTUBE_CHANNEL_OPERATION": ["ranking format", "trend scan", "script system", "upload calendar"],
            "ADSENSE_AFFILIATE_REVENUE": ["affiliate CTA", "product comparison funnel"],
            "WEB_SUBSCRIPTION_SERVICE": ["free content to paid report funnel"],
            "AI_AUTOMATION_SYSTEM_SALES": ["case-study content to consultation funnel"],
            "PAPER_CAPITAL_INTELLIGENCE": ["market briefing channel with safety wording"],
        },
        "readiness": ["YouTube account", "channel positioning", "content calendar", "disclosure rules", "analytics access"],
    },
}

REVENUE_LOOPS = [
    "free lead magnet",
    "low-ticket report or template",
    "diagnostic product",
    "subscription product",
    "B2B automation project",
    "affiliate comparison page",
    "monthly retainer",
]

RISK_TERMS = [
    "unapproved execution", "performance guarantee", "secret key", "sensitive data", "copy exactly"
]


def now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def identify_seed(seed: str) -> str:
    text = seed.lower()
    for key in TOOL_EXPANSIONS:
        if key in text:
            return key
    if "유튜브" in text or "랭킹" in text:
        return "youtube"
    if "결제" in text or "구독" in text:
        return "stripe"
    if "원장" in text or "crm" in text:
        return "airtable"
    return "generic"


def generic_expansion(seed: str) -> dict:
    return {
        "essence": "Unclassified seed: expand through essence, canon, tools, revenue, readiness, and risk checks.",
        "tool_chain": ["GitHub", "Google Drive", "Airtable", "Vercel"],
        "applications": {line: ["derive concrete application from seed"] for line in BUSINESS_LINES},
        "readiness": ["source evidence", "business-line mapping", "tool readiness", "ledger destination"],
    }


def evaluate_risk(seed: str) -> list[str]:
    lower = seed.lower()
    return [term for term in RISK_TERMS if term.lower() in lower]


def council(seed: str, expansion: dict, risks: list[str]) -> list[dict]:
    return [
        {"role": "Top-1 Operator", "question": "What is the hidden leverage in this seed?", "answer": expansion["essence"]},
        {"role": "Programmer", "question": "What must become code or schema?", "answer": "Create or update scripts, ledgers, API routes, and runbooks after readiness checks."},
        {"role": "Problem Solver", "question": "What did the previous system miss?", "answer": "It treated the input linearly instead of expanding it radially."},
        {"role": "Revenue Architect", "question": "How can this become revenue?", "answer": ", ".join(REVENUE_LOOPS)},
        {"role": "Risk Reviewer", "question": "What must be controlled?", "answer": ", ".join(risks) if risks else "No hard risk detected in MVP pass."},
        {"role": "Evidence Auditor", "question": "What evidence is needed?", "answer": "source reference, ledger row, output artifact, code/runbook, readiness result"},
        {"role": "CEO Report Editor", "question": "How should this be summarized?", "answer": "Seed expanded into applications, tool chain, revenue loops, readiness gaps, and patch candidates."},
    ]


def expand(seed: str) -> dict:
    key = identify_seed(seed)
    expansion = TOOL_EXPANSIONS.get(key, generic_expansion(seed))
    risks = evaluate_risk(seed)
    decision = "BLOCK" if risks else "PATCH_REQUIRED"
    return {
        "date_kst": now_kst(),
        "seed": seed,
        "identified_pattern": key,
        "decision": decision,
        "essence": expansion["essence"],
        "top1_analog_pattern": "World-class operators turn one input into reusable workflows, assets, metrics, and revenue loops.",
        "canon_layers": CANON_LAYERS,
        "business_line_expansions": expansion["applications"],
        "tool_chain": expansion["tool_chain"],
        "revenue_loops": REVENUE_LOOPS,
        "readiness_gaps": expansion["readiness"],
        "patch_candidates": [
            "create reusable workflow template",
            "add ledger fields",
            "add readiness check",
            "connect tool output to CEO daily report",
            "record non-regression memory",
        ],
        "risk_flags": risks,
        "ledger_destinations": ["TOOL_REGISTRY", "TASK_QUEUE", "EVIDENCE", "PATCH_COUNCIL", "REPORT_LOG"],
        "council_questions": council(seed, expansion, risks),
        "ceo_report_summary": f"Input seed '{seed}' expanded into {len(expansion['applications'])} business-line routes, {len(expansion['tool_chain'])} tool-chain nodes, and {len(REVENUE_LOOPS)} revenue-loop candidates.",
    }


def write_ledger(payload: dict, root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "radial_upgrade.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def self_test() -> None:
    result = expand("Canva를 JOS 유튜브와 구독 시스템에 활용")
    assert result["identified_pattern"] == "canva"
    assert "YOUTUBE_CHANNEL_OPERATION" in result["business_line_expansions"]
    assert "WEB_SUBSCRIPTION_SERVICE" in result["business_line_expansions"]
    assert result["decision"] == "PATCH_REQUIRED"
    flagged = expand("secret key exposure")
    assert flagged["decision"] == "BLOCK"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", nargs="*", help="Input seed to expand")
    parser.add_argument("--ledger-root", default="runtime/ledgers")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("SELF_TEST_PASS")
        return 0
    seed = " ".join(args.seed).strip() or "Canva"
    payload = expand(seed)
    write_ledger(payload, Path(args.ledger_root))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
