# JOS Notion Bookmark Classification — 2026-06-11

## 0. 목적 / 방법 / 한계 (No-False-PASS)

CEO 지시: Notion 워크스페이스(`👋 Notion에 오신 것을 환영합니다!`,
https://app.notion.com/p/35ce3f282659804f80ddda26bf9cbf47)에 쌓인 약 93개
북마크(중복 포함)를, 사용자가 선택한 4개 카테고리
(트레이딩 인사이트 / 유튜브·쇼츠 수익화 / 클로드코드 자동화 /
1인기업·수익모델)에 대해 **정본 기준**(`docs/JOS_CHEONOK_MASTER_SYSTEM_v1.md`,
`docs/HOURLY_NOTION_SOURCE_INTELLIGENCE_PROTOCOL_2026-05-26.md`,
North Star: EXPOSURE→LEAD→PAYMENT→DELIVERY→REVIEW→SUBSCRIPTION)으로
**사업화(Revenue)** / **시스템(System/Automation)** 분류를 진행한다.

**적용한 방법**: Hourly Notion Source Intelligence Protocol의 10문항
디컴포지션을 항목 93개 각각에 적용하는 것은 비현실적이므로(거의 모든
항목에 메모 0개, YouTube 자막은 이 환경에서 IP 차단 — Task A에서
2건 확인됨), **클러스터(주제군) 단위**로 경량 디컴포지션을 적용했다.

**한계 (반드시 명시)**:
- 모든 분류는 **제목/URL만 근거**로 한 1차 분류(Evidence Status =
  `TITLE_ONLY / HOLD`)다. 영상 본문, 댓글, 설명란은 확인하지 않았다.
- 추정·확정이 아니라 "제목이 시사하는 카테고리"이며, 실제 영상 내용이
  다를 수 있다.
- 이미 Task A에서 처리된 2건(`이거 깨닫고 시드 40억`,
  `55억 자산 비법 저평가우량주 점수표`)은 결과만 요약하고 재작업하지
  않았다.
- 본 문서는 "분류 + 다음 액션 제안"까지이며, 90개 항목 각각의 코드
  구현은 범위에서 제외한다(과잉 구현 금지). 대신 가장 근거가 뚜렷한
  2건만 "Quick Win"으로 실제 구현했다(§8).

---

## 1. 도메인 → 정본 타겟 매핑

| 사용자 카테고리 | 정본 Layer / Agent | CASH CHAIN 단계 | 리포 타겟 |
|---|---|---|---|
| 트레이딩 인사이트 | Layer 5~11 (RANK OVERLAP ~ PAPER VALIDATION), Layer 12 SUBSCRIPTION REPORT | EXPOSURE / DELIVERY (콘텐츠 소재) | `automation/python_paper_capital_runtime/JOS_MASTER.py` |
| 유튜브/쇼츠 수익화 | Revenue Agent, North Star EXPOSURE→LEAD | EXPOSURE / PAYMENT | `automation/python_youtube_runtime/`, `_company/_agents/youtube/`, `_company/_agents/editor/` |
| 클로드코드 자동화 | Technology Agent, Layer 16 GOD HYBRID MIND ENGINE, Layer 18 AUTO REVIEW PATCH COUNCIL | DELIVERY (운영 효율) | `.claude/skills/`, `.claude/agents/`, `_company/_agents/*/skills/` |
| 1인기업/수익모델 | Revenue Agent, SUBSCRIPTION_ASSETS 탭 | PAYMENT / SUBSCRIPTION | `_company/_agents/business/`, `docs/` (참고 카탈로그) |

---

## 2. A. 트레이딩 인사이트 (→ `automation/python_paper_capital_runtime`)

| 클러스터 | 항목 (제목 / Notion 링크) | 사업화 | 시스템 |
|---|---|---|---|
| **A1. 추세/리스크 디시플린**(손절·익절) | [수익은 짧고 손실은 길게? 이러면 절대 못 법니다](https://app.notion.com/p/36be3f28265981768f72fe5776c5745d), [주식 고수만 아는 익절 참는 법](https://app.notion.com/p/36fe3f282659816f816bcfb03e4b75a8), [이거 깨닫고 시드 40억 달성한 트레이더](https://app.notion.com/p/37ce3f28265981e49094c959143a7f59) | Subscription Report 코멘터리 소재 | ✅ **이미 구현됨** — `trend_breakout_signal()` (Task A, commit `1f48c2b`, `main`에 머지됨) |
| **A2. 지표 우선순위론**(거래량/VWAP/기관유동성/스탑헌팅) | [거래량...타점이 중요한 이유 ×2](https://app.notion.com/p/373e3f28265981b7b086c6e67f978353) / ([중복](https://app.notion.com/p/378e3f28265981d8afabec8cb3af35c2)), [VWAP 매매전략 핵심포인트](https://app.notion.com/p/376e3f28265981c29878c4f9dbaa4c84), [기관유동성 체크하는법](https://app.notion.com/p/37be3f28265981e893fed661c8dec93c), [스탑헌팅](https://app.notion.com/p/37be3f282659815a99dfe6c9bba9e5b7), [하락장을 대비하는 것이 더 중요한 이유](https://app.notion.com/p/36de3f282659815ba3cfc3e168f9d13f) | 콘텐츠 소재(지표 비교 시리즈) | HOLD — `score_market()`/`rank_engine()` 가중치 추가 후보. 제목만으로는 구체 룰을 알 수 없어 **구현 보류**, 추가 조사 필요 |
| **A3. 종목/테마 추천** | [삼성전기 MLCC 유리기판 대장주](https://app.notion.com/p/36ce3f28265981b69f05ed48cede8978), [구글 AI 연합 수혜주 TOP3](https://app.notion.com/p/36de3f28265981c482d6e75640bcd2f2), [국민연금 매수 1티어 소형주](https://app.notion.com/p/37ce3f282659813f9f9fd61e5cd29206), [도시광산 제련 기술](https://app.notion.com/p/36de3f28265981afa2ebf523e614af10) | Layer 6 THEME CLUSTER 콘텐츠 소재 | HOLD — 종목명은 `KOREA_THEME_TRANSLATION` 입력 후보지만, **개별 종목 추천을 코드에 하드코딩하는 것은 정본 위반 소지**(추측/근거 없는 확정). 자동 수집 파이프라인(Layer 4 REAL DATA BRIDGE)으로만 흡수 가능 |
| **A4. 거시/시황·마인드셋** | [내가 먼저 한 코인...월가가 따라옵니다](https://app.notion.com/p/36ae3f282659819d9e77d2725a95eca9), [워렌버핏 3500억](https://app.notion.com/p/36ce3f2826598104a759e9914060e440), [1500억 벌어보니](https://app.notion.com/p/36ce3f28265981f1b29de8646ecd73b8), [일론 머스크의 예측](https://app.notion.com/p/36ce3f28265981d78e4df91f1c31b603), [코스피 더 오를 수 있나](https://app.notion.com/p/37be3f2826598112a46dc93633df56cd), [무조건 가난해지는 통장의 비밀](https://app.notion.com/p/36de3f2826598163a4a9c3f546e8f711), [100억 트레이더 #코인단타](https://app.notion.com/p/37be3f28265981239108c03db76caf31) | Subscription/CEO Report 칼럼 소재 | 해당 없음 (정성적) |
| **A5. 퀀트+AI** ★ | [유퀴즈 한국인 최초 퀀트 우승자, AI 사용법(UNIST 김민겸)](https://app.notion.com/p/37be3f2826598155af52d35a89ebc884) | "AI+퀀트" 포지셔닝 — JOS Paper Capital의 정체성과 직접 일치 | HOLD — 콘텐츠 소재로는 강력하나 구체 알고리즘 불명, 구현 보류 |
| 처리 완료 (Task A) | [55억 자산 비법 저평가우량주 점수표](https://app.notion.com/p/37ce3f28265981fc878ed2ebe2b48b8c) | — | dead end (이미지가 무관한 썸네일, 보고 완료) |

---

## 3. B. 유튜브/쇼츠 수익화 (→ `automation/python_youtube_runtime`, `_company/_agents/youtube`, `_company/_agents/editor`)

| 클러스터 | 항목 | 사업화 | 시스템 |
|---|---|---|---|
| **B1. 멀티플랫폼 배포/외주 자동화** | [쇼츠 1개로 5군데 배포](https://app.notion.com/p/36be3f282659817e80d7f8888248e68e) ([중복](https://app.notion.com/p/36be3f282659814db6ebdb75b826765b)), [쇼핑쇼츠 외주 월3000만원](https://app.notion.com/p/36ee3f28265981408c2fee26cb3f5710), [사진3장 쇼핑쇼츠 20억](https://app.notion.com/p/37ae3f28265981229c45c1796851ce75) | 멀티채널 배포 = 동일 산출물 재활용 (EXPOSURE 극대화) | HOLD — `_company/_agents/editor/`(영상→음악/배포 도구 보유)에 "1 source → N platform" 배포 단계 추가 후보. 플랫폼별 API 연동 필요, 구현 보류 |
| **B2. AI 채널 대량 운영** | [AI로 채널 400개, 연 매출 8억 ×3](https://app.notion.com/p/36be3f282659810f9dd8e12dbc9d9e52), [온가족 유튜브 5억](https://app.notion.com/p/37ae3f2826598142bbe8e3f776d8f059) | 채널 다각화 = 구독자/노출 다각화 | HOLD — `_company/_agents/youtube/tools/auto_planner.py`가 단일 채널 자동화 구조. N채널 확장은 큰 변경, 구현 보류 |
| **B3. AI 음성/자막 도구** ★ | [목소리 복제 영상자동화 (클로드코드+보이스박스+하이퍼프레임) ×2](https://app.notion.com/p/36be3f28265981ea9c61f8321e021d1b), [자막다운 다운섭](https://app.notion.com/p/37ae3f2826598191bfb3eae995bb8b9b), [자막제거 v메이커 ×2](https://app.notion.com/p/37ae3f28265981c588ffdc38c92803d4) | 제작 시간 단축 → 산출량↑ | `_company/_agents/editor/tools/`에 이미 `music_generate`/`music_to_video` 존재. 보이스 클로닝/자막 도구는 **외부 SaaS 의존**(보이스박스, 하이퍼프레임 — 계정/요금제 필요) → 사용자 계정 셋업 선행 필요, 구현 보류 |
| **B4. 틈새 채널 사례 모음** | [쇼츠 하나로 월1000](https://app.notion.com/p/36be3f282659813eb686f66f35637b87), [AI경제 채널 월3000](https://app.notion.com/p/36be3f28265981d39f2bd7b437565f8f), [1.2억 짧은영상](https://app.notion.com/p/36be3f28265981b58e0dd63cc08ec7b6), [청주 주부 미국 비밀영상](https://app.notion.com/p/373e3f282659812e9199ce106ab18e9d), [대소변 참기 세계1위](https://app.notion.com/p/36ee3f28265981c69023d78a2c89f31e), [10만 뉴스채널 수익공개](https://app.notion.com/p/36ee3f28265981adb371d6ad6e183417), [영상 안만들고 쇼츠 치트키 5억](https://app.notion.com/p/370e3f2826598137bda5db4af52528c3), [AI 음악 유튜브](https://app.notion.com/p/37ae3f2826598100b116c0e0e117fa20) | `_company/_agents/youtube/goal.md` 채널 기획 인풋(벤치마크 사례) | 해당 없음 |

---

## 4. C. 클로드코드 자동화 (→ `.claude/skills/`, `.claude/agents/`, `_company/_agents/*/skills/`)

| 클러스터 | 항목 | 사업화 | 시스템 |
|---|---|---|---|
| **C1. 스킬 vs 에이전트 아키텍처** ★★★ | [진짜는 에이전트가 아니라 '스킬'이었다 95프로시스템](https://app.notion.com/p/37ae3f28265981b0a1ebfa31e28a7142) | 자동화 효율 = 운영비 절감 | ✅ **Quick Win 구현** (§8-1) — `_company/_agents/*/skills/`(이미 존재) + `.claude/skills/jos-council-review`(이미 존재) 패턴을, Notion 소스 인텔리전스 프로토콜에도 새 스킬로 적용 |
| **C2. 비동기/오버나이트 개발** | [퇴근할때 다음날 아침에 개발 #에이전트뷰](https://app.notion.com/p/376e3f282659811fb534f21a4dbf8b52), [클로드코드 10개월 50가지](https://app.notion.com/p/376e3f282659817f94d6d6f7cfacf4d0), [클로드 비밀무기 31가지](https://app.notion.com/p/37ae3f282659811bad07c40d1d516bd4), [바이브코딩 공부해야하나](https://app.notion.com/p/376e3f2826598131b761dfafbd85e2fd) | — | 본 세션 자체가 이 패턴(원격 컨테이너, 비동기 PR 워크플로)의 실사용 사례. 추가 코드 변경 불필요, **운영 관행으로 이미 반영 중** |
| **C3. 유튜브 채널 클론/운영(Claude)** | [Clone Any Youtube Channel With Claude AI ×2](https://app.notion.com/p/370e3f28265981a7a80bf53942c5ba6d), [How to Start a YouTube Channel With Claude](https://app.notion.com/p/376e3f282659810a81ebd21feeb7f440), [콘텐츠 무한생성](https://app.notion.com/p/37ce3f28265981d8b484cddae0da9213), [카드뉴스 디자인 자동화](https://app.notion.com/p/37be3f28265981f8a18fcf5ca575c5e2) | B2/B3와 동일 카테고리 | `_company/_agents/youtube/`, `editor/`로 흡수 가능하나 영상 본문 미확인 → HOLD |
| **C4. AI 사업화/에이전시 모델** | [How I'd Make Money with Claude AI 2026](https://app.notion.com/p/370e3f282659816fb6b1e8a634272c60), [The AI Agency Nobody's Building](https://app.notion.com/p/373e3f28265981408bc6cea791925c6a), [코드 한줄 안짜고 마케팅 에이전트](https://app.notion.com/p/370e3f282659814eb9aee87df777e03c), [사업에서 AI 제대로 쓰는 법 ChatGPT 5가지](https://app.notion.com/p/370e3f282659818ba4fdfcfd8278958f) | §6 D1 수익모델 카탈로그와 통합 | — |
| **C5. AI 도구/뉴스(참고용)** | [커서 AI #커서](https://app.notion.com/p/375e3f28265981c09bfee4e0f6c43710), [구글 젬마4 출시](https://app.notion.com/p/376e3f2826598181b01ae3fb5c44667d), [AI영상표현 고려대특강](https://app.notion.com/p/36ee3f282659811d9af3f9038ee4eaab), [힉스필드 슈퍼컴퓨터](https://app.notion.com/p/36ee3f28265981b4af6df330f0dd20a0), [AI자동화 영상제작 시간단축 가이드](https://app.notion.com/p/36be3f28265981f59875c17e604f8138), [Tistory365Blog AI자동화 블로그](https://app.notion.com/p/36be3f28265981378c51df6e906b5a10) | — | 일반 동향 참고. 액션 없음 |
| **C6. 계정 관리** ⚠️ | [폰 하나로 앱 무제한 복제, 부계정 굴리기](https://app.notion.com/p/377e3f28265981f6a5f0f0ce7cddbd69) | — | **BLOCK 권고** — 멀티 부계정 운영은 플랫폼 ToS 위반/계정 정지 리스크. Final Veto의 "unresolved legal/security risk" 해당. 시스템 흡수 비권장 |

---

## 5. D. 1인기업/수익모델 (→ `_company/_agents/business/`, `docs/` 참고 카탈로그)

| 클러스터 | 항목 | 사업화 | 시스템 |
|---|---|---|---|
| **D1. 수익모델 카탈로그** ★★ | [돈 버는 방식은 정해져 있다, 수익모델 15종 ×2](https://app.notion.com/p/370e3f28265981329c47e7bdfb923e12), [The Only 14 Ways to Make Money with AI 2026](https://app.notion.com/p/370e3f2826598140bb5bdafe8a14d3cd), [내 사업에 딱 맞는 수익모델 찾기](https://app.notion.com/p/36fe3f28265981d893f0dccea7183d47), ["이 단계" 부자되는 6단계 법칙](https://app.notion.com/p/36fe3f2826598116be45d5385f8a712a) | ✅ **Quick Win 구현** (§8-2) — 본 문서 §8-2의 "수익모델 후보 ↔ 기존 에이전트 매핑 표" | — |
| **D2. 위탁/이커머스/중고거래** | [02년생 과일위탁 2026](https://app.notion.com/p/36be3f282659811ea126eebeccc12f4f), [아마존 상세페이지 개판이어도 대박](https://app.notion.com/p/37be3f28265981329f48f0f5b699fd71), [당근치트키 20억](https://app.notion.com/p/371e3f2826598166967dce60e5cf9581), [자판기로 수억 컴맹](https://app.notion.com/p/37ae3f28265981e88860c6d989ff410d) | D1 카탈로그의 "물판/위탁/중고" 항목 사례 | — |
| **D3. 콘텐츠/AI 부업 사례** | [45살 부업 월순익1억](https://app.notion.com/p/36be3f28265981848476d77e9a4633cb), [잔고3만원→챗GPT 콘텐츠 월1억(안혜빈)](https://app.notion.com/p/378e3f28265981f7ae24eab25f4f40ba), [일기10개로 네이버광고승인](https://app.notion.com/p/36ce3f2826598144a4cad08eedb0d9fe), [잠자는동안 영업사원 #shorts](https://app.notion.com/p/36ee3f2826598168bb4ce39efab8555c) | D1 카탈로그의 "콘텐츠/광고수익" 항목 사례 | — |
| **D4. 경영/마인드셋** | [부자 1200억 충성고객](https://app.notion.com/p/36ee3f28265981409dbff6b3338a5bb2), [사장과 직원의 시간](https://app.notion.com/p/36fe3f28265981c2b45de2e9b50d7221), [회사에서 일잘하는법 본질/why기법 ×2](https://app.notion.com/p/36fe3f282659818ea446d73b8b6ce4fd), [컨설팅·데이터분석·마케팅 혼자(고영혁)](https://app.notion.com/p/370e3f28265981ae90a8cb7b6a7f8a68) | 운영 원칙 참고 | — |
| HOLD (제목 불명) | ["Ai놓자"](https://app.notion.com/p/370e3f282659814b9498c9b4724c37eb) | 제목이 깨져있어 분류 불가 — **추측 금지, HOLD** | — |

---

## 6. E. 제외 항목 (자기계발/건강/라이프스타일 — 사업화·시스템 무관)

다음 18건은 제목상 "본질/마인드셋/건강/라이프스타일" 콘텐츠로,
4개 카테고리(트레이딩/유튜브/클로드코드/1인기업) 어디에도 속하지 않아
이번 분류에서 제외했다. 필요 시 콘텐츠 소재(자기계발 채널)로 재검토 가능:

[국내 최고급 호텔바의 의외의 가격](https://app.notion.com/p/369e3f28265981e7b8afe91c945d923f) ([중복](https://app.notion.com/p/370e3f28265981c7a54addf30b412f5e)) ·
[밤새고 머리 멍할 때 #뇌과학](https://app.notion.com/p/36ae3f282659814d939df346cda8a71c) ·
[뇌를 60시간 폭풍 실행](https://app.notion.com/p/36ce3f28265981af8442dcc5f6533ef3) ·
[성공한 사람들의 스트레스 관리법](https://app.notion.com/p/36ce3f28265981d2bfb9f77ff096a8f8) ·
[본질을 쫓으면 성공한다](https://app.notion.com/p/36fe3f2826598115b449c16c5770fe07) ·
[본질을 이해하자](https://app.notion.com/p/36fe3f282659812ab0d0f74b7aa90922) ·
[잡음을 버리고 본질에 몰두하라](https://app.notion.com/p/36fe3f28265981cfb662dfffb01906e7) ·
[서울대 우울증검사](https://app.notion.com/p/36fe3f28265981febaefdc09d0ce9f41) ·
[본질을 모르면 삶은 허상](https://app.notion.com/p/36fe3f282659818ebb4df7cc275af4d7) ·
[본질을 파악하라](https://app.notion.com/p/36fe3f28265981699319fe09cff2aee7) ·
[사람을 파악하는 4가지 기준](https://app.notion.com/p/36fe3f2826598140872bc7f4e9c6da32) ·
[본질을 꿰뚫는 질문력](https://app.notion.com/p/36fe3f28265981d0b914f25677810b61) ·
[심장 노화 되돌리는 방법](https://app.notion.com/p/36fe3f2826598184a6a8ce2aeaf1ccbf) ·
[이지영쌤 시간관리](https://app.notion.com/p/36fe3f282659816380f9d8bfd4b9f455) ·
[인생이 망했다고 좌절하는 너에게](https://app.notion.com/p/36fe3f282659815ca79bd10207514c62) ·
[리더가 된 후 가장 많이 하는 착각](https://app.notion.com/p/36fe3f28265981838e38c32e925b025b) ·
[스킨십이 중요한 이유](https://app.notion.com/p/36fe3f2826598161b133c81006bac776) ·
[100년이 지나도 변하지 않는 23가지 본질](https://app.notion.com/p/36fe3f28265981a0a7c9c01e70a551ba)

---

## 7. 중복 정리

다음 항목들은 동일 영상이 2~3회 중복 북마크된 것으로 보인다(제목 동일,
ID만 다름). 정리 시 1건만 남기고 나머지는 삭제 후보 — **단, Environment
Agent 원칙에 따라 본 작업에서 직접 삭제하지 않고 후보만 제시**:

- AI로 채널 400개, 연 매출 8억 — 3건
- 거래량...타점이 중요한 이유 — 2건
- 목소리 복제 영상자동화(보이스박스+하이퍼프레임) — 2건
- 쇼츠 1개로 5군데 배포 — 2건
- 자막제거 v메이커 — 2건
- Clone Any Youtube Channel With Claude AI — 2건
- 회사에서 일잘하는법 본질/why기법 — 2건
- 돈 버는 방식은 정해져 있다, 수익모델 15종 — 2건
- 국내 최고급 호텔바/신라호텔바 — 2건

---

## 8. Quick Win 구현 (이번 세션에서 실제 작업한 항목)

### 8-1. 시스템화: `.claude/skills/jos-notion-source-scan` 신설

C1("스킬 vs 에이전트 95프로시스템")의 시사점과
`docs/HOURLY_NOTION_SOURCE_INTELLIGENCE_PROTOCOL_2026-05-26.md`(이미
정본에 명시되어 있으나 실행 가능한 형태로는 없던 프로토콜)을 결합해,
`/jos-council-review`와 동일한 패턴의 새 Claude Code 스킬을 추가했다.
이 스킬은 다음에 Notion에 새 북마크가 쌓였을 때, 본 문서를 갱신하는
**반복 가능한 절차**를 제공한다 (상세는 해당 SKILL.md 참고).

### 8-2. 사업화: 수익모델 후보 ↔ 기존 에이전트 매핑

D1(수익모델 카탈로그) 항목들의 제목에서 공통적으로 등장하는 수익모델
유형을, **일반적으로 알려진 비즈니스 모델 분류**(영상 본문 미검증,
일반 지식 기반)로 정리하고 이 리포의 기존 `_company/_agents/`와
매핑했다:

| 수익모델 유형 (D1/D2/D3에서 반복 등장) | 이 리포의 대응 에이전트/시스템 | 현재 상태 |
|---|---|---|
| 콘텐츠/조회수 광고 수익 (쇼츠·유튜브) | `_company/_agents/youtube/`, `editor/` | 운영 중 |
| AI 자동화 대행/에이전시 (마케팅 에이전트 등) | `_company/_agents/business/` | `tools/paypal_revenue.py` 존재 — 결제 인프라 일부 구축됨 |
| 구독/리포트 판매 (Subscription Report) | `automation/python_paper_capital_runtime` Layer 12 | 운영 중 (`subscription_report.json`) |
| 위탁/이커머스/중고거래 (당근, 아마존, 과일위탁) | 없음 | **신규 영역** — 결제·배송·재고 관리 필요, 이번 세션 범위 밖 |
| SNS 부계정/계정 다중화 | 없음 | **BLOCK 권고** (§4 C6) |

이 표는 "어떤 수익모델이 이미 시스템화되어 있고, 어떤 모델이 신규
투자가 필요한지"를 한눈에 보여주기 위한 것이며, **개별 영상의 구체
전략을 검증한 것은 아니다** (영상 제목 기반 일반 분류).

---

## 9. JOS Merge Decision (요약)

| 카테고리 | 사업화 흡수 | 시스템 흡수 | HOLD/BLOCK |
|---|---|---|---|
| 트레이딩 인사이트 | A1 (이미 구현, Task A) | A2/A3/A5 — 추가 조사 필요 | A3 종목 하드코딩은 BLOCK (정본 위반) |
| 유튜브/쇼츠 수익화 | B4 사례는 콘텐츠 기획 참고로 흡수 | B1/B2/B3 — 외부 SaaS·API 의존, HOLD | — |
| 클로드코드 자동화 | C4 → D1로 통합 | C1 (Quick Win 구현, §8-1) | C6 BLOCK 권고 |
| 1인기업/수익모델 | D1 (Quick Win 매핑, §8-2) | D2/D3은 D1의 사례로 흡수 | "Ai놓자" HOLD (제목 불명) |

---

## 10. Next Action

1. (선택) `.claude/skills/jos-notion-source-scan`을 1회 실행해, 이번에
   "제외" 처리한 18건/HOLD 항목들에 대해 영상 설명·댓글 등 추가 근거를
   확보할 수 있는지 재시도.
2. (선택) D2(위탁/이커머스) 영역을 신규 사업으로 진행할지는 CEO 판단
   필요 — 결제/배송 인프라가 없으므로 별도 스코핑 세션 권장.
3. §7 중복 북마크 정리는 사용자가 Notion에서 직접 삭제 권장(자동
   삭제는 수행하지 않음).
