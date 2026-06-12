# CHEONOK Google Ads (SKAG) — 자동화 준비

출처: https://youtu.be/Gi50YPwbiVA (Claude Code + Google Ads SKAG 전략)

## 핵심 전략: SKAG (Single Keyword Ad Group)
검색어 = 광고 헤드라인 = 랜딩페이지 메시지를 1:1로 정렬. `campaigns/business_diagnosis_skag.json`에
첫 캠페인 기획(키워드, 헤드라인 15개, 설명 4개, 랜딩페이지 = cta-5m.html, 캠페인 설정 체크리스트)이 정리돼있음.

## 키워드 주의
JSON의 키워드는 초안(best-guess)임. 영상에서도 "AI 추측 키워드의 함정"을 경고함 -
실제 캠페인 생성 전, Google Ads 키워드 플래너로 검색량/CPC를 확인하고 교체할 것.

## 광고 송출 전 필요한 외부 설정 (사용자가 직접 - Claude Code가 대신 할 수 없음)
1. Google Ads 매니저 계정 생성
2. Google Ads API 개발자 토큰 신청 (승인까지 수일 소요 가능)
3. Google Cloud Console에서 OAuth 클라이언트 생성 (Ads API용)
4. 위 3개 완료 후 `google-ads` Python 라이브러리로 Claude Code <-> Google Ads 연동 가능

## 연동 후 자동화 범위
- `campaigns/*.json`의 캠페인 기획을 Google Ads API로 캠페인/광고그룹/광고 자동 생성
- `/api/lead`가 이미 받고 있는 payment_click / subscription_lead 이벤트를 전환으로 연결해 ROAS 추적

## 광고 예산
이 단계는 코드/기획만 - 실제 캠페인 집행(예산 입력)은 위 계정/토큰 세팅 후, 예산 규모를 별도로 정하고 진행.
