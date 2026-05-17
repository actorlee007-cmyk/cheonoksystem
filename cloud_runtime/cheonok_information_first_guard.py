import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "canon" / "CHEONOK_INFORMATION_FIRST_CONSTITUTION.json"
REPORT_DIR = ROOT / "_reports"
REPORT_DIR.mkdir(exist_ok=True)

BLOCKED_PATTERNS = [
    "직접 확인해주세요",
    "파일을 열어보세요",
    "직접 찾아보세요",
    "명령어를 계속 입력하세요",
    "대표님이 판단하세요",
    "수동으로 계속 처리하세요",
    "월 500만 원 부족분",
    "일 목표 부족분 ₩167,000"
]

REQUIRED_SIGNALS = [
    "1000억 시스템",
    "월 10억",
    "SUPREME MASTER OS",
    "BLOCK_LEGACY",
    "자율 학습 및 PAPER 데이터 축적 상태"
]


def load_canon():
    if CANON.exists():
        return json.loads(CANON.read_text(encoding="utf-8"))
    return {"version": "MISSING_CANON", "non_regression_rules": []}


def scan_text(text):
    violations = []
    for p in BLOCKED_PATTERNS:
        if p in text:
            violations.append({"type": "BLOCKED_PATTERN", "pattern": p})
    missing = [s for s in REQUIRED_SIGNALS if s not in text]
    return violations, missing


def classify_task(task):
    task_l = task.lower()
    if any(x in task_l for x in ["token", "secret", "password", "결제 계정", "인증", "bot_token", "chat_id"]):
        return "SECRET_OR_AUTH_EXCEPTION"
    if any(x in task_l for x in ["deploy", "github", "vercel", "api", "report", "telegram", "n8n", "homepage", "lead"]):
        return "SYSTEM_EXECUTE_FIRST"
    return "INFO_FILTER_FIRST"


def build_execution_filter(task):
    canon = load_canon()
    classification = classify_task(task)
    now = datetime.now(KST).isoformat()
    return {
        "version": "CHEONOK_INFORMATION_FIRST_GUARD_001",
        "checked_at": now,
        "task": task,
        "classification": classification,
        "decision": {
            "first": "READ_EXISTING_INFO_AND_CANON",
            "second": "PASS_HOLD_BLOCK",
            "third": "SYSTEM_EXECUTE_AVAILABLE_ACTIONS",
            "fourth": "ASK_ONLY_SECRET_OR_APPROVAL_IF_ABSOLUTELY_NEEDED"
        },
        "user_manual_work": "BLOCK_EXCEPT_SECRET_OR_AUTH",
        "canon_version": canon.get("version"),
        "final_goal": canon.get("final_goal", "1000억 시스템"),
        "monthly_attack_metric": canon.get("monthly_attack_metric", "월 10억"),
        "status": "READY"
    }


def main():
    task = " ".join(os.sys.argv[1:]).strip() or "CHEONOK master operation"
    result = build_execution_filter(task)
    out = REPORT_DIR / "latest_information_first_guard.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
