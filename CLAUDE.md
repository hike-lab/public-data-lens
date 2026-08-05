# CLAUDE.md

공공데이터 렌즈(Public Data Lens) — 중앙대학교 HIKE 연구실. 공공데이터포털 월간 목록을
정본 JSON-LD로 정규화하고 버전 관리되는 판정 규칙으로 탐색·판단 계층을 제공한다.
AIRD(AI-Ready Data) 표준안의 독립적 선행 구현(의존 방향은 렌즈 → 표준).

공개 저장소다 — 커밋·문서는 공개를 전제로 쓴다. 원본 CSV·카탈로그 산출물·관측 DB는
커밋하지 않는다(`data/`는 gitignore, 파이프라인으로 재생성).

## 구조

```
apps/server    FastAPI. REST(/api/*) + MCP + 정본 URI 디레퍼런싱. 판정 로직 전부
apps/web       React 18 + Vite. 표현 계층만
apps/gateway   nginx real-ip
docs/          설계서·부속명세·매핑표·배포·호환성·개인정보 고지
```

## 설계 문서 (작업 전 확인)

| 문서 | 내용 |
|---|---|
| `DESIGN.md` | 웹 표면의 제품 설계 원칙 |
| `docs/UI_IMPLEMENTATION_GUIDE.md` | 필드 매핑·컴포넌트 계약·Phase·DoD |
| `docs/부속명세_v1.0.md` | Tool별 JSON Schema + 공통 계약 |
| `apps/server/datanav/spec/tool-schemas-v1.7.0.json` | **enum·필드의 정본** |

UI 작업 시 `DESIGN.md`와 `docs/UI_IMPLEMENTATION_GUIDE.md`를 먼저 읽는다.
문서와 계약이 어긋나면 계약이 이긴다.

## 책임 분리 (설계서 §2)

재현되어야 하는 판정은 **서버**가 결정론적으로 수행한다. 목적 의존적 해석은 호스트 LLM이
한다. 프론트엔드는 표현만 한다.

## 불변식

1. **프론트엔드에 새로운 점수를 만들지 않는다** — readiness, quality, suitability, 종합
   적합도. 계약은 `kdp:qualityTier`·`kdp:diagnosticMaturity`를 `null` 고정으로 명시한다.
2. **판정 임계값을 프론트엔드에서 정하지 않는다** — `topPercent <= 10` 같은 컷오프.
3. **서버가 준 값을 변형하지 않는다** — `region.name`을 정규식으로 자르는 등.
4. **서버 경고 문안을 치환하지 않는다** — `warnings[]` 원문을 툴팁으로 밀어내지 않는다.
5. **문자열 패턴으로 계약 의미를 추론하지 않는다** — `ranking.method.includes('bm25')` 등.
6. **백엔드 로직을 프론트엔드에서 재구현하지 않는다** — 질의→필터 해석은 서버
   `plan-assembly-v1.0`(`apps/server/datanav/api/plan.py`)에 이미 있다.
7. **모든 데이터 호출은 `apps/web/src/api.js`를 경유한다.** raw `fetch` 금지 —
   익명 로그 옵트아웃(DNT/GPC)과 오류 모델 언랩이 여기에 있다.
8. **`api.js`의 기존 메서드 시그니처를 바꾸지 않는다.** 메서드 추가는 허용.

## 계약 의미 — 위반하면 제품이 거짓말을 한다

```
NOT_COLLECTED / QUEUED / COLLECTING        수집 상태다. 품질 문제가 아니다
MISSING_FROM_SNAPSHOT                      관찰 사실이다. 폐기 확정이 아니다
                                           (폐기는 OFFICIALLY_WITHDRAWN만)
UNKNOWN (freshness)                        판단 불가다. 나쁨이 아니다
INFERRED_* (region)                        추론이다. 틀렸다는 뜻이 아니다
WITHHELD_BY_LICENSE / _SAFETY              정책적 보류다
검색 결과 없음                              데이터 부재가 아니다
search_by_columns 결과 없음                 컬럼 부재가 아니다 (미수집일 수 있음)
familyCandidate (UNREVIEWED)               자동 후보다. 확정된 계열이 아니다
LEGITIMATE_SPLIT                           정당한 분리다. 파편화가 아니다
계열 후보 존재                              문제 신호가 아니다
family 축 available=false                  미산출이다. 0건이 아니다
```

**색 규칙**: 위 항목에 실패색·경고색을 쓰지 않는다. 빨강·앰버는 `error.code` 9종,
`warnings[]`, `COLLECTION_FAILED`, `POSSIBLY_STALE`, `OFFICIALLY_WITHDRAWN`에만.

사용자는 문안보다 색을 먼저 읽는다.

## 백엔드 변경

additive만. 필드 추가는 minor. **required 제거·타입/의미 변경·오류코드 제거는 breaking이며
재승인이 필요하다.** 서버 변경 시 `scripts/gen_tool_spec.py` 재생성 +
`tests/test_contract_spec.py` 갱신 + `config.py`의 `SCHEMA_VERSION` 증가를 동반한다.

## 테스트·빌드

```
cd apps/server && python -m pytest -q          # 실패 0 기준
cd apps/web && npm run build                   # 라벨 가드(check-labels) 포함
cd apps/web && npx vitest run                  # 컴포넌트 단위 테스트
cd apps/web && npx playwright test --project=core-desktop   # 시각 베이스라인(darwin)
```

CSS·컴포넌트를 변경하기 전에 Playwright 시각 베이스라인과 대조한다. CI(darwin 아님)는
`SKIP_VISUAL=1`로 스크린샷 대조를 생략하고 스모크만 수행한다.

## 표면 분기

`VITE_SURFACE` = `core`(프로덕션, MCP 동반 웹) | `concierge` | `all`(로컬 기본).

AI 컨시어지는 별도 서비스이며 이 저장소에는 컨시어지 코드가 없다 —
**컨시어지 컴포넌트 부재가 정상 상태다.** `App.jsx`의 `import.meta.glob` 분기가
`ConciergeView.jsx` 부재 시 빈 객체를 반환해 표면 자체가 사라지므로, 부재 상태에서
`core`·`all` 모두 코어 화면만 렌더링한다. 컨시어지는 렌즈를 공개 MCP 계약을 통해서만
소비한다(특혜 접근 금지).

**웹과 컨시어지는 영구적으로 다른 시각 시스템을 쓴다.** 단 컴포넌트는 공유한다 —
컴포넌트가 팔레트 토큰을 직접 참조하지 않고 의미 토큰만 참조해야 한다.

## 축적 규칙

작업 산출물이 아니라 자산을 남긴다.

- **`glossary/`** — 새 개념의 정형 정의. YAML·JSON Schema 우선
- **`evals/`** — "이 입력이면 이 판정이 맞다" 형태의 케이스 쌍.
  `evals/results/**`는 미커밋(drift 리포트만 예외 — 응답 원문이 누적되기 때문)

버전 변경이나 구조 결정의 근거가 대화 속에서 증발하지 않게 즉시 기록한다.

## 언어

응답·문서·주석은 한국어. 스키마·코드·필드명은 영어.
