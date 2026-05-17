import os
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
FINAL_GOAL_KRW = 100_000_000_000
MONTHLY_ATTACK_KRW = 1_000_000_000
DEFAULT_BASE_URL = "https://cheonoksystem.com"
ROOT = Path(__file__).resolve().parents[1]
CANON_PATH = ROOT / "canon" / "CHEONOK_INFORMATION_FIRST_CONSTITUTION.json"
REPORT_DIR = ROOT / "_reports"
REPORT_DIR.mkdir(exist_ok=True)

PRODUCTS = [
    {"name": "무료진단", "price": 0, "role": "lead"},
    {"name": "AI 운세·타로 미니 리포트", "price": 9900, "role": "low_friction"},
    {"name": "AI 인생/사업 방향 리포트", "price": 49000, "role": "low_ticket"},
    {"name": "CEO 보고서 1회 제작", "price": 99000, "role": "trust"},
    {"name": "AI 매출 시스템 진단 프로젝트", "price": 3000000, "role": "high_ticket"},
    {"name": "CHEONOK 매출 OS 구축 Lite", "price": 10000000, "role": "build"},
    {"name": "CHEONOK 매출 OS 구축 Pro", "price": 30000000, "role": "build_pro"},
    {"name": "Enterprise AI Revenue OS", "price": 100000000, "role": "enterprise"}
]

COUNTRIES = ["AU", "US", "CA", "NZ", "CH", "DE", "NO", "GB", "NL", "JP"]

BLOCKED_REPORT_PATTERNS = [
    "월 500만 원 부족분",
    "일 목표 부족분",
    "무료진단 제안: 0",
    "CEO 보고서 판매: 0",
    "명령어를 계속 입력하세요",
    "직접 확인해주세요",
    "파일을 열어보세요",
    "대표님이 판단하세요"
]


def load_canon():
    if CANON_PATH.exists():
        try:
            return json.loads(CANON_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            return {"version": "CANON_READ_FAILED", "error": str(e)}
    return {"version": "CANON_MISSING"}


def information_first_gate(task_name="MASTER_ORCHESTRATOR"):
    canon = load_canon()
    return {
        "version": "INFO_FIRST_GATE_INLINE_001",
        "task": task_name,
        "canon_version": canon.get("version"),
        "operator_rule": "USER_SECRET_OR_APPROVAL_ONLY",
        "manual_delegation": "BLOCK_EXCEPT_SECRET_OR_AUTH",
        "decision_order": canon.get("decision_order", [
            "READ_EXISTING_INFO_AND_LOGS",
            "PASS_HOLD_BLOCK",
            "SYSTEM_EXECUTE_AVAILABLE_ACTIONS",
            "ASK_ONLY_SECRET_OR_APPROVAL_IF_ABSOLUTELY_NEEDED"
        ]),
        "final_goal": canon.get("final_goal", "1000억 시스템"),
        "monthly_attack_metric": canon.get("monthly_attack_metric", "월 10억")
    }


def validate_report(report):
    violations = [p for p in BLOCKED_REPORT_PATTERNS if p in report]
    required = ["1000억 시스템", "월 10억", "BLOCK_LEGACY", "자율 학습 및 PAPER 데이터 축적 상태"]
    missing = [r for r in required if r not in report]
    return {
        "ok": not violations and not missing,
        "violations": violations,
        "missing": missing,
        "status": "PASS_REPORT_CANON" if not violations and not missing else "BLOCK_REPORT_CANON_VIOLATION"
    }


def won(n):
    return "₩" + f"{int(n):,}"


def env_int(name, default=0):
    try:
        return int(os.environ.get(name, str(default)) or default)
    except Exception:
        return default


def http_json(url, method="GET", payload=None, timeout=30):
    try:
        data = None
        headers = {"User-Agent": "CHEONOK-MASTER-ORCHESTRATOR/INFO-FIRST"}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as res:
            text = res.read().decode("utf-8", errors="ignore")
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = {"raw": text[:500]}
            return {"ok": 200 <= res.status < 300, "status": res.status, "body": parsed}
    except Exception as e:
        return {"ok": False, "status": 0, "error": str(e)[:500]}


def send_telegram(text):
    token = os.environ.get("CHEONOK_TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("CHEONOK_TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("HOLD_TELEGRAM_SECRETS_MISSING")
        print(text)
        return False
    for i in range(0, len(text), 3500):
        chunk = text[i:i + 3500]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": "true"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=30) as res:
            print(res.read().decode("utf-8", errors="ignore"))
    return True


def post_n8n(payload):
    webhook = os.environ.get("N8N_WEBHOOK_URL", "").strip()
    if not webhook:
        return {"ok": False, "status": "HOLD_N8N_WEBHOOK_MISSING"}
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(webhook, data=data, method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as res:
            return {"ok": 200 <= res.status < 300, "status": res.status}
    except Exception as e:
        return {"ok": False, "status": "HOLD_N8N_POST_FAILED", "error": str(e)[:300]}


def build_lead_probe():
    return {
        "source": "master_orchestrator_info_first_probe",
        "type": "system_probe",
        "product": "CHEONOK Supreme Master OS",
        "price": 0,
        "country": "KR",
        "question": "INFO_FIRST_GATE_TEST: 1000억 시스템 / 월 10억 / legacy blocked / API lead bridge check"
    }


def run():
    now = datetime.now(KST)
    gate = information_first_gate()
    base_url = os.environ.get("CHEONOK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    revenue = env_int("CHEONOK_MANUAL_REVENUE")
    leads = env_int("CHEONOK_MANUAL_LEADS")
    checkout = env_int("CHEONOK_MANUAL_CHECKOUT")
    high_ticket = env_int("CHEONOK_MANUAL_HIGH_TICKET")
    reverse_cases = env_int("CHEONOK_REVERSE_CASES")
    global_tests = env_int("CHEONOK_GLOBAL_TESTS")
    content_published = env_int("CHEONOK_CONTENT_PUBLISHED")

    probes = {
        "home": http_json(base_url, "GET"),
        "os_status": http_json(f"{base_url}/api/os_status", "GET"),
        "lead_api": http_json(f"{base_url}/api/lead", "POST", build_lead_probe())
    }

    n8n_payload = {
        "version": "CHEONOK_MASTER_ORCHESTRATOR_INFO_FIRST_002",
        "reported_at": now.isoformat(),
        "information_first_gate": gate,
        "final_goal_krw": FINAL_GOAL_KRW,
        "monthly_attack_krw": MONTHLY_ATTACK_KRW,
        "metrics": {
            "revenue": revenue,
            "leads": leads,
            "checkout_requests": checkout,
            "high_ticket_offers": high_ticket,
            "reverse_cases": reverse_cases,
            "global_tests": global_tests,
            "content_published": content_published
        },
        "probes": probes,
        "products": PRODUCTS,
        "countries": COUNTRIES
    }
    n8n_result = post_n8n(n8n_payload)

    monthly_gap = max(MONTHLY_ATTACK_KRW - revenue, 0)
    final_gap = max(FINAL_GOAL_KRW - revenue, 0)

    def passhold(ok):
        return "PASS" if ok else "HOLD"

    report = f"""📊 CHEONOK SUPREME MASTER OS 보고

보고시각: {now.strftime('%Y-%m-%d %H:%M:%S')} KST
운영방식: INFORMATION-FIRST MASTER ORCHESTRATOR
최종목표: 1000억 시스템
중간 공격 지표: 월 10억

0. 정보 우선 가드
- 정본 버전: {gate.get('canon_version')}
- 사용자 수동 위임: BLOCK_EXCEPT_SECRET_OR_AUTH
- 사용자 역할: CEO / 승인 / 보안값 제공 한정
- 시스템 역할: 조회 / 실행 / 검증 / 복구 / 보고

1. 시스템 상태
- 홈 배포: {passhold(probes['home'].get('ok'))} / HTTP {probes['home'].get('status')}
- OS 상태 API: {passhold(probes['os_status'].get('ok'))} / HTTP {probes['os_status'].get('status')}
- 리드 API: {passhold(probes['lead_api'].get('ok'))} / HTTP {probes['lead_api'].get('status')}
- n8n 전달: {n8n_result.get('status')}

2. 매출 지표
- 리드: {leads}
- 결제요청: {checkout}
- 고액제안: {high_ticket}
- 매출: {won(revenue)}
- 월 10억 부족분: {won(monthly_gap)}
- 1000억 부족분: {won(final_gap)}

3. 판정
- 매출 0: {'CRITICAL' if revenue <= 0 else 'PASS'}
- 리드 0: {'CRITICAL' if leads <= 0 else 'PASS'}
- 결제요청 0: {'CRITICAL' if checkout <= 0 else 'PASS'}
- 고액제안 0: {'HOLD_TO_ACTION' if high_ticket <= 0 else 'PASS'}
- 구버전 500만 보고: BLOCK_LEGACY
- 무단 자동결제/스팸: BLOCK

4. 시스템 실행 큐
A. 시스템이 기존 정보/정본/로그를 먼저 조회한다.
B. 시스템이 가능한 조치는 직접 실행한다.
C. 사용자 요청은 보안값/계정 승인/최종 승인으로 제한한다.
D. JoCoding/TikTok/Shorts 도구를 상품·결제·보고 루프로 변환한다.
E. 고단가 10개국 소재와 고액 B2B 제안을 생성한다.

5. 정본
쪼개진 단계는 내부 구현 단위일 뿐이다. 외부 운영 기준은 SUPREME MASTER OS 단일 원소스다.

현재 시스템 상태:
자율 학습 및 PAPER 데이터 축적 상태."""

    report_validation = validate_report(report)
    result = {
        "version": "CHEONOK_MASTER_ORCHESTRATOR_INFO_FIRST_002",
        "telegram_sent": False,
        "n8n_result": n8n_result,
        "probes": probes,
        "information_first_gate": gate,
        "report_validation": report_validation
    }

    if report_validation["ok"]:
        result["telegram_sent"] = send_telegram(report)
    else:
        print("BLOCK_REPORT_CANON_VIOLATION")
        print(json.dumps(report_validation, ensure_ascii=False, indent=2))

    (REPORT_DIR / "latest_master_orchestrator_info_first.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "latest_master_orchestrator_info_first.txt").write_text(report, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    run()
