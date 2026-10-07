// 근거 표기의 단일 지점(가이드 §7, DESIGN §7 시그니처) — 판정이 있으면 근거가 있다.
// 문장을 하드코딩하지 않고 evidenceLevel 값에서 도출한다.
import { useLang } from '../i18n.jsx'

// 지역 배지 — 근거 수준(명시/추론)을 색이 아니라 텍스트로도 병기한다.
// short: 행 밀도용 접미사 축약('서울특별시'→'서울') — 표시 축약일 뿐 서버 값 변형이 아니다(STEP 5에서 존폐 검토).
// r.name은 서버 값(한국어)이며 어느 표시 언어에서도 번역하지 않는다.
export function RegionBadges({ regions, short }) {
  const { t, L } = useLang()
  if (!regions?.length) return null
  return regions.map((r) => (
    <span
      key={r.code}
      className={`region ${r.evidence === 'EXPLICIT_SPATIAL' ? 'explicit' : 'inferred'}`}
      title={t('ev.regionTitle', { label: L.EVIDENCE_LABEL[r.evidence] || r.evidence, conf: r.confidence })}
    >
      {short ? r.name.replace(/(특별자치|특별|광역)?(시|도)$/, '') : r.name}
      {r.evidence !== 'EXPLICIT_SPATIAL' && <span className="inf-mark">{t('ev.inferredMark')}</span>}
    </span>
  ))
}

export default function EvidenceRow({ level, snapshot, rules, observation, className, children }) {
  const { t, L } = useLang()
  const parts = []
  if (level) {
    parts.push(t('ev.level', { label: L.EVIDENCE_LEVEL_LABEL[level] || level, level }))
    if (L.EVIDENCE_LEVEL_NOTE[level]) parts.push(L.EVIDENCE_LEVEL_NOTE[level])
  }
  if (observation) {
    parts.push(t('ev.observation', {
      date: observation.observedAt?.slice(0, 10) || '—',
      prov: observation.provenance,
      scope: observation.scanScope,
    }))
  }
  if (snapshot) parts.push(t('ev.snapshot', { s: snapshot }))
  if (rules?.length) parts.push(t('ev.rules', { r: rules.join(', ') }))
  if (!parts.length && !children) return null
  return (
    <p className={className || 'evidence-note'}>
      {parts.join(' — ')}
      {children}
    </p>
  )
}
