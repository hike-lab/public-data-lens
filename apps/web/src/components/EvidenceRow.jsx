// 근거 표기의 단일 지점(가이드 §7, DESIGN §7 시그니처) — 판정이 있으면 근거가 있다.
// 문장을 하드코딩하지 않고 evidenceLevel 값에서 도출한다.
import { EVIDENCE_LABEL, EVIDENCE_LEVEL_LABEL } from '../labels.js'

const LEVEL_NOTE = {
  CATALOG_METADATA_ONLY: '실제 데이터 내용은 확인되지 않았습니다',
  FILE_OBSERVATION: '관측 표본 한정 — 전체 품질을 보증하지 않습니다',
}

// 지역 배지 — 근거 수준(명시/추론)을 색이 아니라 텍스트로도 병기한다.
// short: 행 밀도용 접미사 축약('서울특별시'→'서울') — 표시 축약일 뿐 서버 값 변형이 아니다(STEP 5에서 존폐 검토).
export function RegionBadges({ regions, short }) {
  if (!regions?.length) return null
  return regions.map((r) => (
    <span
      key={r.code}
      className={`region ${r.evidence === 'EXPLICIT_SPATIAL' ? 'explicit' : 'inferred'}`}
      title={`${EVIDENCE_LABEL[r.evidence] || r.evidence} · 신뢰도 ${r.confidence}`}
    >
      {short ? r.name.replace(/(특별자치|특별|광역)?(시|도)$/, '') : r.name}
      {r.evidence !== 'EXPLICIT_SPATIAL' && <span className="inf-mark">추론</span>}
    </span>
  ))
}

export default function EvidenceRow({ level, snapshot, rules, observation, className, children }) {
  const parts = []
  if (level) {
    parts.push(`근거 수준: ${EVIDENCE_LEVEL_LABEL[level] || level}(${level})`)
    if (LEVEL_NOTE[level]) parts.push(LEVEL_NOTE[level])
  }
  if (observation) {
    parts.push(
      `관측 ${observation.observedAt?.slice(0, 10) || '—'} · ${observation.provenance}` +
      ` · 스캔 ${observation.scanScope}`,
    )
  }
  if (snapshot) parts.push(`판정 스냅샷 ${snapshot}`)
  if (rules?.length) parts.push(`규칙 ${rules.join(', ')}`)
  if (!parts.length && !children) return null
  return (
    <p className={className || 'evidence-note'}>
      {parts.join(' — ')}
      {children}
    </p>
  )
}
