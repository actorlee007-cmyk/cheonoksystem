# 집가서 할 것 (운전 중 메모)

## 1. 노트북 연동 시스템
- 목적: 운전 중 떠오른 아이디어를 모바일로 던지고, 집 노트북에서 정리/실행하는 흐름 만들기
- 우선 검토: Claude Cowork 기반 설계 - https://youtu.be/5q5ZUpwgj4E
  ("클로드 코워크 전문가처럼 쓰는 꿀팁 5가지" - 프로젝트로 사고하기 + 맥락 채우기 + 음성 기능,
  데모로 "매주 월요일 9시 자동 주간 매출 모니터링 시스템"을 Cowork로 셋업함.
  집에서 Cowork 켜놓고 같이 셋업해볼 것 - JOS_MASTER.py 주간 리포트와 역할 겹치는지/
  모바일 음성 인터페이스로 보완되는지 확인)
- 첫 Cowork 적용 사례 (주식 시스템, 2WJnNhQD2go "Claude Fable 5 실거래 테스트" 영상 관련):
  - JOS_MASTER.py Layer 22/23(STRATEGY MULTIVERSE/AUTO CANONICAL FILTERING)이 이미
    "전략 생성->병행 페이퍼트레이딩 백테스트->자동 승격" 루프를 갖고 있음 (STRATEGIES 딕셔너리에
    primary/shadow_fixed_pct 두 변형, evaluate_strategy_promotion이 우위 입증되면 자동 교체)
  - Claude(Fable 5/Cowork)의 역할 = "전략 생성" 단계만: 매주 learning_stats.json
    (primary vs shadow) + leader_analysis.json을 읽고 새 risk_mode/rotation_mode 조합을
    새 shadow 변형으로 STRATEGIES에 제안 -> 기존 Layer 23이 검증/승격 그대로 처리
  - PAPER_ONLY/LIVE_TRADE BLOCKED 불변 - Claude는 매매 안 함, 파라미터 가설만 제안
- 참고 영상 (YouTube 자막 차단으로 못 읽음 - 집에서 직접 설명해주면 그걸로 설계):
  - https://youtu.be/3XhbI597gm8
  - https://youtube.com/shorts/Vw7GG0tKt_Q ("미래준비")
  - https://youtube.com/shorts/zFXzqDynTBY ("시스템 업그레이드")

## 2. 플리(플레이리스트) 채널
- 아이디어: 큐레이션 + 썸네일 자동화 기반 음악 플레이리스트 채널 (CHEONOK 본 시스템과 독립)
- 참고: https://youtu.be/LXhRtn5EDLw (플리 썸네일 공식 - 음악보다 썸네일이 조회수 가른다)
- 우선순위: 주식 시스템/구독 정리 이후, 별도 트랙으로 시작

## 3. AI 영상 광고 소재 (6초 KO 16:9 CTA-Value) 만들어보기
- 참고: https://youtu.be/4kIM20RPZHs (AI 광고 생성 파이프라인이 만든 6초 영상 광고 소재 샘플)
- 연결: automation/google_ads/campaigns/business_diagnosis_skag.json (무료 사업 진단 SKAG 캠페인)의 영상 광고 버전
- 할 일: 같은 포맷(6초, 한국어, CTA-Value)으로 스크립트/스토리보드 작성 -> Capcut AI/Veo 등으로 렌더링 시도

## 4. 이지비디오(EasyVideo) - 대본->AI영상 SaaS 가입/평가
- 참고: https://youtu.be/NeOYP50G_Jk (할인코드 ai1sang5000, 5000원 할인)
- https://easyvideo-landing.vercel.app/?ref=youtuber1sang
- 연결: (3) 영상 광고 소재 제작 엔진 + 블로그 초안 001-003을 영상/쇼츠로 변환하는 파이프라인
- 할 일: 가입 후 SKAG 영상 스크립트 1개 테스트 렌더링

## 5. Higgsfield MCP / citevue.com (홈페이지구축 영상 참고)
- Higgsfield MCP: 비주얼/디자인 에셋 생성 도구 - 랜딩페이지/광고 소재 제작에 쓸만한지 검토
- citevue.com: 무료 AI 인용·AEO(AI 검색노출) 진단 - cheonoksystem.com에 한번 돌려볼 것
- 우선순위: 낮음, 다른 작업 끝난 뒤

## 6. 카카오톡 일일 리포트 (send_kakao_report 코드 작성 완료)
- JOS_MASTER.py에 send_telegram()을 미러링한 send_kakao_report() 함수 추가됨
  (카카오 "나에게 보내기" Memo API, https://kapi.kakao.com/v2/api/talk/memo/default/send)
- 집에서 할 일: 카카오 디벨로퍼스에서 앱 생성 -> REST API 키 발급 -> 카카오 로그인(talk_message 스코프)으로
  access_token 발급 -> CHEONOK_KAKAO_ACCESS_TOKEN 환경변수(GitHub Secrets)에 등록
- 주의: 카카오 access_token은 6시간 만료. refresh_token 자동 재발급 로직은 아직 미구현
  (토큰 만료되면 HOLD_KAKAO_SECRETS_MISSING으로 스킵, 텔레그램은 정상 발송)
