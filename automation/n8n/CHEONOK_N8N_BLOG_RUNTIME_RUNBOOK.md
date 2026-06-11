# CHEONOK n8n Blog Runtime Runbook

## Executive Purpose
This runtime converts CHEONOK build/operation activity and Naver search
signals into Naver Blog (애드포스트) and Tistory/Daum (애드센스) posting
drafts.

It does not store API secrets in GitHub. API keys must be stored only
inside n8n Credentials or n8n Variables.

## Source
This runtime implements two items from
`docs/JOS_NOTION_BOOKMARK_CLASSIFICATION_2026-06-11.md`:
- D3 "일기10개로 네이버광고승인" -> Naver Blog / 애드포스트 운영일지 라인
- C5 "Tistory365Blog AI자동화 블로그" -> Tistory / 애드센스 튜토리얼 라인

No income or approval is guaranteed. Only the structural principle
(consistent real-activity-based posting, SEO structure, CTA placement) is
adopted.

## n8n Variables
Create these inside n8n:

- NAVER_CLIENT_ID
- NAVER_CLIENT_SECRET
- CHEONOK_SITE_URL = https://cheonoksystem.com/cta-5m.html
- CHEONOK_MODE = PAPER_ONLY

`NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` come from
https://developers.naver.com (검색 Open API, 무료). If these are not set,
the runtime still runs and produces offline posting drafts
(`API_BLOCKED_OFFLINE_REVENUE_ASSETS_GENERATED`).

## First Workflow
Name: CHEONOK Blog Runtime

Core flow:
1. Schedule Trigger (e.g. daily)
2. Execute Command / Code node:
   `python3 automation/python_blog_runtime/cheonok_blog_runtime.py`
3. Read `content_queue.csv` from the latest `_RUNTIME_OUTPUTS/<timestamp>/`
4. Human review step (no auto-posting): operator copies the draft into
   Naver Blog / Tistory editor, adds screenshots/real details, and posts
5. Record posted URL back into the content queue / Google Sheet
6. Report: evidence, blocked items, next proof

## CASH CHAIN Mapping
Exposure:
- Naver Blog operations-journal posts
- Tistory automation-tutorial posts

Lead:
- CTA to cheonoksystem.com/cta-5m.html

Payment:
- 300,000 KRW AI Revenue Bottleneck Diagnosis (CTA route)

Subscription:
- AdPost / AdSense cumulative traffic asset
- JOS_MASTER paper-trading subscription report (recap niche)

Exit Ledger:
- content_queue.csv
- blog_intelligence.json
- posted-URL log (operator maintained)

## Risk Veto
- No income/approval guarantees in any post copy
- Operations-journal posts must reflect real work only
- Paper-trading recap posts must include "투자자문 아님" disclaimer and
  must not promise returns or recommend specific buys
- No mass/duplicate posting (저품질/스팸 정책 위반 방지)

## Next Proof
PASS only when at least one of these exists:
- successful runtime execution log (`CEO_REPORT.md`)
- Naver Search API response stored (`NAVER_API_STATUS=NAVER_API_READY`)
- a real published post URL (Naver Blog or Tistory)
- AdPost/AdSense approval or revenue evidence
- a free-diagnosis lead from a blog CTA

## Final Veto
LIVE_TRADE: BLOCKED
CAPITAL_SCALE: BLOCKED
KIS_ORDER_GATE: BLOCKED
PAPER_ONLY: TRUE
