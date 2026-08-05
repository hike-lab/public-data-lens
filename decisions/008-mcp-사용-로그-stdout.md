# ADR-008: MCP 사용 로그 — stdout 구조화, 컨테이너 무쓰기 유지

- 상태: 채택 (2026-08-04)
- 날짜: 2026-08-04

## 맥락

웹/REST는 익명 사용 로그(usage-*.jsonl)가 있었지만 MCP는 접속 수준(게이트웨이)만
남고 Tool 단위 사용량이 없었다. 프로덕션 mcp 컨테이너는 read_only + 데이터 볼륨 :ro
("MCP는 어떤 쓰기도 하지 않는다")라 파일 로그가 구조적으로 불가능했다.

## 결정

**stdout JSONL 방식** — 파일 쓰기 대신 표준 출력으로 기록하고 수집·보존은 도커
로그 로테이션(기존 x-logging 10m×5)이 담당한다. 컨테이너 무쓰기 하드닝 불변.

- `_guard` 확장: Tool명·처리시간(ms)·오류 코드(스택트레이스 미기록)·0건 여부·질의
  원문(200자 캡, search/columns/plan만)을 `datanav.mcp.usage` 로거로 한 줄 JSON 기록.
- **익명 규칙은 REST와 단일 출처**(`api/usage.py` 신설): IP는 HMAC 일부만(원 IP
  미저장 — mcp는 볼륨 ro라 임시 키, 필요 시 DATANAV_ANON_HMAC_KEY로 api와 공유),
  **UA 원문 미저장 — 클라이언트 종류로 정규화**(claude/openai/claude-code/sdk/other,
  지문화 방지), 옵트아웃(DNT/GPC/X-Datanav-No-Log)이면 전부 미기록.
- 헤더·IP는 MCP SDK의 `request_ctx`(lowlevel contextvar)에서 취득 — Tool 시그니처
  불변(스펙 재생성 불필요). stdio·인메모리(테스트)에서는 빈 값으로 안전 강등.
- **uvicorn access log 차단**(api Dockerfile `--no-access-log`, mcp는 실행 전
  LOGGING_CONFIG 변조 — `disabled=True`는 uvicorn dictConfig가 되돌리는 것을 실측
  확인): 클라이언트 주소가 stdout에 남을 여지 제거.
- 게이트웨이: `/mcp`에 `X-Real-IP` 전달(+ mcp에 DATANAV_TRUST_PROXY=1) — 해시 후 폐기.
- **고지 v1.1**: MCP Tool 사용 로그 항목 신설, UA 정규화·MCP 옵트아웃 경로 명시.
  `/api/resources/privacy`가 v1.1을 서빙(v1.0 파일은 이력으로 보존).

## 함께 고친 결함

게이트웨이 `/api/`의 `limit_except GET`이 **POST /api/plan(계약 v1.5)을 405로
차단**하고 있었다 — `location = /api/plan`(POST 전용) 신설. 이 결함은 uvicorn 직결
테스트로는 잡히지 않았다(게이트웨이 경유 실측 항목으로 기억).

## 파악 가능 범위(정직 고지)

호출량 추이·Tool별 분포·클라이언트 종류별 분포·0건 비율·오류율·질의 유형은 측정
가능. **순 사용자 수는 불가** — 원격 커넥터(Claude·ChatGPT)는 벤더 인프라 IP로
호출이 오므로 anon 해시는 사용자 단위가 아니다(무인증 공개 MCP의 본질).

## 기각한 대안

- 파일 로그 + mcp 볼륨 쓰기 완화: 무쓰기 하드닝 축소 — 이득 없이 표면 증가.
- UA 원문 저장: 지문화 소지 — "브라우저 지문 미수집" 고지와 충돌.
- 인증 도입으로 사용자 식별: "인증 없이 무료" 공개 원칙과 충돌.
