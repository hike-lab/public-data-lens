// 정규화 코드의 사용자 표시 라벨 — 코드(계약값)는 그대로 두고 표시만 한글화한다.
export const UPDATE_CYCLE_LABEL = {
  DAILY: '일간', WEEKLY: '주간', MONTHLY: '월간', QUARTERLY: '분기',
  SEMIANNUAL: '반기', ANNUAL: '연간', IRREGULAR: '수시', UNSPECIFIED: '미기재',
}

export const LICENSE_LABEL = {
  NO_RESTRICTION: '제한 없음',
  KOGL_BY: '공공누리 1유형(출처표시)',
  KOGL_BY_NC: '공공누리 2유형(상업적 이용 금지)',
  KOGL_BY_ND: '공공누리 3유형(변경 금지)',
  KOGL_BY_NC_ND: '공공누리 4유형(상업적 금지·변경 금지)',
  OTHER: '기타(원문 확인)',
  UNSPECIFIED: '미기재',
}

export const CHANGE_STATUS_LABEL = {
  ADDED: '신규',
  MODIFIED: '변경',
  MISSING_FROM_SNAPSHOT: '스냅샷 부재',
  REAPPEARED: '재등장',
  POSSIBLE_IDENTITY_CHANGE: '정체성 변경 의심',
  OFFICIALLY_WITHDRAWN: '공식 폐기',
}

// 상태 의미의 오해를 막는 부연(§3.3: 스냅샷 부재 ≠ 폐기)
export const CHANGE_STATUS_NOTE = {
  MISSING_FROM_SNAPSHOT:
    '이번 스냅샷에서 관찰되지 않았다는 사실 기록입니다 — 폐기 확정이 아닙니다(폐기는 "공식 폐기"로만 표기).',
  POSSIBLE_IDENTITY_CHANGE:
    '제목·기관 등이 크게 달라져 같은 데이터셋인지 확인이 필요합니다(기관 개편·명칭 변경일 수 있음).',
  REAPPEARED: '이전 스냅샷에서 부재였다가 다시 관찰되었습니다.',
}

export const cycleLabel = (v) => UPDATE_CYCLE_LABEL[v] || v
export const licenseLabel = (v) => LICENSE_LABEL[v] || v
