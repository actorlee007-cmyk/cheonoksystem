import os
import re
import json
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
FINAL_GOAL = "1000억 시스템"
MONTHLY_ATTACK = "월 10억"
DEFAULT_CHANNEL = "https://www.youtube.com/@jocoding/videos"
OUT = Path("_channel_absorption")
OUT.mkdir(parents=True, exist_ok=True)

TOOL_RULES = [
    ("ai_builder", ["chatgpt", "gpt", "claude", "gemini", "llm", "openai", "ai", "인공지능", "챗gpt", "챗GPT"], "AI 직원/리포트/상담 자동화 엔진 후보"),
    ("automation", ["자동화", "automation", "workflow", "n8n", "zapier", "make", "bot", "봇"], "실행브릿지·리드처리·보고 자동화 후보"),
    ("web_app", ["웹", "사이트", "홈페이지", "react", "next", "vercel", "배포", "html", "javascript"], "홈페이지/결제창/리드 API 개선 후보"),
    ("data", ["데이터", "크롤", "스크래핑", "api", "db", "database", "supabase", "sheets", "google sheet"], "리드·시장·매출 데이터 저장/수집 후보"),
    ("content", ["유튜브", "쇼츠", "릴스", "틱톡", "콘텐츠", "영상", "썸네일"], "숏폼/광고/돈 번 사례 역추적 후보"),
    ("monetization", ["돈", "수익", "부업", "창업", "비즈니스", "매출", "판매", "구독"], "상품화·결제·업셀 후보"),
    ("education", ["강의", "코딩", "초보", "만들기", "따라", "노코드", "노 코드"], "구독자용 쉬운 온보딩/교육 상품 후보"),
    ("agent", ["agent", "에이전트", "직원", "자동", "자율"], "자율성장 OS/AI 직원 분업 후보"),
]

COUNTRIES = ["AU", "US", "CA", "NZ", "CH", "DE", "NO", "GB", "NL", "JP"]
PRODUCT_LADDER = [
    "무료진단",
    "AI 운세·타로 미니 리포트 9,900원",
    "AI 인생/사업 방향 리포트 49,000원",
    "CEO 보고서 99,000원",
    "AI 매출 시스템 진단 프로젝트 300만 원",
    "CHEONOK 매출 OS 구축 1,000만~3,000만 원",
    "Enterprise AI Revenue OS 1억 원+",
]


def now():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")


def run_cmd(args, timeout=180):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="ignore")
        return {"ok": p.returncode == 0, "stdout": p.stdout, "stderr": p.stderr, "code": p.returncode}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "code": -1}


def send_telegram(text):
    token = os.environ.get("CHEONOK_TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("CHEONOK_TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("HOLD_TELEGRAM_SECRETS_MISSING")
        print(text)
        return False
    for i in range(0, len(text), 3500):
        chunk = text[i:i+3500]
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": chunk, "disable_web_page_preview": "true"}).encode("utf-8")
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=30) as res:
            print(res.read().decode("utf-8", errors="ignore"))
    return True


def classify(title, description=""):
    text = (title + " " + description).lower()
    tags = []
    mappings = []
    for tag, keys, mapping in TOOL_RULES:
        if any(k.lower() in text for k in keys):
            tags.append(tag)
            mappings.append(mapping)
    if not tags:
        tags = ["watchlist"]
        mappings = ["추가 자막/설명 분석 후 매출 OS 패치 후보화"]
    return tags, mappings


def cheonok_transform(video):
    title = video.get("title") or ""
    desc = video.get("description") or ""
    tags, mappings = classify(title, desc)
    revenue_angle = []
    if "monetization" in tags or "content" in tags:
        revenue_angle.append("돈 번 사례 역추적 → CHEONOK 상품/결제/콘텐츠로 변환")
    if "web_app" in tags or "automation" in tags:
        revenue_angle.append("홈페이지·리드 API·보고 루프 자동화 패치 후보")
    if "ai_builder" in tags or "agent" in tags:
        revenue_angle.append("AI 직원/자율성장 엔진으로 흡수")
    if "education" in tags:
        revenue_angle.append("초보 친화 온보딩/구독 상품 콘텐츠로 변환")
    if not revenue_angle:
        revenue_angle.append("정본 필터 후 PASS/HOLD/BLOCK 판정")
    return {
        "title": title,
        "url": video.get("webpage_url") or video.get("url") or "",
        "id": video.get("id") or "",
        "duration": video.get("duration"),
        "view_count": video.get("view_count"),
        "tags": tags,
        "mappings": mappings,
        "revenue_angle": revenue_angle,
        "next_patch": [
            "도구/아이디어를 CHEONOK 실행브릿지에 붙일 수 있는지 확인",
            "저마찰 상품 또는 고액 B2B 상품으로 전환 가능성 평가",
            "10개국 언어/광고/결제/보고 루프에 넣을 소재 추출",
        ]
    }


def load_videos(channel_url, limit):
    cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings", channel_url]
    result = run_cmd(cmd, timeout=240)
    videos = []
    if result["ok"] and result["stdout"].strip():
        for line in result["stdout"].splitlines():
            if not line.strip():
                continue
            try:
                videos.append(json.loads(line))
            except Exception:
                pass
    return videos[:limit], result


def build_report(channel_url, transformed, fetch_result):
    top = transformed[:12]
    tag_counts = {}
    for v in transformed:
        for t in v["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    tag_line = ", ".join([f"{k}:{v}" for k, v in sorted(tag_counts.items(), key=lambda x: -x[1])]) or "없음"

    lines = []
    lines.append("📺 CHEONOK JO CODING CHANNEL ABSORPTION REPORT")
    lines.append("")
    lines.append(f"보고시각: {now()} KST")
    lines.append(f"채널: {channel_url}")
    lines.append(f"최종목표: {FINAL_GOAL}")
    lines.append(f"중간 공격 지표: {MONTHLY_ATTACK}")
    lines.append("")
    lines.append("1. 수집 상태")
    lines.append(f"- yt-dlp 수집: {'PASS' if fetch_result.get('ok') else 'HOLD'}")
    if not fetch_result.get("ok"):
        lines.append(f"- 오류: {fetch_result.get('stderr','')[:500]}")
    lines.append(f"- 분석 영상 수: {len(transformed)}")
    lines.append(f"- 태그 분포: {tag_line}")
    lines.append("")
    lines.append("2. CHEONOK 흡수 원칙")
    lines.append("- 영상은 참고자료가 아니라 도구/상품/자동화 패치 후보로 본다.")
    lines.append("- 코딩 도구는 홈페이지·API·리드·보고·결제·자동화에 붙인다.")
    lines.append("- AI/자동화/노코드/콘텐츠 도구는 저마찰 상품과 고액 B2B 상품 사다리에 연결한다.")
    lines.append("- 모든 결과는 1000억 시스템 단일 원소스로 보고한다.")
    lines.append("")
    lines.append("3. 우선 흡수 후보 TOP")
    for i, v in enumerate(top, 1):
        lines.append(f"{i}. {v['title']}")
        lines.append(f"   - 태그: {', '.join(v['tags'])}")
        lines.append(f"   - 접목: {' / '.join(v['revenue_angle'])}")
    lines.append("")
    lines.append("4. 다음 실행 큐")
    lines.append("A. AI/자동화 영상은 실행브릿지 패치 후보로 분류")
    lines.append("B. 웹앱/배포 영상은 홈페이지·API·Vercel 개선 후보로 분류")
    lines.append("C. 수익/부업/콘텐츠 영상은 Revenue Reverse Engine에 투입")
    lines.append("D. 초보 강의형 영상은 구독자 온보딩 상품으로 변환")
    lines.append("E. 상위 후보를 10개국 광고 소재/결제 페이지/리포트 템플릿으로 전환")
    lines.append("")
    lines.append("현재 시스템 상태:")
    lines.append("자율 학습 및 PAPER 데이터 축적 상태.")
    return "\n".join(lines)


def main():
    channel_url = os.environ.get("CHEONOK_CHANNEL_URL", DEFAULT_CHANNEL)
    limit = int(os.environ.get("CHEONOK_CHANNEL_LIMIT", "80") or 80)
    videos, fetch_result = load_videos(channel_url, limit)
    transformed = [cheonok_transform(v) for v in videos]

    (OUT / "jocoding_videos_raw.json").write_text(json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "jocoding_absorption_index.json").write_text(json.dumps(transformed, ensure_ascii=False, indent=2), encoding="utf-8")
    report = build_report(channel_url, transformed, fetch_result)
    (OUT / "jocoding_absorption_report.txt").write_text(report, encoding="utf-8")
    send_telegram(report)
    print(report)

if __name__ == "__main__":
    main()
