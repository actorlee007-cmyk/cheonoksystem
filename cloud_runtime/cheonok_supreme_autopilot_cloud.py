import os
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
FINAL_GOAL_KRW = 100_000_000_000
MONTHLY_ATTACK_KRW = 1_000_000_000
ANNUAL_SCALE_KRW = 10_000_000_000

PRODUCTS = [
    ("무료진단", 0, "유입"),
    ("AI 운세·타로 미니 리포트", 9900, "저마찰 결제"),
    ("AI 인생/사업 방향 리포트", 49000, "저가 신뢰"),
    ("CEO 보고서 1회 제작", 99000, "신뢰 확보"),
    ("AI 매출 시스템 진단 프로젝트", 3000000, "고액 진입"),
    ("CHEONOK 매출 OS 구축 Lite", 10000000, "구축"),
    ("CHEONOK 매출 OS 구축 Pro", 30000000, "구축"),
    ("Enterprise AI Revenue OS", 100000000, "기업형")
]

COUNTRIES = ["AU", "US", "CA", "NZ", "CH", "DE", "NO", "GB", "NL", "JP"]


def won(n):
    return "₩" + f"{int(n):,}"


def env_int(name, default=0):
    try:
        return int(os.environ.get(name, str(default)) or default)
    except Exception:
        return default


def send_telegram(text):
    token = os.environ.get("CHEONOK_TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("CHEONOK_TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("HOLD_CONFIG_REQUIRED: Telegram secrets missing")
        print(text)
        return False
    for chunk_start in range(0, len(text), 3500):
        chunk = text[chunk_start:chunk_start + 3500]
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
        print("HOLD_N8N_WEBHOOK_MISSING")
        return False
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(webhook, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            print(res.read().decode("utf-8", errors="ignore"))
        return True
    except Exception as e:
        print(f"HOLD_N8N_POST_FAILED: {e}")
        return False


def build_report():
    now = datetime.now(KST)
    revenue = env_int("CHEONOK_MANUAL_REVENUE")
    leads = env_int("CHEONOK_MANUAL_LEADS")
    checkouts = env_int("CHEONOK_MANUAL_CHECKOUT")
    high_offers = env_int("CHEONOK_MANUAL_HIGH_TICKET")
    reverse_cases = env_int("CHEONOK_REVERSE_CASES")
    global_tests = env_int("CHEONOK_GLOBAL_TESTS")
    content_published = env_int("CHEONOK_CONTENT_PUBLISHED")

    monthly_gap = max(MONTHLY_ATTACK_KRW - revenue, 0)
    final_gap = max(FINAL_GOAL_KRW - revenue, 0)

    status = {
        "revenue": "CRITICAL" if revenue <= 0 else "PASS",
        "lead": "CRITICAL" if leads <= 0 else "PASS",
        "checkout": "CRITICAL" if checkouts <= 0 else "PASS",
        "high_ticket": "HOLD_TO_ACTION" if high_offers <= 0 else "PASS",
        "mission": "LOCKED_1000B"
    }

    product_lines = "\n".join([f"- {name}: {won(price)} / {role}" for name, price, role in PRODUCTS])
    country_lines = ", ".join(COUNTRIES)

    text = f"""📊 CHEONOK SUPREME AUTOPILOT OS 보고

보고시각: {now.strftime('%Y-%m-%d %H:%M:%S')} KST
운영위치: CLOUD / PC OFF SAFE
최종목표: 1000억 시스템

1. 현재 매출 상태
- 리드: {leads}
- 결제요청: {checkouts}
- 고액제안: {high_offers}
- 매출: {won(revenue)}
- 월 10억 부족분: {won(monthly_gap)}
- 1000억 부족분: {won(final_gap)}

2. 판정
- 매출: {status['revenue']}
- 리드: {status['lead']}
- 결제요청: {status['checkout']}
- 고액제안: {status['high_ticket']}
- 초목적: {status['mission']}
- 무단 자동결제/스팸: BLOCK
- HOLD: 안전 우회 실행

3. 상품 사다리
{product_lines}

4. 글로벌 10개국
- {country_lines}

5. 자율 실행 큐
- 돈 번 사례 역추적: {reverse_cases}
- 글로벌 테스트: {global_tests}
- 콘텐츠 발행: {content_published}

6. 다음 1시간 강제 목표
A. 저마찰 리드 10건 또는 결제요청 1건
B. 300만 원 AI 매출 시스템 진단 제안 1건
C. TikTok/Shorts/Reels 돈 번 사례 1개 역추적 후 상품·결제·콘텐츠로 변환

현재 시스템 상태:
자율 학습 및 PAPER 데이터 축적 상태."""

    payload = {
        "version": "CHEONOK_SUPREME_AUTOPILOT_CLOUD_001",
        "reported_at": now.isoformat(),
        "final_goal_krw": FINAL_GOAL_KRW,
        "monthly_attack_krw": MONTHLY_ATTACK_KRW,
        "metrics": {
            "leads": leads,
            "checkout_requests": checkouts,
            "high_ticket_offers": high_offers,
            "revenue": revenue,
            "monthly_gap": monthly_gap,
            "final_gap": final_gap,
            "reverse_cases": reverse_cases,
            "global_tests": global_tests,
            "content_published": content_published
        },
        "status": status,
        "report_text": text
    }
    return text, payload


if __name__ == "__main__":
    text, payload = build_report()
    send_telegram(text)
    post_n8n(payload)
