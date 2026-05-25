#!/usr/bin/env python3
"""JOS Tool Scout MVP.

Classifies available apps/connectors into JOS business lines and produces
PASS / TOOL_CANDIDATE / HOLD / BLOCK decisions before tool use.
"""
from __future__ import annotations

import argparse, json
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))

TOOLS = [
    {"name": "GitHub", "capabilities": ["code", "issues", "audit", "version_control"], "connected": True},
    {"name": "Google Drive", "capabilities": ["docs", "sheets", "slides", "reports", "archive"], "connected": True},
    {"name": "Gmail", "capabilities": ["email", "delivery", "support", "outreach"], "connected": True},
    {"name": "Airtable", "capabilities": ["crm", "ledger", "task_queue", "content_calendar"], "connected": True},
    {"name": "Stripe", "capabilities": ["payments", "subscriptions", "customers", "invoices"], "connected": True},
    {"name": "PayPal", "capabilities": ["invoices", "payments"], "connected": True},
    {"name": "Vercel", "capabilities": ["deploy", "web", "api", "domain"], "connected": True},
    {"name": "Canva", "capabilities": ["thumbnail", "social_asset", "proposal", "report_design"], "connected": True},
    {"name": "Figma", "capabilities": ["design_system", "diagram", "deck", "ui_mockup"], "connected": True},
    {"name": "Adalo", "capabilities": ["no_code_app", "mobile_app", "web_app", "database"], "connected": True},
    {"name": "Notion", "capabilities": ["knowledge_base", "notes", "workspace_search"], "connected": True},
    {"name": "Google Calendar", "capabilities": ["schedule", "availability", "meeting"], "connected": True},
]

BUSINESS_MAP = {
    "PAPER_CAPITAL_INTELLIGENCE": {"code", "audit", "docs", "sheets", "reports", "archive", "email", "web", "api"},
    "YOUTUBE_CHANNEL_OPERATION": {"thumbnail", "social_asset", "content_calendar", "docs", "archive", "design_system"},
    "AI_AUTOMATION_SYSTEM_SALES": {"crm", "task_queue", "payments", "invoices", "email", "proposal", "reports", "deploy", "web"},
    "ADSENSE_AFFILIATE_REVENUE": {"web", "domain", "thumbnail", "social_asset", "sheets", "ledger", "reports"},
    "WEB_SUBSCRIPTION_SERVICE": {"subscriptions", "customers", "payments", "web", "api", "crm", "ledger", "email"},
}

RISK_BY_CAPABILITY = {
    "payments": "payment_dispute_or_refund_risk",
    "subscriptions": "recurring_billing_compliance_risk",
    "email": "privacy_and_spam_risk",
    "crm": "personal_data_handling_risk",
    "web": "public_claim_and_compliance_risk",
    "api": "secret_management_risk",
}


def now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def classify(tool: dict) -> dict:
    caps = set(tool["capabilities"])
    mapped_lines = [line for line, needed in BUSINESS_MAP.items() if caps & needed]
    risks = sorted({RISK_BY_CAPABILITY[c] for c in caps if c in RISK_BY_CAPABILITY})

    if not tool.get("connected"):
        decision = "HOLD"
        reason = "Tool exists but connection/readiness is not verified."
    elif not mapped_lines:
        decision = "HOLD"
        reason = "No clear mapping to the five business lines."
    elif risks:
        decision = "TOOL_CANDIDATE"
        reason = "Useful but requires workflow and risk controls."
    else:
        decision = "PASS"
        reason = "Connected and directly useful with low immediate risk."

    return {
        "tool": tool["name"],
        "decision": decision,
        "reason": reason,
        "capabilities": tool["capabilities"],
        "business_lines": mapped_lines,
        "risks": risks,
        "next_actions": next_actions(tool["name"], decision, mapped_lines, risks),
    }


def next_actions(name: str, decision: str, lines: list[str], risks: list[str]) -> list[str]:
    if decision == "PASS":
        return [f"Register {name} in Tool Registry and route to {', '.join(lines)}."]
    if decision == "TOOL_CANDIDATE":
        return [
            f"Define workflow boundary for {name}.",
            "Add permission and evidence check.",
            "Add risk control before production use: " + ", ".join(risks),
        ]
    if decision == "HOLD":
        return [f"Verify account/permission and JOS workflow fit for {name}."]
    return [f"Do not use {name} until Final Veto clears it."]


def run() -> dict:
    results = [classify(tool) for tool in TOOLS]
    return {
        "date_kst": now_kst(),
        "summary": {
            "total": len(results),
            "pass": sum(1 for r in results if r["decision"] == "PASS"),
            "tool_candidate": sum(1 for r in results if r["decision"] == "TOOL_CANDIDATE"),
            "hold": sum(1 for r in results if r["decision"] == "HOLD"),
            "block": sum(1 for r in results if r["decision"] == "BLOCK"),
        },
        "results": results,
    }


def write_ledger(payload: dict, root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    target = root / "tool_registry.jsonl"
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return target


def self_test() -> None:
    result = run()
    names = {r["tool"] for r in result["results"]}
    assert "GitHub" in names
    assert "Airtable" in names
    assert "Stripe" in names
    assert result["summary"]["total"] >= 10
    assert any("WEB_SUBSCRIPTION_SERVICE" in r["business_lines"] for r in result["results"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger-root", default="runtime/ledgers")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("SELF_TEST_PASS")
        return 0
    payload = run()
    write_ledger(payload, Path(args.ledger_root))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
