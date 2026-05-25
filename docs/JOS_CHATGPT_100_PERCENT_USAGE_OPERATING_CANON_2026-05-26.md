# JOS ChatGPT 100% Usage Operating Canon — 2026-05-26

## Canon Integration Judgment

This document is added as a supporting operating protocol for JOS/CHEONOK.
It does not replace the JOS master canon.
It defines how ChatGPT must be used inside JOS so the system does not drift into vague conversation, tool-listing, or false reporting.

## Canon Placement

- Canon class: Operating Protocol
- Applies to: ChatGPT / connected tools / external-agent handoffs / report generation
- North Star: EXPOSURE -> LEAD -> PAYMENT -> DELIVERY -> REVIEW -> SUBSCRIPTION
- Safety: PAPER_ONLY remains TRUE; LIVE_TRADE remains BLOCKED
- No-false-PASS rule: evidence required before PASS

## Core Interpretation

ChatGPT is not used as a casual Q&A tool.
Inside JOS, ChatGPT is used as:

- thinking engine
- verification engine
- report engine
- productization engine
- automation design engine
- evidence-first operating coordinator

All ChatGPT use must follow:

```text
Goal -> Background -> Criteria -> Materials -> Role -> Verification -> Final Output Format
```

---

# 원문 통합본

## 결론

ChatGPT를 100% 활용하려면 **“잘 물어보기”가 아니라 “일 시키는 구조”**를 만들어야 합니다.

즉, 매번 이렇게 써야 합니다.

> **목표 → 배경 → 기준 → 자료 → 역할 → 검증 → 최종 산출물 형식**

---

## 1. ChatGPT를 쓰는 5단계 구조

### 1단계: 질문하지 말고 “목표”를 줘라

나쁜 예:

> 주식 뭐 사야 돼?

좋은 예:

> 한국장 기준으로 내일 관심종목 TOP30 후보를 만들어라.  
> 기준은 글로벌 자금 흐름, 미국장 섹터 강도, 환율, 금리, 테마 순환, 거래대금, 세력성, 리스크를 반영한다.  
> 실전 매수 추천이 아니라 PAPER_ONLY 시뮬레이션 후보로 정리한다.

ChatGPT는 **짧은 질문에는 짧은 추측**을 하고, **명확한 목표에는 구조화된 결과물**을 냅니다.

---

## 2. 매번 써야 하는 기본 프롬프트 공식

아래 형식이 가장 강합니다.

```text
너는 [역할]이다.

목표:
[내가 얻고 싶은 최종 결과]

배경:
[현재 상황, 문제, 조건]

입력자료:
[파일, 숫자, 링크, 문장, 기준]

판단기준:
1. [기준 1]
2. [기준 2]
3. [기준 3]

금지사항:
- 추측 금지
- 근거 없는 확정 금지
- 애매하면 한계 명시
- 사용자가 수동으로 할 일을 떠넘기지 말 것

출력형식:
1. 결론
2. 핵심 근거
3. 실행안
4. 리스크
5. 다음 액션
```

---

## 3. ChatGPT 기능별 100% 활용법

| 기능 | 제대로 쓰는 방법 |
|---|---|
| **Projects** | 장기 프로젝트별로 방을 나누고, 관련 파일·대화·지침을 한곳에 모아 지속 맥락을 유지한다. OpenAI 공식 설명상 Projects는 채팅, 파일, 지침, 관련 맥락을 한 공간에 묶는 용도다. |
| **Custom Instructions** | 매번 반복할 말투, 역할, 금지사항, 출력 형식을 고정한다. 공식 문서상 Custom Instructions는 ChatGPT가 응답할 때 고려해야 할 내용을 미리 전달하는 기능이다. |
| **Memory** | 장기적으로 반복되는 선호, 프로젝트 원칙, 운영 기준을 기억시킨다. OpenAI는 사용자가 메모리를 직접 관리·삭제·비활성화할 수 있다고 설명한다. |
| **파일 업로드 / 데이터 분석** | 엑셀, CSV, 보고서, 캡처를 넣고 요약이 아니라 계산·분류·랭킹·차트까지 맡긴다. 공식 문서상 ChatGPT는 업로드 파일 분석, 데이터 질문 답변, 표·차트 생성을 지원한다. |
| **Deep Research** | 복잡한 시장·사업·정책·경쟁사 분석처럼 여러 출처 검증이 필요한 작업에 쓴다. 공식 설명상 Deep Research는 온라인 작업을 조사·종합해 문서화된 보고서로 만드는 기능이다. |
| **Tasks** | 매일 반복되는 브리핑, 리마인더, 정기 점검을 자동화한다. OpenAI 공식 문서상 Tasks는 자동화된 프롬프트를 실행하고 사용자에게 알림을 주는 기능이다. |
| **Apps / Connectors** | Gmail, Drive, Calendar, Notion 등 내부 자료가 필요한 작업에 연결해 쓴다. 공식 문서상 Apps는 연결된 외부 서비스에서 관련 정보를 찾아 대화에 가져올 수 있다. |

Reference links from source text:

1. https://help.openai.com/en/articles/10169521-projects-in-chatgpt
2. https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions
3. https://help.openai.com/en/articles/8590148-memory-faq
4. https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt
5. https://help.openai.com/en/articles/10500283-deep-research-in-chatgpt
6. https://help.openai.com/en/articles/10291617-tasks-in-chatgpt
7. https://help.openai.com/en/articles/11487775-connectors-in-chatgpt

---

## 4. 한울님 기준 최적 사용법

한울님은 ChatGPT를 이렇게 써야 합니다.

### A. 일반 검색용으로 쓰지 말 것

검색은 누구나 합니다.  
한울님에게 필요한 건 검색이 아니라:

```text
수집 → 정리 → 충돌 분석 → 생존 검증 → 상품화 → 보고서화
```

입니다.

---

### B. 매일 같은 구조로 명령할 것

예시:

```text
JOS 정본 기준으로 오늘 시장을 분석해라.

목표:
내일 한국장 TOP30 PAPER 후보 생성

반영:
1. 미국장 섹터 흐름
2. 일본장/중국장/홍콩장 흐름
3. 환율/금리/원자재
4. 한국장 시간외/장중 수급
5. 테마 순환
6. 전일 실패 테마
7. 장전 강세 후 붕괴 가능성
8. 세력성/거래대금/뉴스 지속성

출력:
1. 오늘 글로벌 핵심 변화
2. 한국장 번역 테마
3. TOP30 후보
4. 생존율
5. 실패 조건
6. 구독자용 요약
7. CEO 보고
8. PAPER_ONLY 최종 상태
```

---

### C. “질문”보다 “검증”을 시킬 것

나쁜 사용:

```text
이거 괜찮아?
```

좋은 사용:

```text
이 전략을 12개 관점에서 반박해라.
억만장자, 기관, 세력, 개인투자자, 정책가, 퀀트, 역사, 법률, 구독자 관점에서 실패 조건을 찾아라.
마지막에 살아남는 조건만 남겨라.
```

---

## 5. 가장 강한 명령어 10개

바로 쓰면 됩니다.

```text
1. 이 답변을 상위 1% 기준으로 다시 압축해라.
2. 내가 놓친 리스크를 먼저 찾아라.
3. 반대로 생각하면 어떤 결론이 나오는지 분석해라.
4. 이 아이디어를 실제 돈이 되는 상품으로 바꿔라.
5. 고객이 돈을 낼 이유만 남겨라.
6. 실패할 조건을 먼저 정리해라.
7. 오늘 기준 최신 정보로 검증해라.
8. 보고서, 실행안, 구독상품 버전으로 각각 변환해라.
9. 중복·추측·허세를 제거하고 정본만 남겨라.
10. 사용자가 직접 할 일을 없애고 자동화 구조로 바꿔라.
```

---

## 6. 최종 운영 원칙

ChatGPT를 100% 쓰는 사람은 이렇게 씁니다.

```text
생각 보조 X
검색 보조 X
글쓰기 보조 X

→ 판단 엔진
→ 검증 엔진
→ 자동 보고 엔진
→ 상품화 엔진
→ 반복 개선 엔진
```

한울님 기준으로는 ChatGPT를 **비서**가 아니라 **JOS/CHEONOK 운영체제의 상위 사고·검증·보고 엔진**으로 써야 합니다.

---

## 한 줄 정본

> ChatGPT는 질문을 잘하는 도구가 아니라, **목표·자료·기준·검증·출력형식을 고정했을 때 자동으로 결과물을 만드는 운영 시스템**이다.

**현재 상태: 자율 학습 및 PAPER 데이터 축적 상태.**

---

## JOS Enforcement Layer

Every JOS interaction with ChatGPT must be filtered through the following mandatory gates:

```text
1. North Star Check
   Does the request strengthen EXPOSURE -> LEAD -> PAYMENT -> DELIVERY -> REVIEW -> SUBSCRIPTION?

2. Canon Filter
   Does it match the JOS master canon, PAPER_ONLY safety, and Final Veto rules?

3. Top-1 Perspective Council
   Has the issue been checked through operator, programmer, business, revenue, risk, customer, and evidence perspectives?

4. Evidence Gate
   What record, commit, log, email, payment proof, or artifact proves the result?

5. No-False-PASS Gate
   If evidence does not exist, status must be HOLD / VERIFY_REQUIRED / PATCH_REQUIRED, not PASS.
```

## Final Canon Line

ChatGPT must not be used as a question-answering interface inside JOS.
It must be used as a structured operating engine that receives goals, applies canon filters, checks top-1 perspectives, verifies evidence, and produces execution-ready outputs.
