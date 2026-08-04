# UI_IMPLEMENTATION_GUIDE.md

> `DESIGN.md`를 구현 가능한 형태로 옮긴다. 원칙의 근거는 `DESIGN.md`에 있다.
>
> 이 문서의 모든 enum·필드명은 **`apps/server/datanav/spec/tool-schemas-v1.7.0.json`이 정본**이다.
> 문서와 계약이 어긋나면 계약이 이긴다. 어긋남을 발견하면 이 문서를 고친다.

---

# 1. 일반 규칙

프론트엔드는 **표현 계층**이다.

백엔드가 소유하는 것:

- 근거(`evidenceLevel`, `region.evidence`, `observation.provenance`)
- 상태(`coverageStatus`, `freshness.status`, change `status`, `exampleStatus`)
- 규칙 버전(`meta.ruleVersions[]`, `completeness.rule`, `cardRule`, `freshness.rule`)
- 완전성(`completeness.*`)
- 경고(`warnings[]`)와 오류(`error.code`)

## 금지

1. **새로운 품질·적합도 점수를 만들지 않는다.** readiness, quality, suitability, 종합 적합도 — 전부.
2. **판정 임계값을 프론트엔드에서 정하지 않는다.** `topPercent <= 10` 같은 컷오프는 계약에 없다.
3. **서버가 준 값을 변형하지 않는다.** `region.name`을 정규식으로 잘라내는 등. 표시 정책이
   필요하면 `labels.js` 단일 지점에서 하거나 서버 라벨을 요청한다.
4. **서버 경고 문안을 치환하지 않는다.** 다듬을 필요가 있으면 additive 필드를 요청한다.
5. **문자열 패턴으로 계약 의미를 추론하지 않는다.** `ranking.method.includes('bm25')`로 정렬
   방식을 유추하는 식. 계약에 방향 필드가 없으면 표시하지 않거나 additive를 요청한다.
6. **결정론적 판정을 프론트엔드에서 재구현하지 않는다.** 질의→필터 해석은 서버
   `plan-assembly-v1.0`에 이미 존재한다.

## 판단 기준

새 표시 항목을 만들 때 물어야 하는 질문: **"이 값을 어떤 응답 필드에서 읽는가?"**
답할 수 없으면 만들지 않는다.

---

# 2. API 매핑

## 2.1 정본과 빌드 시 검증

라벨 레지스트리는 `apps/web/src/labels.js` **한 곳**에만 둔다. 컴포넌트 파일 안에 로컬
라벨 상수를 두지 않는다.

**빌드 시 가드를 넣는다.** 계약 enum과 라벨 정의를 대조해 누락이 있으면 빌드를 실패시킨다.

```
계약 파일(tool-schemas-v1.7.0.json)에서 enum 추출
  → labels.js의 키와 대조
  → 누락 발견 시 빌드 실패
```

이 가드가 없으면 계약에 enum이 추가될 때 원시 코드가 사용자에게 노출된다. 현재
`COVERAGE_LABEL`이 10종 중 5종만 정의한 상태가 그 증상이다. `region.evidence`의
`UNKNOWN` 누락(`EVIDENCE_LABEL` 4/5)도 같은 증상이다 — 가드는 coverageStatus만이 아니라
§2.2~§2.10의 **닫힌 enum 전부**를 대조한다.

`license`는 계약에 열린 집합으로 정의되어 있다(`NO_RESTRICTION|KOGL_BY|… 등`). 여기만
폴백 라벨(`기타(원문 확인)`)을 허용하고, 나머지는 전부 닫힌 집합으로 취급한다.

## 2.2 근거 수준 — `evidenceLevel` (2종)

| 코드 | 라벨 | 의미 | 색 |
|---|---|---|---|
| `CATALOG_METADATA_ONLY` | 메타데이터 기준 | 포털 목록 기재 사항만. 실데이터 미확인 | 중립 |
| `FILE_OBSERVATION` | 실제 파일 구조 관측 | 파일에서 관측. 표본 한정, 전체 품질 미보증 | 강조 |

## 2.3 지역 근거 — `region.evidence` (5종)

| 코드 | 라벨 | 색 |
|---|---|---|
| `EXPLICIT_SPATIAL` | 공간범위 명시 | 강조 |
| `INFERRED_FROM_TITLE` | 제목 추론 | 중립 + "추론" 텍스트 |
| `INFERRED_FROM_PUBLISHER` | 기관명 추론 | 중립 + "추론" 텍스트 |
| `INFERRED_FROM_DESCRIPTION` | 설명 추론 | 중립 + "추론" 텍스트 |
| `UNKNOWN` | 지역 불명 | 중립 |

`confidence`(0~1)를 동반한다. **추론을 오류색으로 칠하지 않는다** — 틀렸다는 뜻이 아니다.

## 2.4 구조 수집 상태 — `coverageStatus` (10종)

| 코드 | 라벨 | 성격 | 색 |
|---|---|---|---|
| `AVAILABLE` | 구조 확인됨 | 정상 | 강조 |
| `PARTIAL` | 일부 파일만 확인 | 정상 | 강조(약) |
| `NOT_COLLECTED` | 아직 관측되지 않음 | 정상 — 수집 순번 | **중립** |
| `QUEUED` | 수집 대기 | 정상 | **중립** |
| `COLLECTING` | 수집 중 | 정상 | **중립** |
| `SOURCE_UNAVAILABLE` | 원본에 접근할 수 없음 | 정상 | **중립** |
| `UNSUPPORTED_FORMAT` | 지원하지 않는 형식 | 정상 | **중립** |
| `ACCESS_RESTRICTED` | 접근 제한 | 정상 | **중립** |
| `COLLECTION_FAILED` | 구조 수집 실패 | 실패 | 경고 |
| `API_STRUCTURE_NOT_SUPPORTED_YET` | API 구조는 차기 지원 | 정상 | **중립** |

`COLLECTION_FAILED` 하나만 경고색이다. **나머지 9종은 품질 문제가 아니다**(계약 명문).
`reason`·`failureReason` 필드가 있으면 함께 표시한다.

## 2.5 예시값 상태 — `exampleStatus` (6종) × `examplesPublic` (정책 플래그)

두 축은 별개다. `exampleStatus`는 **컬럼 단위** 수집·게이트 결과이고, `examplesPublic`은
**응답 최상위**의 배포 정책 플래그(발췌 제공 범위의 법적 확인 전 보수 모드)다.
화면 문안은 둘의 **조합**으로 결정하며, 조합 처리도 `labels.js` 단일 지점에 둔다 —
컴포넌트 인라인 분기 금지(현재 `DatasetProfile`의 'AVAILABLE → 비공개(정책)' 인라인
폴백이 이전 대상이다).

| `exampleStatus` | `examplesPublic: true` | `examplesPublic: false` | 색 |
|---|---|---|---|
| `AVAILABLE` | 예시값 표시 | "비공개(정책)" — 값 미표시 | 중립 |
| `NO_NON_NULL_VALUES` | 값 없음 | 값 없음 | 중립 |
| `WITHHELD_BY_LICENSE` | 라이선스 보류 | 라이선스 보류 | 중립 |
| `WITHHELD_BY_SAFETY` | 안전 비공개 | 안전 비공개 | 중립 |
| `NOT_COLLECTED` | 미수집 | 미수집 | 중립 |
| `COLLECTION_FAILED` | 수집 실패 | 수집 실패 | 경고 |

`examplesPublic: false`일 때는 컬럼별 문안과 별도로 **보수 모드임을 응답 단위로 한 번**
표기한다(서버 `warnings[]`에 동일 취지 문안이 이미 포함된다 — 치환하지 않는다).

## 2.6 최신성 — `freshness.status` (3종)

| 코드 | 라벨 | 색 |
|---|---|---|
| `FRESH` | 최신 | 강조 |
| `POSSIBLY_STALE` | 갱신 지연 가능 | 경고 |
| `UNKNOWN` | 최신성 판단 불가 | **중립** |

`ageDays`·`note`·`rule` 동반. `UNKNOWN`은 나쁨이 아니다.

## 2.7 변경 상태 — change `status` (6종)

| 코드 | 라벨 | 색 | 필수 부연 |
|---|---|---|---|
| `ADDED` | 신규 | 강조 | — |
| `MODIFIED` | 변경 | 중립 | `changedFields[]` 표시 |
| `MISSING_FROM_SNAPSHOT` | 스냅샷 부재 | **중립** | **필수** — 폐기 확정이 아님을 명시 |
| `REAPPEARED` | 재등장 | 중립 | 권장 |
| `POSSIBLE_IDENTITY_CHANGE` | 정체성 변경 의심 | 중립 | **필수** — 확인 필요 사유 |
| `OFFICIALLY_WITHDRAWN` | 공식 폐기 | 경고 | — |

`MISSING_FROM_SNAPSHOT`의 부연은 **툴팁이 아니라 화면 텍스트**로 제공한다. 오독의 결과가
크다(존재하는 데이터를 폐기로 오인).

## 2.8 목록 유형 — `listType` (3종)

`FILE` 파일 · `API` API · `STD` 표준. `profile`(완전성 프로파일)과 `distributionType`도 같은 집합.

## 2.9 갱신 주기 — `updateCycle` (8종)

`DAILY` 일간 · `WEEKLY` 주간 · `MONTHLY` 월간 · `QUARTERLY` 분기 · `SEMIANNUAL` 반기 ·
`ANNUAL` 연간 · `IRREGULAR` 수시 · `UNSPECIFIED` 미기재

## 2.10 오류 — `error.code` (9종)

| 코드 | 사용자 문안 방향 |
|---|---|
| `INVALID_ARGUMENT` | 입력 조건 문제. 무엇을 고치면 되는지 |
| `DATASET_NOT_FOUND` | 해당 데이터셋 없음. 스냅샷 교체 가능성 안내 |
| `SNAPSHOT_NOT_FOUND` | 조회 기준 스냅샷 부재 |
| `FILTER_NOT_AVAILABLE` | 해당 필터 미지원 |
| `TOO_MANY_DATASETS` | 비교는 최대 5개 |
| `INDEX_NOT_READY` | 색인 준비 중. 재시도 안내 |
| `SOURCE_VERSION_UNAVAILABLE` | 요청 버전 부재 |
| `RATE_LIMITED` | 요청 한도. 벌크 파일 안내 |
| `INTERNAL_ERROR` | 일시적 오류. 재시도 |

오류는 사과하지 않고 모호하지 않다. **무엇이 일어났고 무엇을 하면 되는지** 말한다.

## 2.11 계획 조립 — `build_data_plan` (v1.4.0)

Possible Uses 렌즈의 근거. **현재 MCP Tool 전용이며 REST 경로가 없다**(§12).

| 필드 | 값 |
|---|---|
| `planStatus` | `DRAFT` 고정 — 서버는 계획을 확정하지 않음 |
| `qualityAssessment` | `NOT_ASSESSED` 고정 |
| `possibleJoinKeys[].status` | `CANDIDATE_ONLY` 고정 — 결합 가능성 미확정 |
| `dataNeeds[].role` | `PRIMARY` 주 데이터 · `DEMAND` 수요 · `SUPPLY` 공급 · `SPATIAL` 공간 · `TEMPORAL` 시간 · `REFERENCE` 참조 |
| `dataNeeds[].status` | `SATISFIED` 충족 · `PARTIAL` 부분 충족 · `UNSATISFIED` 미충족 |
| `recommendedDatasets[].roles` | 위 6종 + `RELATED` 관련 |
| `fitSignals.searchRelevance` | `HIGH` · `MEDIUM` · `LOW` |
| `fitSignals.structureEvidence` | `FILE_OBSERVATION` · `STRUCTURE_NOT_COLLECTED` · `NOT_APPLICABLE` |
| `fitSignals.freshness` | `LISTED` 기재됨 · `UNKNOWN` |
| `interpretedPurpose.regionSource` | `PARAMETER` · `PURPOSE_TEXT` · `null` |

**`fitSignals`를 하나의 점수로 합치지 않는다.** 계약 주석이 이유를 명시한다:
"단일 점수는 과도한 확신을 만든다." 네 신호를 각각 표시한다.

`DRAFT`·`NOT_ASSESSED`·`CANDIDATE_ONLY`는 화면에 반드시 드러난다. 이 렌즈를 "추천"이나
"적합 데이터"로 부르지 않는다.

---

# 3. 홈페이지

각 블록은 **이미 존재하는 응답**으로 채운다. 괄호 안이 데이터 출처다.

| # | 블록 | 내용 | 데이터 출처 |
|---|---|---|---|
| 1 | **Hero** | 서비스 정의 1문장 + 검색 진입 | `/api/status` → `service.definition`, `counts.datasets` |
| 2 | **Real search** | 실제 동작하는 검색바. 키워드/컬럼 2모드 | `/api/search`, `/api/search/columns` |
| 3 | **Representative prompts** | 예시 질의 칩. 클릭 시 즉시 검색 실행 | 정적 문안 + 2번 호출 |
| 4 | **Live exploration** | 마운트 시 이미 받아둔 결과 상위 3~5건 노출 | `/api/search`(빈 질의, 최신 수정순) — **추가 왕복 없음** |
| 5 | **Dataset anatomy** | `structureAvailable: true` 레코드 1건의 실제 컬럼 표 | `/api/datasets/{id}/structure` → `assets[].tables[].columns[]` |
| 6 | **Coverage** | 분모를 반드시 함께 (§3.1) | `/api/status` → `counts.datasets`, `structureCoverage.*` |
| 7 | **Lens** | 렌즈 5종이 무엇에 답하는지 | 정적 + `/api/datasets/{id}` 실물 링크 |
| 8 | **MCP experience** | 커넥터 URL + 실제 호출 기록 | `/api/resources/spec/tools`, `/api/cases/{id}` → `toolTrace[]` |
| 9 | **Open infrastructure** | 판정 규칙·스키마·평가 지표 (§3.2) | `/api/status` → `service.rules[]` + `/api/resources/*` |

## 3.1 Coverage 블록 — 분모 규칙

세 숫자를 **함께** 보여준다. 사용자가 나눗셈을 하게 만들지 않는다.

```
목록 전체        counts.datasets                      예: 96,056
FILE 유형        structureCoverage.fileRecordsTotal   예: 83,695
구조 관측 확보    structureCoverage.recordsAvailable   예: 59,395
                → FILE의 71.0% / 전체의 61.8%
```

`API`·`STD` 유형은 구조 관측 대상이 아님을 명시한다
(`API_STRUCTURE_NOT_SUPPORTED_YET`).

**스냅샷 지연을 함께 표기한다.**

```
현재 스냅샷      currentSnapshot     예: 2026-06
배포 시각        deployedAt          예: 2026-08-03
릴리스           release
```

최신성을 판정하는 서비스가 자기 지연을 숨기면 §2 원칙 5 위반이다.

## 3.2 Open Infrastructure 블록

**전부 기존 라우트다. 백엔드 변경 없이 구현한다.**

| 항목 | 출처 | 표현 |
|---|---|---|
| 판정 규칙 레지스트리 전체 | `/api/status` → `service.rules[]` (`ruleId`, `title`) | 목록 — 개수는 `service.rules[].length`로 렌더(하드코딩 금지). 추가 왕복 없음 |
| 규칙 상세 | `/api/resources/rules` (`definition`, `effectiveDate`, `fields`) | 펼침 |
| Tool 스키마 | `/api/resources/spec/tools` | 링크 |
| JSON-LD Context | `/api/resources/context` | 링크 |
| SHACL | `/api/resources/shapes` | 링크 |
| Prompt 원문 | `/api/resources/prompts/build-data-plan` | 링크 |
| 개인정보·로그 고지 | `/api/resources/privacy` | 링크 |
| 검색 품질 지표 | `golden/eval_report.json` — **라우트 없음**(§12) | 추가 후 |

규칙 목록에 폐기된 규칙(`aird-mmi-v1.0`)이 포함된다. **숨기지 않고 폐기 표시한다** —
버전 관리되고 있다는 증거다.

규칙 **개수를 문서·UI에 하드코딩하지 않는다** — v1.4 기준 21종이며 계약이 자랄 때마다
늘어난다. 항상 `service.rules[].length`로 렌더한다.

---

# 4. 검색 결과

## 4.1 기본 레이아웃

`DatasetRow`. 카드는 특별 콘텐츠에만 쓴다(§7 Components).

| 열 | 필드 | L |
|---|---|---|
| 유형 | `listType` | L1 |
| 제목 | `title` | L1 |
| 제공기관 | `orgName` | L1 |
| 분류 | `theme.top` / `theme.sub` | L1 |
| 포맷 | `formats[]` | L1 |
| 수정일 | `modifiedDate` | L1 |
| 행 수 | `rowCountListed` | L1 |
| 구조 | `structureAvailable` → `CoverageIndicator` | L1 |
| 기재 사항 | `completeness.keyFields{spatial,temporal,dataLimits}` | L1 |
| 지역 | `regions[]{name,evidence,confidence}` → `EvidenceRow` | L1 |
| 원문 | `portalUrl` | L1 |
| 비교 선택 | (클라이언트 상태, 최대 5) | L1 |
| 일치 컬럼 | `matchedColumns[]{keyword,columns}` — 컬럼 검색 시만 | L1 |

## 4.2 완전성 표시 — 종합 점수를 쓰지 않는다

`completeness.score`는 판별력이 없다. FILE의 약 89%가 동일 값이며
(`typical: true`, `typicalShare`), 실제 차이는 `keyFields` 3필드에서 나온다.

**표시 방법**: 기재된 `keyFields`만 칩으로 노출(미기재가 기본값), 그리고
`filledFields`/`totalFields`를 옅게. `score`를 진행 막대로 그리지 않는다.

```
표시:      [공간범위 ✓] [기간 ✓]   기재 15/16
비표시:    ━━━━━━━━░░ 81%
```

`typical`·`topPercent`는 부연으로만 쓰고 **프론트엔드 임계값을 두지 않는다.**

## 4.3 결과 메타

| 표시 | 필드 |
|---|---|
| 총 건수 | `totalEstimate` |
| 정렬 방식 | `ranking.method` / `.version` — **문자열 패턴으로 추론하지 않는다**(§12) |
| 색인 버전 | `ranking.indexVersion` (L3) |
| 동순위 처리 | `ranking.tieBreak` (L3) |
| 컬럼 검색 모집단 | `coverage.searchedRecords` / `coverage.fileRecordsTotal` |

`score`(BM25 음수)는 화면에 노출하지 않는다. 방향이 계약에 없어 오독을 만든다.

**필터 옵션은 계약 enum 전체를 덮는다.** 현재 주기 필터가 `updateCycle` 8종 중 7종만
제공해 `UNSPECIFIED`(미기재)로 필터할 수 없다. 미기재는 이 카탈로그에서 드물지 않은
상태라 필터 가치가 있다 — 닫힌 enum 필터(유형·주기 등)는 전 항목을 노출하며, 이 완결성도
§2.1 빌드 가드의 대조 대상에 포함한다.

## 4.4 페이징

키워드 검색은 `nextCursor` + `hasMore`로 커서 페이징. **컬럼 검색에는 커서가 없다** —
`pageSize` 상한까지만 반환되며, 이 한계를 화면에 명시한다. 조용히 끊지 않는다.

## 4.5 빈 결과

```
✗  "조건에 맞는 데이터를 찾지 못했습니다"                    ← 데이터 부재로 읽힌다
✓  "이 조건으로는 결과가 없습니다.
    조회 범위: 2026-06 스냅샷 96,056건
    (컬럼 검색은 구조가 관측된 59,395건 내에서만 찾습니다)
    → 키워드를 줄이거나 필터를 해제해 보세요"
```

빈 결과는 방향을 준다. 컬럼 검색의 경우 **모집단 한계를 반드시 함께** 말한다 —
결과에 없다고 컬럼이 없는 것이 아니다(계약 명문).

---

# 5. 데이터셋 상세

## 5.1 렌즈 구성

`LensNavigation`이 렌즈 5종을 담는다. 기술 표현은 접힘 격리였다가 '원본 데이터'
렌즈로 승격했다(2026-08-04).

```
렌즈:     Overview | Structure | Evidence | Possible Uses* | Raw(원본 데이터)
                                          * REST 경로 추가 후
```

## 5.2 Overview 렌즈

| 항목 | 필드 |
|---|---|
| 제목·기관·유형 | `title`, `orgName`, `listType` |
| 속성 | `theme`, `formats`, `updateCycleRaw`, `license.raw`, `createdDate`, `modifiedDate` |
| 공간·시간 범위 | `spatial`, `temporal` (미기재 시 "미기재") |
| 행 수 | `rowCount` |
| 기재 사항 체크리스트 | `completeness.fields{}` (필드별 boolean) |
| 최신성 | `freshness{status,ageDays,note}` |
| 기관 기재 한계 | `dataLimits` |
| 설명·키워드 | `description`, `keywords[]` |
| 포털 | `portal{listKey,orgName,listUrl,listBaseDate,analyzedAt}` |

## 5.3 Structure 렌즈

| 항목 | 필드 |
|---|---|
| 수집 상태 | `coverageStatus` + `reason` |
| 근거 수준 | `evidenceLevel` (= `FILE_OBSERVATION`) |
| 파일 커버리지 | `coverage{availableAssets,totalAssets}` |
| 예시값 정책 | `examplesPublic` |
| 파일 | `assets[]{fileName,containerName,format,shape,status,failureReason}` |
| 관측 정보 | `observation{observedAt,provenance,scanScope,licenseGate}` |
| 표 | `tables[]{sheetName,rowsScanned,rowCountObserved,columnCount,scanScope}` |
| 컬럼 | `columns[]{ordinal,sourceName,observedType,distinctCount,distinctApprox,exampleStatus,safetyStatus,examples,exampleMethod,note}` |

`sourceName`은 **원본 컬럼명 그대로**다. 번역·정규화하지 않는다.
`rowsScanned`(스캔 행수)와 `rowCountObserved`(관측된 전체 행수)를 구분해 표시한다.

## 5.4 Evidence 렌즈

**신규 필드 없이 기존 값 조합으로 구성된다.** 이 렌즈가 §2 원칙 2와 시그니처를 구현한다.

| 항목 | 필드 |
|---|---|
| 근거 수준 | `evidenceLevel` |
| 판정 스냅샷 | `meta.sourceSnapshot`, `meta.processedAt` |
| 적용 규칙 | `meta.ruleVersions[]` |
| 카드 재구성 규칙 | `cardRule` |
| 완전성 규칙 | `completeness.rule` + `profile` |
| 최신성 규칙 | `freshness.rule` |
| 지역 판정 | `regions[]{evidence,confidence}` |
| 구조 관측 출처 | `observation{provenance,scanScope,observationId}` |
| 스키마 버전 | `meta.schemaVersion` |
| 서버 경고 | `warnings[]` |

`DatasetProfile`의 `evidence-note`는 현재 문장이 하드코딩되어 있다. `evidenceLevel` 값에서
도출하도록 바꾼다.

## 5.5 Possible Uses 렌즈 (REST 경로 추가 후)

| 항목 | 필드 |
|---|---|
| 초안 표시 | `planStatus: DRAFT` — **항상 노출** |
| 품질 미평가 | `qualityAssessment: NOT_ASSESSED` — **항상 노출** |
| 해석된 목적 | `interpretedPurpose{searchTerms[],regionApplied,regionSource,iterationsUsed}` |
| 데이터 요구 | `dataNeeds[]{role,need,status,matchedRecordIds,reason}` |
| 후보 | `recommendedDatasets[]{recordId,title,roles,fitSignals,whySelected,limitations}` |
| 예상 결합 키 | `possibleJoinKeys[]` — `CANDIDATE_ONLY` 명시 |
| 미충족 | `missingNeeds[]` |
| 다음 확인 | `nextChecks[]` |

`fitSignals` 4개를 각각 표시한다. 합치지 않는다.

## 5.6 원본 데이터 렌즈 (구 접힘 영역)

`view=normalized` / `source` / `jsonld`. 현재 `JSON.stringify`로 던지고 있다.
최소 처리 후보: 필드명 검색, 복사 버튼, `view` 별 1줄 설명.

접힘(L3) 격리에서 렌즈로 승격했다(2026-08-04). 판정을 덧붙이지 않는
서버 표현 원문이라는 성격은 유지한다.

---

# 6. 진행적 공개

| 층 | 내용 | 기본 상태 |
|---|---|---|
| **L1** | 제목·기관·유형·포맷·수정일·행수·기재 사항·지역·구조 유무 | 펼침 |
| **L2** | 속성 전체·설명·기관 기재 한계·컬럼 구조·예시값·수집 상태·정규화 원본·원본 CSV·JSON-LD | 렌즈 진입 시 |
| **L3** | 규칙 버전·색인 버전·관측 ID | 접힘 |

규칙: **L3의 존재는 L1에서 보여야 한다.** 근거를 열 수 있다는 사실 자체가 신뢰 요소다.
"근거 보기" 진입점을 L1에 둔다.

한 번에 전부 펼치지 않는다.

---

# 7. 컴포넌트

각 컴포넌트는 독립 테스트를 갖는다.

## DatasetRow

```
props:  item(summaryItem), onOpen, compared, compareFull, onToggleCompare
필드:   §4.1 전체
금지:   점수 막대, 프론트엔드 임계값
접근성: 행 전체가 키보드 도달 가능. div+onClick 금지
```

## EvidenceRow

```
props:  level(evidenceLevel), rules(string[]), snapshot, regions?, observation?
용도:   근거 표기의 단일 지점. §5.4의 모든 항목이 이 컴포넌트를 거친다
현상태: DatasetCardRow의 지역 배지, DatasetProfile의 evidence-note,
        StructureView의 obs-meta에 흩어져 있다 → 통합
```

## CoverageIndicator

```
props:  status(coverageStatus), available?, total?, reason?, examplesPublic?
        또는 searchedRecords/fileRecordsTotal (검색 모집단 모드)
규칙:   분모 없이 표시하지 않는다. 미수집을 실패로 칠하지 않는다
현상태: 3곳에 다른 형태로 존재 → 통합
```

## LensNavigation

```
props:  lenses(available), active, onChange
규칙:   백엔드가 지원하는 렌즈만 노출. L3 뷰를 포함하지 않는다
접근성: role="tablist" + 자식 role="tab" + aria-selected 완비.
        tablist만 선언하고 tab이 없는 현 상태는 없는 것보다 나쁘다
```

## ExplorationTrail

```
props:  (라우터 히스토리에서 도출)
전제:   라우팅 필요. 현재 App.jsx의 useState('search') 구조에서는 구현 불가
용도:   "왜 이것을 보고 있는가"의 경로 — 질의 → 결과 → 데이터셋 → 렌즈
```

## WarningPanel

```
props:  warnings(string[]), error?
규칙:   서버 문안을 치환하지 않는다. 툴팁에만 두지 않는다
현상태: 7개 파일이 startsWith('본 결과는') 필터를 복제(개발 저장소 기준,
        컨시어지 2종 포함 — 공개 스냅샷 기준 5개). 서버 DISCLAIMER 문안에
        문자열로 결합된 상태 → 전부 단일화(§12)
```

## SourceBadge

```
props:  kind('portal'|'observation'|'rule'), value, href?
용도:   출처의 최소 표기
```

## Timeline

```
props:  snapshots, current, base?
용도:   변경 이력·스냅샷 관계. baseSnapshot이 null인 상황을 표현할 수 있어야 한다
```

---

# 8. 접근성

WCAG 2.1 AA. **DoD 항목이며 마지막 Phase로 미루지 않는다.**

## 8.1 현재 확인된 실패 — 우선 처리

| 항목 | 현상 | 기준 |
|---|---|---|
| 결과 행 조작 | `div className="card-main" onClick` — `tabIndex`·`role`·`onKeyDown` 없음. **키보드로 상세를 열 수 없다** | 2.1.1 |
| 모달 | drawer에 `role="dialog"`·`aria-modal` 없음. Escape 없음. 포커스 트랩·복귀 없음 | 2.4.3 / 4.1.2 |
| 포커스 표시 | 여러 곳 `outline: none`, 일부는 대체 없음 | 2.4.7 |
| ARIA | `role="tablist"` 선언 + 자식 `role="tab"`·`aria-selected` 부재 | 4.1.2 |
| 툴팁 전용 정보 | 계약 경고 원문이 `title`에만 존재 | 1.3.1 |

## 8.2 체크리스트

- 모든 인터랙티브 요소가 키보드로 도달·조작 가능
- 포커스 링이 항상 보임 (`:focus-visible`, 배경 대비 3:1 이상)
- 모달: `role="dialog"` + `aria-modal="true"` + 포커스 트랩 + Escape + 닫을 때 포커스 복귀
- 탭: `role="tablist"` / `role="tab"` / `aria-selected` / 화살표 키 이동
- 색만으로 상태를 전달하지 않음 — **모든 상태 배지에 텍스트 병기**
- 표: `<th scope>`, 캡션. 가로 스크롤 컨테이너에 `tabindex="0"`
- 비동기 결과: `aria-live="polite"`로 건수 변화 안내
- 대비: 본문 4.5:1, 큰 텍스트 3:1
- `prefers-reduced-motion: reduce` 준수
- 확대 200%에서 콘텐츠 손실 없음
- 폼: 모든 입력에 연결된 라벨 (placeholder는 라벨이 아니다)

---

# 9. 반응형

| 계층 | 폭 | 처리 |
|---|---|---|
| Desktop | ≥ 1024px | 전체 열 |
| Tablet | 640–1023px | 부차 열 접힘 (행수·색인 버전) |
| Mobile | < 640px | `DatasetRow`가 세로 스택 |

**브레이크포인트를 통일한다.** 현재 760 / 720 / 640px 세 값이 혼재한다.

컨테이너 폭이 현재 980px이다. 밀도 높은 행을 수용하려면 재검토가 필요하다.

표는 가로 스크롤 컨테이너에 담고 스크롤 가능함을 시각적으로 알린다.

---

# 10. 구현 단계

## Phase 0 — 전제 (코드 변경 없음)

| 작업 | 대상 |
|---|---|
| 문서 등재 | `DESIGN.md`, `docs/UI_IMPLEMENTATION_GUIDE.md` |
| 시각 회귀 베이스라인 | Playwright 스크린샷. **Phase 1 착수 조건** |
| 배포 격차 해소 | 라이브 `schemaVersion 1.3.0` vs 저장소 `1.4.0` |

베이스라인 없이 Phase 1을 시작하지 않는다. 웹 테스트가 0개이고 브랜드 토큰이 30여 곳에서
의미 역할을 겸하고 있어 되돌릴 근거가 없다.

## Phase 1 — 토큰·타이포

| 파일 | 작업 |
|---|---|
| `src/styles.css` | 3층 분리(§7 DESIGN). 팔레트/의미/컴포넌트 |
| `src/styles.concierge.css` (신규) | `.cz-*` 분리. 해당 표면에서만 로드 |
| `src/App.jsx` | 시각 분기와 기능 분기(concierge 유무) 분리 |
| `index.html` | 폰트 조달, `meta description`, `og:*`, `canonical`, `color-scheme` |

영향: 전 화면. 최대 위험. 시각 결과 불변을 목표로 한다.

## Phase 2 — 홈

| 파일 | 작업 |
|---|---|
| `components/SearchView.jsx` | Hero, Live Exploration(§3 #4) |
| `components/AboutView.jsx` | Coverage(§3.1), Open Infrastructure(§3.2) |
| `components/CoverageIndicator.jsx` (신규) | — |
| `labels.js` | 라벨 통합 + 빌드 가드(§2.1) |

서버 왕복 증가 없음.

## Phase 3 — 검색

| 파일 | 작업 |
|---|---|
| `components/DatasetCardRow.jsx` → `DatasetRow.jsx` | 개명 + `card-*` 클래스 어휘 교체 |
| `components/EvidenceRow.jsx` (신규) | — |
| `components/WarningPanel.jsx` (신규) | 5곳 중복 제거 |
| `components/SearchView.jsx` | 빈 결과(§4.5), 페이징 한계(§4.4), 결과 메타(§4.3) |
| `components/ChangesView.jsx` | 클래스 어휘, `MISSING_FROM_SNAPSHOT` 부연 본문화 |

`card-*` 개명 시 `ChangesView`·`CasesView`·`styles.css`를 함께 잡는다. 고아 컴포넌트를
빠뜨리기 쉽다.

## Phase 4 — 상세

| 파일 | 작업 |
|---|---|
| `components/DatasetProfile.jsx` | 분할. 렌즈/L3 분리 |
| `components/LensNavigation.jsx` (신규) | — |
| `components/EvidenceLens.jsx` (신규) | §5.4 |
| `App.jsx` | 라우팅 도입 시 구조 변경 |

## Phase 5 — MCP·계획

| 파일 | 작업 |
|---|---|
| `components/ConnectView.jsx` | Tool 수 정정, `toolTrace` 전시, `MCP_URL` 환경변수화 |
| `components/PossibleUsesLens.jsx` (신규) | REST 경로 추가 후 |
| `api.js` | `plan()` 메서드 추가 |

## Phase 6 — 접근성·회귀

| 파일 | 작업 |
|---|---|
| 전 컴포넌트 | §8 체크리스트 |
| `package.json` | `test` 스크립트 |
| `.github/workflows/ci.yml` | web job에 테스트 추가 (현재 build만) |

§8.1의 확인된 실패 5건은 **Phase 6까지 미루지 않고 발견 시점에 처리한다.**

---

# 11. Definition of Done

## 계약 준수

- 화면의 모든 상태·근거 표시가 응답 필드에서 직접 온다
- 프론트엔드에 새로운 점수·임계값·판정이 없다
- 계약 enum 전체에 라벨이 정의되어 있고, 빌드 가드가 누락을 잡는다
- 서버 경고 문안이 치환되지 않는다
- `api.js`의 8개 메서드 시그니처가 유지된다
- 모든 데이터 호출이 `api.js`를 경유한다 (raw `fetch` 금지)
- 기존 REST·MCP 계약이 변경되지 않았거나, additive만 추가되었다

## 근거 표현

- 모든 판정에 근거가 붙는다
- 미수집·불명·보류가 실패로 표현되지 않는다
- `MISSING_FROM_SNAPSHOT`이 폐기로 읽히지 않는다
- 결과 부재가 데이터 부재로 읽히지 않는다
- 커버리지가 분모와 함께 표시된다
- 스냅샷과 지연이 화면에 있다
- 툴팁에만 존재하는 정보가 없다

## 품질

- §8 체크리스트 전 항목 통과
- Playwright 회귀 통과
- CI web job이 빌드와 테스트를 모두 수행
- 세 반응형 계층에서 콘텐츠 손실 없음
- 배포되지 않은 기능을 광고하지 않는다
- 자리표시자 AI 기능이 없다

---

# 12. 백엔드 additive 요청 목록

기존 required·타입·오류코드를 건드리지 않는 minor 변경만.

| 요청 | 목적 | 참조 |
|---|---|---|
| `POST /api/plan` — `build_plan()` 래핑 | Possible Uses 렌즈. **로직은 이미 존재**하며 MCP 전용이다 | §5.5 |
| `ranking.direction` 또는 정규 `rank` | 정렬·관련도 표시 시 문자열 추론 제거 | §4.3 |
| `notices[]{code,severity,text}` (기존 `warnings[]` 유지) | `startsWith('본 결과는')` 문자열 결합 제거 | §7 WarningPanel |
| `/api/search` → `interpretedFilters[]{field,value,sourceToken,ruleId}` | 질의 해석 서버 이관. 서버 `plan.py`에 `REGION_CODES`가 이미 있고 `plan-assembly-v1.0`으로 버전 관리된다 | §1 금지 6 |
| `/api/stats?axis=regionEvidence` | `EXPLICIT_SPATIAL` 대비 `INFERRED_*` 실제 비중 | §2.3 |
| `/api/changes` → `baseUnavailableReason` | `baseSnapshot: null` · `counts.changes: 0`을 고장으로 오인하지 않게 | §7 Timeline |
| `/api/status` → `snapshotLagDays` | 지연을 서버 사실로 (프론트 계산 회피) | §3.1 |
| `/api/resources/eval` | 검색 품질 지표 공개 | §3.2 |
| `summaryItem.evidenceLevel` | 목록에서 상세 조회 없이 근거 수준 표시 | §4.1 |

서버 변경 시 `gen_tool_spec.py` 재생성 + `test_contract_spec.py` 갱신 + `SCHEMA_VERSION`
minor 증가를 동반한다.

## 요청하지 않는 것

`readiness` · `qualityTier` · `suitabilityScore` · 종합 적합도. 계약이 `kdp:qualityTier`와
`kdp:diagnosticMaturity`를 `null` 고정으로 명시하며, 이 제품은 확정하지 않는 것을
확정하지 않는다.
