# Claude Desktop ↔ cheonoksystem 저장소 연동 가이드

## 목적
집 노트북의 Claude Desktop 앱에서 이 저장소(cheonoksystem)를 직접 읽고/수정하고,
git 상태 확인·커밋까지 다룰 수 있게 한다. (현재 Claude Code 클라우드 세션에서
하던 파일 읽기/쓰기를 노트북의 Desktop GUI에서도 가능하게)

## 0. 사전 준비
- Node.js 설치 (filesystem MCP 서버용, `npx` 사용) - https://nodejs.org
- Python + uv 설치 (git MCP 서버용, `uvx` 사용) - https://docs.astral.sh/uv/
- Claude Desktop 앱 설치

## 1. 저장소 로컬 클론
```
git clone https://github.com/actorlee007-cmyk/cheonoksystem.git
cd cheonoksystem
git checkout claude/stock-trading-media-check-pc85lu   # 현재 작업 브랜치, 또는 main
```

## 2. Claude Desktop 설정 파일 위치
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

파일이 없으면 새로 만들고, 있으면 `mcpServers` 객체 안에 아래 키들만 추가한다
(다른 MCP 서버 설정이 이미 있으면 그 옆에 추가 - 통째로 덮어쓰지 말 것).

## 3. MCP 서버 설정 추가
```json
{
  "mcpServers": {
    "cheonoksystem-fs": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/절대/경로/cheonoksystem"]
    },
    "cheonoksystem-git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "/절대/경로/cheonoksystem"]
    }
  }
}
```
- `/절대/경로/cheonoksystem`을 1단계에서 클론한 실제 절대경로로 교체
  - Windows는 `C:\\Users\\이름\\cheonoksystem` 처럼 백슬래시 두 번
- `cheonoksystem-git`이 실행 안 되면(패키지 이름이 바뀌었을 수 있음) 일단 `cheonoksystem-fs`만
  쓰고 git 명령은 터미널에서 직접 실행해도 됨 - filesystem 연동이 핵심이고 git은 보조

## 4. 적용 및 확인
1. Claude Desktop 완전 종료 후 재시작
2. 새 대화 시작 → 도구/MCP 아이콘에 `cheonoksystem-fs`(, `cheonoksystem-git`) 표시되는지 확인

## 5. 테스트 프롬프트
- "cheonoksystem 저장소의 automation/personal_ops/home_todo.md 읽어줘"
- "git status 보여줘" (git 서버 연결됐으면)
- 파일 일부 수정 요청 → "git diff 보여줘"로 변경 확인
- 커밋/푸시는 직접 확인 후 진행 권장 (Claude Desktop이 바로 push하지 않도록 주의)

## 주의사항
- filesystem 서버는 지정한 폴더 내부만 접근 가능 (다른 경로 접근 불가 - 안전장치)
- git push는 로컬에 git 자격증명(SSH 키 또는 HTTPS 토큰)이 설정되어 있어야 동작
- 이 클라우드 Claude Code 세션과 노트북의 로컬 클론은 별도 워킹트리.
  서로 자동 동기화되지 않으며, git push/pull로만 맞춰진다.
  → 노트북에서 작업한 내용은 push, 다음 클라우드 세션 시작 전 git pull 권장

## home_todo 항목 1과의 연결
- 운전 중 떠오른 아이디어 → 모바일에서 메모 → 집 도착 후 Claude Desktop +
  cheonoksystem-fs/git MCP로 직접 정리/실행하는 흐름의 "로컬 실행" 축을 이 설정으로 해결.
- Cowork(항목 1 참고 영상, 5q5ZUpwgj4E)는 이 연동과 별개 검토 대상 - 이 MCP 연동만으로도
  "노트북에서 이 저장소 작업"은 충분히 가능해짐.
