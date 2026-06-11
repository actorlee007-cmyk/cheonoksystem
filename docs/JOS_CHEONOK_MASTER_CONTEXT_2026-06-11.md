# JOS/CHEONOK MASTER CONTEXT - 2026-06-11 (정본 동기화 리포트)

이 문서는 CEO가 다른 AI 세션(클라우드 이관용)에 제공한 "JOS/CHEONOK MASTER
CONTEXT" + "[프롬프트용 복사 요약본]"을, 이 저장소(`actorlee007-cmyk/cheonoksystem`,
정본)의 실제 코드/원장 증거와 대조(NR_014 정본 궤도 이탈 자가 검열)한 결과다.

철학·안전수칙·20 Core Layers·Five Agents·Final Veto는 이미
`docs/JOS_CHEONOK_MASTER_SYSTEM_v1.md`가 정본이므로 이 문서에서 반복하지
않는다. 이 문서는 **"로컬 C:\JOS_OS 현재 상태" vs "클라우드 정본 현재 상태"**
의 차이와, 향후 클라우드 AI에게 줄 컨텍스트는 어느 쪽을 기준으로 해야 하는지를
정리한다.

## 1. 최종 판정

**로컬 `C:\JOS_OS`에서 보고된 "현재 상태"(JOS_RECOVER_SIM_E.py / E:\JOS_DATA\sim.db
/ random stub / KIS TOKEN FAIL·EGW00002)는 정본이 아니다.** 정본 PAPER 엔진은
이미 이 저장소 `automation/python_paper_capital_runtime/JOS_MASTER.py`로
존재하며, GitHub Actions로 평일 매시간 **실제 yfinance 시세 + 실제 RSS 뉴스**로
가동 중이고, 이미 PAPER 매수/청산 1건(AMD, -3.02%)까지 원장에 기록돼 있다.
KIS는 이 정본 엔진이 애초에 사용하지 않는다 (yfinance 기반).

→ 로컬에서 새 엔진(JOS_RECOVER_SIM_E.py)을 만드는 작업은 "엔진은 동일하다"는
CEO 철학과 어긋나는 **정본 분기(이탈)**다. 다음 패치는 "새로 만들기"가 아니라
"정본을 로컬에 동기화"다.

## 2. 본질

> "본질은 깊게 파고들수록 맥락이 통일된다. 시장만 바뀌고 엔진은 동일하다."

`JOS_MASTER.py`의 docstring 자체가 이미 `C:\JOS_OS`를 로컬 실행 경로로
명시하고 있다:

```
Run (continuous, local):
    cd C:\JOS_OS
    python .\JOS_MASTER.py

Run (single intraday pass, cloud/CI):
    python JOS_MASTER.py --once

Run (end-of-day close / CEO report, cloud/CI):
    python JOS_MASTER.py --close
```

즉 "로컬용 정본"과 "클라우드용 정본"은 **이미 같은 파일**로 설계돼 있다.
`JOS_RECOVER_SIM_E.py`는 이 정본과 별개의 임시/폴백 스크립트로 보이며, 이
저장소 어디에도 존재하지 않는다 (grep 0건: `JOS_RECOVER_SIM`, `sim.db`,
`EGW00002`, KIS 관련 코드 전부 0건).

## 3. 현재 맥락 - Local(보고됨) vs Cloud(정본, 증거 확인됨)

| 항목 | 로컬 `C:\JOS_OS` (CEO 보고) | 클라우드 정본 (이 저장소, 증거 확인) |
|---|---|---|
| 엔진 파일 | `JOS_RECOVER_SIM_E.py` | `automation/python_paper_capital_runtime/JOS_MASTER.py` |
| 데이터 소스 | random 시뮬레이션 (AAPL/TSLA/BTC/ETH/INDEX 전부 stub) | yfinance 실시간 가격 + RSS 실제 뉴스, 25개 실티커 x 6섹터(AI_SEMI/TECH_PLATFORM/EV_BATTERY/BIO/DEFENSE/FINANCE) |
| 저장소 | `E:\JOS_DATA\sim.db` (SQLite) | `automation/python_paper_capital_runtime/ledger/*.jsonl`, `*.json` (git 커밋되는 append-only 원장) |
| 실행 주기 | 5초 루프 (로컬 수동) | GitHub Actions cron - 평일 08:00\~20:00 KST 매시간 (`jos_paper_capital_loop.yml`) + 평일 15:30 KST 마감 (`jos_paper_capital_close.yml`) |
| 실거래/실데이터 여부 | "실제 시장 데이터 없음" (보고) | 실제 PAPER BUY/SELL 1쌍 기록됨: AMD entry 490.33 -> exit 475.51, return -3.02%, win=false (`results_log.jsonl`, `learning_stats.json`) |
| 리포트 | 없음 | `reports/hourly/CHEONOK_HOURLY_*.{json,md}` 200개+ (2026-05-28 \~ 2026-06-10, 시간별) |
| KIS 연동 | TOKEN FAIL / EGW00002 | **사용 안 함** - JOS_MASTER.py는 KIS API를 호출하지 않음 |
| `datetime.utcnow()` 경고 | 보고됨 | JOS_MASTER.py는 전부 `datetime.now(timezone.utc)` 사용 (deprecated 호출 0건) |

**결론**: CEO가 보고한 5개 에러(TOKEN FAIL, EGW00002, `requests not defined`,
`res not defined`, `datetime.utcnow` 경고)는 전부 **정본 `JOS_MASTER.py`가
아닌, 별도의 `JOS_RECOVER_SIM_E.py`에서만 발생하는 문제**다. 정본을 그대로
실행하면 이 5개 에러는 애초에 발생할 여지가 없는 코드 경로다.

## 4. 상위 구조

`JOS_MASTER.py`는 이미 다음을 한 파일에서 수행한다 (docstring 발췌):
실시간 시세(yfinance) + 뉴스(RSS) + 스코어링/랭킹 + 리더 분석 + 섹터 강도 +
시장 상태 분류 + PAPER 포지션 관리(손절/트레일링/로테이션) + 포워드
시뮬레이션 + 적응형 학습 통계 + 원장 영속화 + 인트라데이/마감 리포트 루프 +
Telegram 발송(`CHEONOK_TELEGRAM_BOT_TOKEN`/`CHEONOK_TELEGRAM_CHAT_ID`, 시크릿
없으면 `HOLD_TELEGRAM_SECRETS_MISSING`).

이미 CASH CHAIN의 `Source -> Insight` 단계 핵심 엔진이 완성·가동 중이라는
뜻이다.

## 5. JOS 적합도 (Local 경로 평가)

| 경로 | 적합도 | 사유 |
|---|---|---|
| `JOS_RECOVER_SIM_E.py` 계속 개발 | **부적합 (PATCH_REQUIRED)** | 정본과 별개 코드베이스 분기, random stub만 생성, KIS 의존성으로 불필요한 에러 유발, "엔진은 동일하다" 철학 위반 |
| `C:\JOS_OS`를 이 저장소 클론으로 교체 후 `JOS_MASTER.py --once`/연속 모드 실행 | **적합 (PASS 경로)** | 정본 코드 그대로 사용, KIS 불필요, 클라우드와 동일한 ledger 스키마 -> 로컬/클라우드 결과를 그대로 비교·병합 가능 |

## 6. CASH CHAIN 매핑 (현재 위치, 증거 기준)

| 단계 | 상태 | 증거 |
|---|---|---|
| Source | ✅ | yfinance + RSS, `market_log.jsonl`/`news_log.jsonl` |
| Insight | ✅ | 스코어링/랭킹/리더 분석, `leader_analysis.json`(merge 시 main에 존재 - 경로 재확인 필요, §8 리스크 참조) |
| Offer/Content | ⚠️ HOLD | `_company/_agents/youtube/` 스킬 존재, "Vrew/일 3회 업로드" 자동화는 이 저장소에서 코드 증거 없음 |
| Lead | ⚠️ HOLD | `api/lead.js`, `cta-5m.html`, `40_템플릿/developer/landing-kit/files/CTA.tsx` 존재(배포 코드 PASS) - 그러나 `CHEONOK_LEDGER_STATUS.md`가 "Needs proof: First public CTA exposure, First lead" 명시 |
| Payment | ⚠️ HOLD | `_company/_agents/business/tools/paypal_revenue.py` 코드 존재, `paypal_revenue.json`(자격증명) 미설정 - PayPal 인보이스 "유지 중" 주장은 이 저장소 기준 미검증 |
| Delivery/Retention/Data Asset | ✅ (PAPER 한정) | `ledger/*.jsonl` append-only, `learning_stats.json` 누적 |
| Patch | ✅ | 이번 세션에 `scripts/jos_tool_scout.py`/`jos_radial_upgrade_engine.py` 최초 실행 + Shopify 등록 (커밋 `e9dd521`/`16d25f6`) |

## 7. 증거 상태 - "[프롬프트용 복사 요약본]" 클레임 검증

| 클레임 | 판정 | 근거 |
|---|---|---|
| GitHub -> Vercel 프로덕션 배포, CTA 랜딩 페이지 운영 중 | **PASS(배포) / HOLD(운영 증명)** | 코드 존재(`api/lead.js`, `cta-5m.html`, CTA.tsx). `CHEONOK_LEDGER_STATUS.md`: "Production deployment: READY"이지만 같은 문서가 "Needs proof: First public CTA exposure / First lead / First payment proof"를 명시 - "운영 중"은 트래픽/리드 증거 없음 |
| Pipedream/Make + Telegram + Claude API 자동화 워크플로우 설계 | **HOLD** | "Pipedream"/"Make" 관련 코드 0건. Telegram은 `tools/cheonok_telegram_inbox.py` + `JOS_MASTER.py` 발송 로직으로 실재하나 Pipedream/Make 연동은 이 저장소에 없음(외부/로컬 도구일 가능성, 이 세션에서 미확인) |
| 고빈도(일 3회) 영상 업로드 + Vrew 기반 편집 파이프라인 구축 | **HOLD** | `_company/_agents/youtube/` 스킬(trend_sniper, auto_planner 등) 존재. "Vrew", "일 3회" 빈도 설정 코드 증거 없음 |
| PayPal 수동 인보이스 루트 유지 | **HOLD** | 스크립트(`paypal_revenue.py`)는 있으나 자격증명 파일(`paypal_revenue.json`) 없음 - 미설정 |
| KIS/EGW00002/sim.db/JOS_RECOVER_SIM_E.py 관련 전부 | **별도 시스템(정본 아님)** | 이 저장소 0건. 정본 엔진은 KIS 불필요 |

## 8. 리스크

- **정본 분기 리스크**: 로컬 `JOS_RECOVER_SIM_E.py`가 계속 개발되면, 클라우드
  정본과 별개의 두 번째 PAPER 엔진이 영구화되어 "엔진은 동일하다" 철학과
  데이터 정합성이 깨진다.
- **과장 리스크**: "[프롬프트용 복사 요약본]"의 "운영 중", "구축했습니다",
  "유지하며" 같은 완료형 표현 중 일부(CTA 운영, Pipedream/Make, Vrew, PayPal
  인보이스)는 이 저장소 기준으로 UNVERIFIED_COMPLETE에 해당 - 다른 클라우드
  AI에게 그대로 전달하면 No-False-PASS 위반 소지.
- **원장 경로 불일치**: 직전 `main` fast-forward(`f67b8fd`)에 `ledger/account_status.json`,
  `essence_memory.json`, `final_veto_log.jsonl`, `global_flows.json`,
  `leader_analysis.json` 변경이 포함되어 있었으나, 이 파일들이 현재
  `automation/python_paper_capital_runtime/ledger/`에는 없다 - 다른 ledger
  루트가 존재할 수 있으므로 다음 세션에서 `git log --diff-filter=A -- '**/account_status.json'`
  등으로 실제 경로를 확인 필요 (이번 문서에서는 추측하지 않음, HOLD).

## 9. 다음 패치 (CEO 실행용, 로컬 `C:\JOS_OS`)

1. `C:\JOS_OS`를 이 저장소(`actorlee007-cmyk/cheonoksystem`, `main`)의 클론으로
   교체하거나, 기존 폴더 안에 이 저장소를 클론.
2. 의존성 설치 (CI와 동일):
   ```
   python -m pip install --upgrade pip
   python -m pip install yfinance feedparser
   ```
3. 단발 실행(클라우드와 동일 모드):
   ```
   cd C:\JOS_OS
   python automation\python_paper_capital_runtime\JOS_MASTER.py --once
   ```
4. 연속 로컬 모드가 필요하면 docstring의 `python .\JOS_MASTER.py` 루프 모드
   사용 - 단, 같은 `ledger/` 디렉토리를 클라우드와 공유(git push)하면 정본
   원장이 로컬/클라우드 모두 동일해진다.
5. `JOS_RECOVER_SIM_E.py` / `E:\JOS_DATA\sim.db` / KIS 연동 작업은 **중단**
   (정본 엔진과 무관, "엔진은 동일하다" 철학 위반).
6. KIS 실시간 시세가 정말 필요하다면 (yfinance가 커버 못하는 한국 장중 호가
   등), 이는 Layer 4 REAL DATA BRIDGE로 `JOS_MASTER.py`에 **추가 데이터
   소스로 통합**하는 패치 후보로 다루고 - 별도 엔진을 새로 만들지 않는다.

## 참고

- 정본 철학/안전/Five Agents: `docs/JOS_CHEONOK_MASTER_SYSTEM_v1.md`
- PAPER 엔진 정본: `automation/python_paper_capital_runtime/JOS_MASTER.py`
- 배포/리드 상태: `CHEONOK_LEDGER_STATUS.md`
- 도구 레지스트리(이번 세션 갱신): `runtime/ledgers/tool_registry.jsonl`,
  `runtime/ledgers/radial_upgrade.jsonl`
