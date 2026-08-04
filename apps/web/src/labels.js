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
  MISSING_FROM_SNAPSHOT: '스냅샷 부재',
  REAPPEARED: '재등장',
  POSSIBLE_IDENTITY_CHANGE: '정체성 변경 의심',
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
  UNKNOWN: { text: '최신성 판단 불가', cls: 'unknown' },
}

// §2.2 근거 수준 (2종)
export const EVIDENCE_LEVEL_LABEL = {
  CATALOG_METADATA_ONLY: '메타데이터 기준',
  FILE_OBSERVATION: '실제 파일 구조 관측',
}

// §2.8 목록 유형 (3종)
export const LIST_TYPE_LABEL = { FILE: '파일', API: 'API', STD: '표준' }

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
