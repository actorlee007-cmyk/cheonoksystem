#!/usr/bin/env python3
"""JOS readiness audit MVP.

Checks whether a claimed JOS business/system function has the minimum
cost model, account/access, ledger, payment, CRM, delivery, and evidence
requirements before it can be treated as executable.
"""
from __future__ import annotations

import argparse, json, os, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))

REQUIRED_COST_FIELDS = [
    "buy_fee_bps",
    "sell_fee_bps",
    "venue_fee_bps",
    "tax_bps",
    "spread_bps",
    "slippage_bps",
    "fx_cost_bps",
    "delay_penalty_bps",
    "partial_fill_assumption",
]

DEPENDENCIES = {
    "PAPER_CAPITAL_INTELLIGENCE": [
        "MARKET_DATA_ACCESS",
        "PAPER_LEDGER",
        "COST_MODEL",
        "SIMULATION_LEDGER",
        "BLOCKED_EXECUTION_GATE",
    ],
    "YOUTUBE_CHANNEL_OPERATION": [
        "YOUTUBE_ACCOUNT",
        "CONTENT_CALENDAR_LEDGER",
        "THUMBNAIL_TOOL_ACCESS",
        "DISCLOSURE_TEMPLATE",
    ],
    "AI_AUTOMATION_SYSTEM_SALES": [
        "LEAD_CAPTURE_PATH",
        "CRM_STORAGE",
        "PROPOSAL_TEMPLATE",
        "DELIVERY_LEDGER",
        "SUPPORT_CHANNEL",
    ],
    "ADSENSE_AFFILIATE_REVENUE": [
        "AFFILIATE_ACCOUNT",
        "TRACKING_LINK_POLICY",
        "DISCLOSURE_TEMPLATE",
        "CONVERSION_TRACKING",
    ],
    "WEB_SUBSCRIPTION_SERVICE": [
        "PRODUCTION_DOMAIN",
        "ANALYTICS",
        "PAYMENT_ACCOUNT",
        "PAYMENT_SUCCESS_RECORD",
        "SUBSCRIBER_LEDGER",
        "GATED_DELIVERY_PATH",
    ],
}

GLOBAL_DEPENDENCIES = [
    "OFFICIAL_DOMAIN",
    "OFFICIAL_EMAIL",
    "PRIVACY_POLICY",
    "TERMS_OF_SERVICE",
    "REFUND_POLICY",
    "ENV_INVENTORY",
    "ACCESS_OWNER_LEDGER",
]

ENV_HINTS = {
    "MARKET_DATA_ACCESS": ["MARKET_DATA_API_KEY", "DATA_VENDOR_API_KEY"],
    "YOUTUBE_ACCOUNT": ["YOUTUBE_CHANNEL_ID", "YOUTUBE_API_KEY"],
    "AFFILIATE_ACCOUNT": ["AFFILIATE_ACCOUNT_ID", "COUPANG_PARTNERS_ID"],
    "PAYMENT_ACCOUNT": ["STRIPE_SECRET_KEY", "PAYPAL_CLIENT_ID"],
    "CRM_STORAGE": ["AIRTABLE_API_KEY", "GOOGLE_SHEETS_ID", "CRM_BASE_ID"],
    "OFFICIAL_DOMAIN": ["OFFICIAL_DOMAIN"],
    "OFFICIAL_EMAIL": ["OFFICIAL_EMAIL"],
}


def now_kst() -> str:
    return datetime.now(KST).replace(microsecond=0).isoformat()


def load_json(path: str | None, default: dict) -> dict:
    if not path:
        return default
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return json.loads(p.read_text(encoding="utf-8"))


def env_present(names: list[str]) -> bool:
    return any(bool(os.environ.get(name)) for name in names)


def check_cost_model(cost_model: dict) -> dict:
    missing = [field for field in REQUIRED_COST_FIELDS if field not in cost_model]
    numeric_fields = [field for field in REQUIRED_COST_FIELDS if field.endswith("_bps")]
    invalid = [field for field in numeric_fields if field in cost_model and not isinstance(cost_model[field], (int, float))]
    status = "PASS" if not missing and not invalid else "BLOCK"
    return {"status": status, "missing": missing, "invalid": invalid}


def check_dependencies(readiness: dict, business_lines: list[str]) -> dict:
    declared = set(readiness.get("dependencies", []))
    required = set(GLOBAL_DEPENDENCIES)
    for line in business_lines:
        required.update(DEPENDENCIES.get(line, []))

    missing = sorted(required - declared)
    env_supported = []
    for dep in missing[:]:
        hints = ENV_HINTS.get(dep, [])
        if hints and env_present(hints):
            env_supported.append(dep)
            missing.remove(dep)

    return {
        "status": "PASS" if not missing else "HOLD",
        "required": sorted(required),
        "declared": sorted(declared),
        "env_supported": sorted(env_supported),
        "missing": missing,
    }


def council_questions(cost_check: dict, dep_check: dict, business_lines: list[str]) -> list[dict]:
    blocked_lines = business_lines if dep_check["missing"] else []
    return [
        {"agent": "CostModelAgent", "q": "Is the PAPER result net of realistic costs?", "a": cost_check["status"]},
        {"agent": "DependencyAgent", "q": "Which dependencies are missing?", "a": ", ".join(dep_check["missing"]) or "none"},
        {"agent": "BusinessLineAgent", "q": "Which business lines are blocked or held?", "a": ", ".join(blocked_lines) or "none"},
        {"agent": "ProgrammerCouncil", "q": "Smallest safe patch?", "a": "Create dependency ledger fields and fail readiness when required fields are missing."},
        {"agent": "EvidenceAgent", "q": "What proof is required?", "a": "Config file, env inventory, ledger row, webhook/CRM/write-path evidence."},
    ]


def audit(config: dict) -> dict:
    business_lines = config.get("business_lines", [])
    cost_check = check_cost_model(config.get("cost_model", {}))
    dep_check = check_dependencies(config.get("readiness", {}), business_lines)

    if cost_check["status"] == "BLOCK" and "PAPER_CAPITAL_INTELLIGENCE" in business_lines:
        decision = "BLOCK"
    elif dep_check["status"] != "PASS":
        decision = "HOLD"
    else:
        decision = "PASS"

    return {
        "date_kst": now_kst(),
        "decision": decision,
        "business_lines": business_lines,
        "cost_model_check": cost_check,
        "dependency_check": dep_check,
        "council_questions": council_questions(cost_check, dep_check, business_lines),
        "next_actions": next_actions(cost_check, dep_check),
    }


def next_actions(cost_check: dict, dep_check: dict) -> list[str]:
    actions = []
    if cost_check["missing"] or cost_check["invalid"]:
        actions.append("Add full fee/tax/spread/slippage cost model before PAPER validation claims.")
    for dep in dep_check["missing"]:
        actions.append(f"Resolve dependency: {dep}")
    if not actions:
        actions.append("Proceed to implementation patch with evidence logging.")
    return actions


def demo_config() -> dict:
    return {
        "business_lines": ["PAPER_CAPITAL_INTELLIGENCE", "YOUTUBE_CHANNEL_OPERATION", "WEB_SUBSCRIPTION_SERVICE"],
        "cost_model": {
            "buy_fee_bps": 1.5,
            "sell_fee_bps": 1.5,
            "venue_fee_bps": 0.5,
        },
        "readiness": {
            "dependencies": ["PAPER_LEDGER", "SIMULATION_LEDGER", "BLOCKED_EXECUTION_GATE", "CONTENT_CALENDAR_LEDGER"]
        },
    }


def self_test() -> None:
    result = audit(demo_config())
    assert result["decision"] == "BLOCK"
    assert "tax_bps" in result["cost_model_check"]["missing"]
    assert "YOUTUBE_ACCOUNT" in result["dependency_check"]["missing"]

    full = demo_config()
    full["cost_model"] = {k: 0 for k in REQUIRED_COST_FIELDS}
    full["cost_model"]["partial_fill_assumption"] = "paper model assumes no partial fill in first MVP"
    required = set(GLOBAL_DEPENDENCIES)
    for line in full["business_lines"]:
        required.update(DEPENDENCIES[line])
    full["readiness"] = {"dependencies": sorted(required)}
    result2 = audit(full)
    assert result2["decision"] == "PASS"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("SELF_TEST_PASS")
        return 0
    result = audit(load_json(args.config, demo_config()))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
