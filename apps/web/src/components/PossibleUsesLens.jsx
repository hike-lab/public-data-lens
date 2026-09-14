// 활용 계획 렌즈(§5.5, v1.5) — POST /api/plan(결정론 조립기)의 표시.
// 절대 규칙: 항상 초안(DRAFT)·품질 미평가(NOT_ASSESSED)·결합 키는 후보(CANDIDATE_ONLY)를
// 화면에 상시 노출한다. fitSignals 4개는 각각 표시하고 하나의 점수로 합치지 않는다.
// 이 렌즈를 '추천'이나 '적합 데이터'로 부르지 않는다 — 후보와 근거, 그리고 한계다.
// 역할·적합 신호·요구 상태 라벨은 labels.js(ROLE_LABEL·FIT_LABEL·NEED_STATUS_LABEL)에 있다.
import { useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'
import WarningPanel from './WarningPanel.jsx'

// 계획 초안 표시의 단일 지점 — 상세의 렌즈와 검색의 '목적' 모드가 공유한다
export function PlanResult({ body, onOpen }) {
  const { t, L } = useLang()
  const plan = body?.data
  if (!plan) return null
  return (
    <>
      <WarningPanel warnings={body.warnings} notices={body.notices} />
      <div className="uses-status">
        <span className="chip small">{t('plan.status', { status: plan.planStatus })}</span>
        <span className="chip small">{t('plan.quality', { q: plan.qualityAssessment })}</span>
      </div>

      <h3>{t('plan.interpretedTitle')}</h3>
      <p className="obs-meta">
        {t('plan.terms', { t: plan.interpretedPurpose.searchTerms.join(', ') || '—' })}
        {plan.interpretedPurpose.regionApplied && t('plan.region', {
          r: plan.interpretedPurpose.regionApplied,
          fromParam: plan.interpretedPurpose.regionSource === 'PARAMETER',
        })}
        {t('plan.iterations', { n: plan.interpretedPurpose.iterationsUsed })}
      </p>

      <h3>{t('plan.needsTitle')}</h3>
      <ul className="case-list">
        {plan.dataNeeds.map((n, i) => (
          <li key={i}>
            [{L.ROLE_LABEL[n.role] || n.role}] {n.need} — {L.NEED_STATUS_LABEL[n.status] || n.status}
            {n.reason && <> ({n.reason})</>}
          </li>
        ))}
      </ul>

      <h3>{t('plan.candidatesTitle')}</h3>
      <ul className="results">
        {plan.recommendedDatasets.map((c) => (
          <li key={c.recordId} className="result-row">
            <div className="row-main">
              <div className="row-title">
                <span className={`type type-${c.listType}`}>{c.listType}</span>
                <button type="button" className="link" onClick={() => onOpen?.(c.recordId)}>
                  {c.title}
                </button>
                {c.roles.map((r) => <span key={r} className="chip small">{L.ROLE_LABEL[r] || r}</span>)}
              </div>
              <div className="row-sub"><span>{c.orgName}</span></div>
              {/* fitSignals 4개 개별 표시 — 종합 점수로 합치지 않는다(계약 주석) */}
              <div className="row-badges">
                {Object.entries(c.fitSignals).map(([k, v]) => (
                  <span key={k} className="key-field">{L.FIT_LABEL[k] || k}: {v}</span>
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

      <h3>{t('plan.joinTitle')}</h3>
      {plan.possibleJoinKeys.length === 0
        ? <p className="obs-meta">{t('plan.joinEmpty')}</p>
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
          <h3>{t('plan.missingTitle')}</h3>
          <ul className="case-list">{plan.missingNeeds.map((m, i) => <li key={i}>{m.need || m}</li>)}</ul>
        </>
      )}

      <h3>{t('plan.nextTitle')}</h3>
      <ul className="case-list">{plan.nextChecks.map((c, i) => <li key={i}>{c}</li>)}</ul>
    </>
  )
}

export default function PossibleUsesLens({ ds, onOpen }) {
  const { t } = useLang()
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
      <h2>{t('plan.lensTitle')}</h2>
      <p className="obs-meta">{t('plan.lensIntro')}</p>
      <form className="uses-form" onSubmit={run}>
        <input
          value={purpose}
          onChange={(e) => setPurpose(e.target.value)}
          placeholder={t('plan.placeholder', { title: ds?.title })}
          maxLength={200}
          aria-label={t('plan.purposeAria')}
        />
        <button type="submit" disabled={loading}>{t('plan.submit')}</button>
      </form>

      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">{t('plan.assembling')}</p>}
      <PlanResult body={body} onOpen={onOpen} />
    </div>
  )
}
