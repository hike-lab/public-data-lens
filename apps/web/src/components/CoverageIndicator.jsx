// 구조 수집 상태 표시의 단일 지점(가이드 §2.4, §7).
// 절대 규칙: COLLECTION_FAILED만 경고색 — 미수집·대기·제한은 전부 중립(품질 문제가 아니라 수집 순번).
// 커버리지 수치는 분모 없이 표시하지 않는다(§4.2).
import { useLang } from '../i18n.jsx'

// mode='note' — 구조 탭 머리말(자산 유무 두 갈래)
// mode='chip' — 행 안의 상태 칩(툴팁으로 의미 부연)
export default function CoverageIndicator({
  mode = 'note', status, available, total, examplesPublic,
}) {
  const { t, L } = useLang()
  const label = L.COVERAGE_LABEL[status] || status
  const note = L.COVERAGE_STATUS_NOTE[status]
  const warn = status === 'COLLECTION_FAILED'

  if (mode === 'chip') {
    return (
      <span
        className={`key-field structure-chip${warn ? ' s-COLLECTION_FAILED' : ''}`}
        title={note || t('cov.chipTitle', { label })}
      >
        {label}
      </span>
    )
  }

  if (available == null || total == null) {
    return (
      <p className={`coverage-note s-${status}`}>
        {label}
        {note && ` — ${note}`}
      </p>
    )
  }
  return (
    <p className="coverage-note">
      <strong>{label}</strong>{t('cov.filesObserved', { a: available, b: total })}
      {examplesPublic === false && <span className="ex-policy">{t('cov.examplesWithheld')}</span>}
    </p>
  )
}

// 컬럼 검색 모집단 문구 — 검색 범위를 분모와 함께 명시(§4.2)
export function CoveragePopulation({ searched, total }) {
  const { t } = useLang()
  if (searched == null) return null
  return t('cov.population', {
    searched: searched.toLocaleString(),
    total: total != null ? total.toLocaleString() : null,
  })
}
