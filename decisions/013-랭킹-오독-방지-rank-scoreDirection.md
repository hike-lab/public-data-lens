# ADR-013: 검색 순위 오독 방지(rank·scoreDirection) + evals 첫 실체화

- 상태: 채택 (계약 버전: 미배포 v1.8.0에 합류 — ADR-014 배포 트레인 동결의 첫 적용.
  초안은 v1.9.0 신설이었으나 v1.8.0이 아직 서빙된 적 없어 합류로 개정, 2026-08-08)
- 날짜: 2026-08-08
- 관련: ADR-004(v1.5 — `ranking.direction`·`basis` 노출, 프론트 문자열 추론 제거),
  ADR-010(evals/ 자산 소유·출처 규정), ADR-012(llms.txt — BM25 상대값 주의 문안 선반영),
  ADR-014(계약 버전 정책)

## 맥락

검색 점수는 SQLite FTS5 `bm25()` 값이다 — **낮을수록(음수로 클수록) 상위**이며, 일반
BM25의 "높을수록 좋음" 직관과 반대다. 실제 응답에서 score −17.31이 −16.29보다 상위다.

v1.5의 `ranking.direction`(asc|desc)은 프론트엔드의 문자열 패턴 추론을 제거했지만,
**호스트 LLM의 score 수치 오독**이라는 원래 위험은 남았다. 오히려 `direction: "desc"`
(개념적 관련도 기준의 방향)를 score 수치에 적용하면 "큰 값이 먼저"라는 오독이 강화된다.
MCP의 주 소비자가 호스트 LLM인 이상, 이 오독은 사용자에게 하위 결과를 최상위로
보고하는 실질 오류로 이어진다.

## 결정

additive 확장으로 두 사실을 응답에 명시한다. 버전 번호는 신설하지 않고 **미배포
v1.8.0에 합류**한다(ADR-014).

1. **`items[].rank`** (integer, 1=최상위) — 서버 정렬에서의 절대 순위. 커서 오프셋을
   반영하므로 페이지를 넘어도 절대 순위다. **순위 판단의 정본은 rank이며**, score의
   부호·크기 해석과 무관하다. 질의 유무와 무관하게 항상 존재한다.
2. **`ranking.scoreDirection`** (enum `LOWER_IS_MORE_RELEVANT` | `NOT_APPLICABLE`) —
   `items[].score`의 해석 방향. score 부재(질의 없음) 시 `NOT_APPLICABLE`.
   `sort=modified`여도 score 값 자체의 의미는 동일하므로(정렬 기준은 `basis`가 말한다)
   score가 있으면 `LOWER_IS_MORE_RELEVANT`다.
3. `search_datasets` Tool 설명에 같은 사실을 명기한다(스키마를 읽지 않는 호스트 대비).
4. `HIGHER_IS_MORE_RELEVANT`는 enum에 **넣지 않는다** — 현행 구현에 그 값을 내는 경로가
   없고, 계약 enum은 실제로 발생 가능한 값만 담는다(발생 불가 값은 소비자 분기만 늘린다).
   랭킹 방법이 바뀌어 필요해지면 additive enum 확장으로 대응한다.

### evals 첫 실체화 (ADR-010 이행 개시)

이 오독은 "이 입력이면 이 판정이 맞다" 케이스의 전형이므로, 계획으로만 있던 evals
구조를 이 변경과 함께 실체화한다.

- `evals/schema/case.schema.json` — 케이스 정형(스키마): id·concept·given·correct·
  misreadings·provenance(source enum에 ADR-010 §4의 `concierge_derived` 포함).
- `evals/cases/ranking-bm25-direction-001.json` — 첫 케이스: −17.31 vs −16.29 중
  상위 판별.
- `tests/test_eval_cases.py` — 케이스-스키마 정합 가드(자산 오염 방지).
- 부재·미수집 오독 5종 등재는 P2로 후속(NOT_COLLECTED≠품질문제 등).

## 절차 준수

- `tool-schemas-v1.8.0.json` 재생성(라이브 검증 통과) — 미배포 버전이므로 같은 번호에
  누적(ADR-014). 수용 테스트 추가.
- required에 넣지 않는다(v1.5 direction·basis 전례) — 구버전 응답과의 additive 호환.

## 결과

- 호스트 LLM이 score 방향을 스스로 추론할 필요가 없어진다 — rank가 정본, scoreDirection이
  보조 사실. llms.txt(ADR-012)의 주의 문안과 삼중 방어가 된다.
- 배포는 v1.8.0 트레인을 탄다(ADR-011 게이트) — 계열 후보와 함께 나간다.
