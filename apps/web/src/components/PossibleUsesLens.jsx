// 활용 계획 렌즈(§5.5, v1.5) — POST /api/plan(결정론 조립기)의 표시.
// 절대 규칙: 항상 초안(DRAFT)·품질 미평가(NOT_ASSESSED)·결합 키는 후보(CANDIDATE_ONLY)를
// 화면에 상시 노출한다. fitSignals 4개는 각각 표시하고 하나의 점수로 합치지 않는다.
// 이 렌즈를 '추천'이나 '적합 데이터'로 부르지 않는다 — 후보와 근거, 그리고 한계다.
import { useState } from 'react'
import { api } from '../api.js'
import WarningPanel from './WarningPanel.jsx'

const ROLE_LABEL = {
  PRIMARY: '주 대상', DEMAND: '수요 측', SUPPLY: '공급 측',
  SPATIAL: '공간 결합', TEMPORAL: '시간 결합', REFERENCE: '참조·코드',
}
const FIT_LABEL = {
  searchRelevance: '검색 관련도',
  structureEvidence: '구조 근거',
  freshness: '최신성',
  metadataCompleteness: '기재 수준',
}
const NEED_STATUS = { SATISFIED: '충족', UNSATISFIED: '미충족', PARTIAL: '부분 충족' }

// 계획 초안 표시의 단일 지점 — 상세의 렌즈와 검색의 '목적' 모드가 공유한다
export function PlanResult({ body, onOpen }) {
  const plan = body?.data
  if (!plan) return null
  return (
    <>
      <WarningPanel warnings={body.warnings} notices={body.notices} />
      <div className="uses-status">
        <span className="chip small">계획 상태: 초안(<code>{plan.planStatus}</code>)</span>
        <span className="chip small">품질: 미평가(<code>{plan.qualityAssessment}</code>)</span>
      </div>

      <h3>해석된 목적</h3>
      <p className="obs-meta">
        검색어 {plan.interpretedPurpose.searchTerms.join(', ') || '—'}
        {plan.interpretedPurpose.regionApplied && <> · 지역 {plan.interpretedPurpose.regionApplied}
          ({plan.interpretedPurpose.regionSource === 'PARAMETER' ? '지정' : '문장에서 추출'})</>}
        {' '}· 검색 반복 {plan.interpretedPurpose.iterationsUsed}회
      </p>

      <h3>데이터 요구</h3>
      <ul className="case-list">
        {plan.dataNeeds.map((n, i) => (
          <li key={i}>
            [{ROLE_LABEL[n.role] || n.role}] {n.need} — {NEED_STATUS[n.status] || n.status}
            {n.reason && <> ({n.reason})</>}
          </li>
        ))}
      </ul>

      <h3>후보 데이터셋 (근거는 목록·관측 사실)</h3>
      <ul className="results">
        {plan.recommendedDatasets.map((c) => (
          <li key={c.recordId} className="result-row">
            <div className="row-main">
              <div className="row-title">
                <span className={`type type-${c.listType}`}>{c.listType}</span>
                <button type="button" className="link" onClick={() => onOpen?.(c.recordId)}>
                  {c.title}
                </button>
                {c.roles.map((r) => <span key={r} className="chip small">{ROLE_LABEL[r] || r}</span>)}
              </div>
              <div className="row-sub"><span>{c.orgName}</span></div>
              {/* fitSignals 4개 개별 표시 — 종합 점수로 합치지 않는다(계약 주석) */}
              <div className="row-badges">
                {Object.entries(c.fitSignals).map(([k, v]) => (
                  <span key={k} className="key-field">{FIT_LABEL[k] || k}: {v}</span>
                ))}
              </div>
              <p className="obs-meta">{c.whySelected}</p>
              {c.limitations?.length > 0 && (
                <ul className="case-list uses-limits">
                  {c.limitations.map((l, i) => <li key={i}>{l}</li>)}
                </ul>
              )}
            </div>
          </li>
        ))}
      </ul>

      <h3>예상 결합 키 — 전부 후보(CANDIDATE_ONLY)</h3>
      {plan.possibleJoinKeys.length === 0
        ? <p className="obs-meta">관측 근거가 있는 결합 키 후보가 없습니다 — 원문 컬럼 정의에서 직접 확인이 필요합니다.</p>
        : (
          <ul className="case-list">
            {plan.possibleJoinKeys.map((k, i) => (
              <li key={i}>
                {k.key} — <code>{k.status || 'CANDIDATE_ONLY'}</code>
                {k.note && <> · {k.note}</>}
              </li>
            ))}
          </ul>
        )}

      {plan.missingNeeds?.length > 0 && (
        <>
          <h3>미충족 요구</h3>
          <ul className="case-list">{plan.missingNeeds.map((m, i) => <li key={i}>{m.need || m}</li>)}</ul>
        </>
      )}

      <h3>다음 확인사항</h3>
      <ul className="case-list">{plan.nextChecks.map((c, i) => <li key={i}>{c}</li>)}</ul>
    </>
  )
}

export default function PossibleUsesLens({ ds, onOpen }) {
  const [purpose, setPurpose] = useState('')
  const [body, setBody] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = async (e) => {
    e.preventDefault()
    if (purpose.trim().length < 2) return
    setLoading(true)
    setError(null)
    try {
      setBody(await api.plan(purpose))
    } catch (err) {
      setError(`${err.code || ''} ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="profile uses-lens">
      <h2>활용 계획 초안</h2>
      <p className="obs-meta">
        하고 싶은 일을 한 문장으로 적으면 결정론 규칙(plan-assembly-v1.0)이 후보와 한계를
        조립합니다 — LLM 없음, 판정 없음, 항상 초안입니다.
      </p>
      <form className="uses-form" onSubmit={run}>
        <input
          value={purpose}
          onChange={(e) => setPurpose(e.target.value)}
          placeholder={`예: ${ds?.title ? `${ds.title.slice(0, 24)}로 ` : ''}지역 간 격차를 분석하고 싶다`}
          maxLength={200}
          aria-label="활용 목적"
        />
        <button type="submit" disabled={loading}>초안 조립</button>
      </form>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">조립 중…</p>}
      <PlanResult body={body} onOpen={onOpen} />
    </div>
  )
}
