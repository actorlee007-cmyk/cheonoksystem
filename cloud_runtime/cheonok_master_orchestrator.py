import os
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
FINAL_GOAL_KRW = 100_000_000_000
MONTHLY_ATTACK_KRW = 1_000_000_000
DEFAULT_BASE_URL = "https://cheonoksystem.com"

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
        headers = {"User-Agent": "CHEONOK-MASTER-ORCHESTRATOR/001"}
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
        "source": "master_orchestrator_smoke_test",
        "type": "system_probe",
        "product": "CHEONOK Supreme Master OS",
        "price": 0,
        "country": "KR",
        "question": "MASTER_ORCHESTRATOR_SMOKE_TEST: 1000억 시스템 / 월 10억 중간 지표 / legacy blocked / API lead bridge check"
    }


def run():
    now = datetime.now(KST)
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

    n8n_result = post_n8n({
        "version": "CHEONOK_MASTER_ORCHESTRATOR_001",
        "reported_at": now.isoformat(),
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
    })

    monthly_gap = max(MONTHLY_ATTACK_KRW - revenue, 0)
    final_gap = max(FINAL_GOAL_KRW - revenue, 0)

    def passhold(ok):
        return "PASS" if ok else "HOLD"

    report = f"""📊 CHEONOK SUPREME MASTER OS 보고

보고시각: {now.strftime('%Y-%m-%d %H:%M:%S')} KST
운영방식: MASTER ORCHESTRATOR / 분산 단계 통합
최종목표: 1000억 시스템
중간 공격 지표: 월 10억

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

4. 실행 큐
A. 저마찰 리드 10건 또는 결제요청 1건
B. 300만 원 AI 매출 시스템 진단 제안 1건
C. TikTok/Shorts/Reels 돈 번 사례 1개 역추적
D. 고단가 10개국 소재 생성
E. 결제 링크/수동 결제 브릿지 연결

5. 정본
쪼개진 단계는 내부 구현 단위일 뿐이다. 외부 운영 기준은 SUPREME MASTER OS 단일 원소스다.

현재 시스템 상태:
자율 학습 및 PAPER 데이터 축적 상태."""

    sent = send_telegram(report)
    print(json.dumps({
        "version": "CHEONOK_MASTER_ORCHESTRATOR_001",
        "telegram_sent": sent,
        "n8n_result": n8n_result,
        "probes": probes
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    run()
