// 구조 수집 상태 표시의 단일 지점(가이드 §2.4, §7).
// 절대 규칙: COLLECTION_FAILED만 경고색 — 미수집·대기·제한은 전부 중립(품질 문제가 아니라 수집 순번).
// 커버리지 수치는 분모 없이 표시하지 않는다(§4.2).
import { COVERAGE_LABEL } from '../labels.js'

const STATUS_NOTE = {
  AVAILABLE: '실제 파일에서 컬럼명과 기본 구조가 관측됨 — 데이터 값의 정확성·품질을 보증하지 않습니다',
  NOT_COLLECTED: '품질 문제가 아니라 수집 순번입니다.',
  QUEUED: '수집 순번을 기다리고 있습니다.',
  API_STRUCTURE_NOT_SUPPORTED_YET: '파일 목록만 구조를 관측합니다.',
}

// mode='note' — 구조 탭 머리말(자산 유무 두 갈래)
// mode='chip' — 행 안의 상태 칩(툴팁으로 의미 부연)
export default function CoverageIndicator({
  mode = 'note', status, available, total, examplesPublic,
}) {
  const label = COVERAGE_LABEL[status] || status
  const warn = status === 'COLLECTION_FAILED'

  if (mode === 'chip') {
    return (
      <span
        className={`key-field structure-chip${warn ? ' s-COLLECTION_FAILED' : ''}`}
        title={STATUS_NOTE[status] || `구조 수집 상태: ${label}`}
      >
        {label}
      </span>
    )
  }

  if (available == null || total == null) {
    return (
      <p className={`coverage-note s-${status}`}>
        {label}
        {STATUS_NOTE[status] && ` — ${STATUS_NOTE[status]}`}
      </p>
    )
  }
  return (
    <p className="coverage-note">
      <strong>{label}</strong> · 파일 {available}/{total}개 관측
      {examplesPublic === false && <span className="ex-policy"> · 예시값 비공개(법적 확인 전)</span>}
    </p>
  )
}

// 컬럼 검색 모집단 문구 — 검색 범위를 분모와 함께 명시(§4.2)
export function CoveragePopulation({ searched, total }) {
  if (searched == null) return null
  return (
    <>
      구조가 관측된 {searched.toLocaleString()}건
      {total != null && <> (전체 파일 목록 {total.toLocaleString()}건)</>} 중 검색
    </>
  )
}
