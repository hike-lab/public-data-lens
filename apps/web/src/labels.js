// 정규화 코드의 사용자 표시 라벨 — 단일 레지스트리(가이드 §2.1).
// 코드(계약값)는 그대로 두고 표시만 한글화한다. 컴포넌트 파일에 로컬 라벨 상수를 두지 않는다.
// 닫힌 enum의 커버리지는 빌드 가드(scripts/check-labels.mjs)가 계약 스펙과 대조한다.

// §2.9 갱신 주기 (8종)
export const UPDATE_CYCLE_LABEL = {
  DAILY: '일간', WEEKLY: '주간', MONTHLY: '월간', QUARTERLY: '분기',
  SEMIANNUAL: '반기', ANNUAL: '연간', IRREGULAR: '수시', UNSPECIFIED: '미기재',
}

// 열린 집합 — 유일하게 폴백 라벨 허용(가드 제외)
export const LICENSE_LABEL = {
  NO_RESTRICTION: '제한 없음',
  KOGL_BY: '공공누리 1유형(출처표시)',
  KOGL_BY_NC: '공공누리 2유형(상업적 이용 금지)',
  KOGL_BY_ND: '공공누리 3유형(변경 금지)',
  KOGL_BY_NC_ND: '공공누리 4유형(상업적 금지·변경 금지)',
  OTHER: '기타(원문 확인)',
  UNSPECIFIED: '미기재',
}

// §2.7 변경 상태 (6종)
export const CHANGE_STATUS_LABEL = {
  ADDED: '신규',
  MODIFIED: '변경',
  MISSING_FROM_SNAPSHOT: '스냅샷에서 확인되지 않음',
  REAPPEARED: '재등장',
  POSSIBLE_IDENTITY_CHANGE: '동일 데이터 여부 확인 필요',
  OFFICIALLY_WITHDRAWN: '공식 폐기',
}

// 상태 의미의 오해를 막는 부연(§2.7: 스냅샷 부재 ≠ 폐기) — 툴팁이 아니라 본문에 쓴다
export const CHANGE_STATUS_NOTE = {
  MISSING_FROM_SNAPSHOT:
    '이번 스냅샷에서 관찰되지 않았다는 사실 기록입니다 — 폐기 확정이 아닙니다(폐기는 "공식 폐기"로만 표기).',
  POSSIBLE_IDENTITY_CHANGE:
    '제목·기관 등이 크게 달라져 같은 데이터셋인지 확인이 필요합니다(기관 개편·명칭 변경일 수 있음).',
  REAPPEARED: '이전 스냅샷에서 부재였다가 다시 관찰되었습니다.',
}

// §2.3 지역 근거 (5종) — 추론은 중립이며 틀렸다는 뜻이 아니다
export const EVIDENCE_LABEL = {
  EXPLICIT_SPATIAL: '공간범위 명시',
  INFERRED_FROM_TITLE: '제목 추론',
  INFERRED_FROM_PUBLISHER: '기관명 추론',
  INFERRED_FROM_DESCRIPTION: '설명 추론',
  UNKNOWN: '지역 불명',
}

// §2.4 구조 수집 상태 (10종) — COLLECTION_FAILED 하나만 경고, 나머지는 전부 중립
export const COVERAGE_LABEL = {
  AVAILABLE: '컬럼 구조 확인됨',
  PARTIAL: '일부 컬럼 구조 확인됨',
  NOT_COLLECTED: '아직 관측되지 않음',
  QUEUED: '수집 대기',
  COLLECTING: '수집 중',
  SOURCE_UNAVAILABLE: '원본에 접근할 수 없음',
  UNSUPPORTED_FORMAT: '지원하지 않는 형식',
  ACCESS_RESTRICTED: '접근 제한',
  COLLECTION_FAILED: '구조 수집 실패',
  API_STRUCTURE_NOT_SUPPORTED_YET: 'API 구조는 차기 지원',
}

// §2.5 예시값 상태 (6종) × examplesPublic(정책 플래그) — 조합 처리도 이 파일 단일 지점
export const EXAMPLE_STATUS_LABEL = {
  AVAILABLE: '예시값 표시',
  NO_NON_NULL_VALUES: '값 없음',
  WITHHELD_BY_LICENSE: '라이선스 보류',
  WITHHELD_BY_SAFETY: '안전 비공개',
  NOT_COLLECTED: '미수집',
  COLLECTION_FAILED: '수집 실패',
}

// §2.5 조합 표: AVAILABLE인데 정책상 비공개면 '비공개(정책)'
export const exampleStatusLabel = (status, examplesPublic) => {
  if (status === 'AVAILABLE' && !examplesPublic) return '비공개(정책)'
  return EXAMPLE_STATUS_LABEL[status] || status
}

// §2.6 최신성 (3종) — UNKNOWN은 나쁨이 아니다
export const FRESHNESS_LABEL = {
  FRESH: { text: '최신', cls: 'fresh' },
  POSSIBLY_STALE: { text: '갱신 지연 가능', cls: 'stale' },
  UNKNOWN: { text: '최신성 확인 불가', cls: 'unknown' },
}

// §2.2 근거 수준 (2종)
export const EVIDENCE_LEVEL_LABEL = {
  CATALOG_METADATA_ONLY: '목록 정보',
  FILE_OBSERVATION: '실제 파일 확인',
}

// §2.8 목록 유형 (3종)
export const LIST_TYPE_LABEL = { FILE: '파일', API: 'API', STD: '표준' }

// 계열 후보 검토 상태(v1.8) — UNREVIEWED는 '검토 전'이지 문제·미확정 실패가 아니다
export const FAMILY_REVIEW_LABEL = {
  UNREVIEWED: '검토 전',
  CONFIRMED_FAMILY: '계열 확정',
  LEGITIMATE_SPLIT: '정당한 분리',
  NOT_A_FAMILY: '계열 아님',
}

// 완전성 점검 필드(열린 사전 — 점수의 분해 근거 체크리스트)
export const COMPLETENESS_FIELD_LABEL = {
  title: '제목', theme: '분류', org_name: '제공기관', update_cycle: '갱신주기',
  keywords: '키워드', description: '설명', license: '이용허락', created_date: '등록일',
  modified_date: '수정일', list_url: '원문 URL', spatial: '공간범위', temporal: '시간범위',
  data_limits: '이용제한', format: '포맷', row_count: '행 수', file_data_name: '파일명',
  api_type: 'API 유형', traffic: '트래픽',
}

// 판단 직결 3필드(completeness.keyFields)
export const KEY_FIELD_LABEL = { spatial: '공간범위', temporal: '기간', dataLimits: '이용제한 명시' }

// 비교 표 필드(열린 사전)
export const COMPARE_FIELD_LABEL = {
  listType: '목록유형', orgName: '제공기관', theme: '분류체계', formats: '포맷',
  updateCycle: '업데이트 주기', license: '이용허락', modifiedDate: '수정일',
  createdDate: '등록일', rowCount: '전체 행', spatial: '공간범위', temporal: '시간범위',
  completenessScore: '완전성 점수', keywords: '키워드', fee: '비용', apiType: 'API 유형',
}

export const cycleLabel = (v) => UPDATE_CYCLE_LABEL[v] || v
export const licenseLabel = (v) => LICENSE_LABEL[v] || v

// ---- 아래는 컴포넌트에 흩어져 있던 로컬 라벨 상수를 이 레지스트리로 모은 것(가이드 §2.1).
// 영어 표면은 labels.en.js가 같은 export 이름으로 제공한다(키 동일성은 i18n.test.js가 검증).

// 시도 코드 → 표시명(검색 필터·해석 배너). 빈 코드는 '전체'
export const REGION_LABEL = {
  '': '지역 전체', 'KR-11': '서울', 'KR-26': '부산', 'KR-27': '대구', 'KR-28': '인천',
  'KR-29': '광주', 'KR-30': '대전', 'KR-31': '울산', 'KR-50': '세종', 'KR-41': '경기',
  'KR-42': '강원', 'KR-43': '충북', 'KR-44': '충남', 'KR-45': '전북', 'KR-46': '전남',
  'KR-47': '경북', 'KR-48': '경남', 'KR-49': '제주',
}

// 검색어가 일치한 항목(matchedFields, v1.6)
export const MATCH_FIELD_LABEL = { title: '제목', keywords: '키워드', description: '설명', orgName: '기관' }

// 해석된 필터의 필드명(interpretedFilters[].field)
export const INTERPRETED_FIELD_LABEL = { region: '지역', format: '포맷', updateCycle: '주기', listType: '유형' }

// 활용 계획(build_data_plan) — 역할·적합 신호·요구 충족 상태
export const ROLE_LABEL = {
  PRIMARY: '주 대상', DEMAND: '수요 측', SUPPLY: '공급 측',
  SPATIAL: '공간 결합', TEMPORAL: '시간 결합', REFERENCE: '참조·코드',
}
export const FIT_LABEL = {
  searchRelevance: '검색 관련도', structureEvidence: '구조 근거',
  freshness: '최신성', metadataCompleteness: '기재 수준',
}
export const NEED_STATUS_LABEL = { SATISFIED: '충족', UNSATISFIED: '미충족', PARTIAL: '부분 충족' }

// 구조 수집 상태 부연(CoverageIndicator) — 중립 문안. 품질 문제로 읽히게 쓰지 않는다
export const COVERAGE_STATUS_NOTE = {
  AVAILABLE: '실제 파일에서 컬럼명과 기본 구조가 관측됨 — 데이터 값의 정확성·품질을 보증하지 않습니다',
  NOT_COLLECTED: '품질 문제가 아니라 수집 순번입니다.',
  QUEUED: '수집 순번을 기다리고 있습니다.',
  API_STRUCTURE_NOT_SUPPORTED_YET: '파일 목록만 구조를 관측합니다.',
}

// 근거 수준 부연(EvidenceRow)
export const EVIDENCE_LEVEL_NOTE = {
  CATALOG_METADATA_ONLY: '실제 데이터의 내용은 확인하지 않았습니다',
  FILE_OBSERVATION: '관측 표본 한정 — 전체 품질을 보증하지 않습니다',
}

// 상세 렌즈 5종(§5.1)과 원본 데이터 렌즈의 표현 3종
export const LENS_LABEL = {
  overview: '개요', structure: '데이터 구조', evidence: '근거', uses: '활용 초안', raw: '원본 데이터',
}
export const RAW_VIEW_LABEL = { normalized: '정규화', source: '원본', jsonld: 'JSON-LD' }
