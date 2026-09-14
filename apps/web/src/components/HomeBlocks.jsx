// 홈 하단 블록(가이드 §3) — 전부 기존 응답으로 채운다. 표에 없는 데이터를 가정하지 않는다.
import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'
import CoverageIndicator from './CoverageIndicator.jsx'
import EvidenceRow from './EvidenceRow.jsx'

const pct = (a, b) => (b ? ((a / b) * 100).toFixed(1) : null)

// §3 #3 탐색 예시 — 결과가 아니라 과정을 보여준다. /api/plan(결정론 조립기)의 실제
// 응답을 축약 서사로 렌더한다: 목적 해석 → 후보 → 한계 → 다음 확인. 날조 없음.
// 목적 문장(q)은 한국어 카탈로그를 조회하므로 언어와 무관하게 같다 — 표시 문안(label)만 바뀐다.
export function ExplorationStoryBlock({ onTryPurpose }) {
  const { t } = useLang()
  const story = t('home.storyPurpose')
  const [body, setBody] = useState(null)
  useEffect(() => {
    api.plan(story.q, undefined, 3).then(setBody).catch(() => setBody(null))
  }, [story.q])
  const plan = body?.data
  if (!plan) return null
  return (
    <section className="home-block story-block">
      <h3>{t('home.storyTitle')}</h3>
      <p className="story-purpose">“{story.label}”</p>
      <ol className="story-steps">
        <li>
          {t('home.step1', {
            terms: plan.interpretedPurpose.searchTerms.map((x) => `‘${x}’`).join(', '),
            region: plan.interpretedPurpose.regionApplied,
          })}
        </li>
        <li>{t('home.step2', { titles: plan.recommendedDatasets.map((c) => c.title).join(' · ') })}</li>
        <li>{t('home.step3')}</li>
        <li>{t('home.step4', { check: plan.nextChecks[0] })}</li>
      </ol>
      <p className="story-note">{t('home.storyNote')}</p>
      {onTryPurpose && (
        <button type="button" className="link story-cta" onClick={() => onTryPurpose(story.q)}>
          {t('home.storyCta')}
        </button>
      )}
    </section>
  )
}

// §3 #5 Dataset anatomy — 구조 관측이 있는 실제 레코드 1건을 해부해 보여준다.
// 원본 컬럼명은 그대로(§5.3), 예시값 정책·관측 출처도 함께.
export function AnatomyBlock({ items, onOpen }) {
  const { t } = useLang()
  const target = items?.find((it) => it.structureAvailable)
  const [body, setBody] = useState(null)
  useEffect(() => {
    if (!target) return
    api.structure(target.recordId).then(setBody).catch(() => setBody(null))
  }, [target?.recordId])
  const st = body?.data
  const table = st?.assets?.[0]?.tables?.[0]
  if (!target || !table) return null
  return (
    <section className="home-block anatomy-block">
      <h3>{t('home.anatomyTitle')}</h3>
      <div className="anatomy-head">
        <strong>{target.title}</strong>
        <span className="obs-meta">{target.orgName}</span>
      </div>
      <CoverageIndicator
        status={st.coverageStatus}
        available={st.coverage.availableAssets}
        total={st.coverage.totalAssets}
        examplesPublic={st.examplesPublic}
      />
      <div className="table-scroll" tabIndex={0}>
        <table className="structure-table">
          <thead>
            <tr><th>{t('profile.th.source')}</th><th>{t('profile.th.type')}</th><th>{t('profile.th.distinct')}</th></tr>
          </thead>
          <tbody>
            {table.columns.slice(0, 5).map((c) => (
              <tr key={c.ordinal}>
                <td>{c.sourceName}</td>
                <td>{c.observedType || '—'}</td>
                <td>{c.distinctCount != null ? c.distinctCount.toLocaleString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <EvidenceRow className="obs-meta" observation={st.assets[0].observation} />
      <button type="button" className="link" onClick={() => onOpen?.(target.recordId)}>
        {t('home.anatomyCta')}
      </button>
    </section>
  )
}

// §3.1 Coverage — 세 숫자를 함께(분모 규칙), 스냅샷 지연을 숨기지 않는다(§2 원칙 5)
export function CoverageBlock({ status }) {
  const { t } = useLang()
  const d = status?.data
  if (!d?.structureCoverage) return null
  const { recordsAvailable, fileRecordsTotal } = d.structureCoverage
  const total = d.counts.datasets
  // 스냅샷 지연: 서버 사실(snapshotLagDays, v1.5)을 우선 — 구버전 응답만 프론트 계산 폴백
  const lagDays = d.snapshotLagDays ?? (d.deployedAt
    ? Math.floor((Date.parse(d.deployedAt) - Date.parse(`${d.currentSnapshot}-01`)) / 86400000)
    : null)
  return (
    <section className="home-block">
      <h3>{t('home.covTitle')}</h3>
      <div className="cov-figures">
        <div className="cov-fig">
          <strong>{total.toLocaleString()}</strong>
          <span>{t('home.covAll')}</span>
        </div>
        <div className="cov-fig">
          <strong>{fileRecordsTotal.toLocaleString()}</strong>
          <span>{t('home.covFile')}</span>
        </div>
        <div className="cov-fig">
          <strong>{recordsAvailable.toLocaleString()}</strong>
          <span>{t('home.covObserved')}</span>
        </div>
      </div>
      <p className="cov-note">
        {t('home.covNote', { pf: pct(recordsAvailable, fileRecordsTotal), pa: pct(recordsAvailable, total) })}
      </p>
      <p className="cov-lag">
        {t('home.covLag', {
          snapshot: d.currentSnapshot, deployed: d.deployedAt?.slice(0, 10), lag: lagDays, release: d.release,
        })}
      </p>
    </section>
  )
}

// §3.2 Open Infrastructure — 판정 규칙 레지스트리 전체(개수 하드코딩 금지).
// 폐기 규칙(deprecated)은 숨기지 않고 표시한다 — 버전 관리의 증거.
// 규칙 제목·정의(r.title·r.definition)는 서버 레지스트리 원문이며 번역하지 않는다.
export function OpenInfraBlock() {
  const { t } = useLang()
  const [registry, setRegistry] = useState(null)
  const [evalReport, setEvalReport] = useState(null)
  useEffect(() => {
    api.rules().then(setRegistry).catch(() => setRegistry(null))
    // 검색 품질 지표(v1.5) — 라우트가 없는 구버전 서버에서는 조용히 생략
    api.evalReport().then(setEvalReport).catch(() => setEvalReport(null))
  }, [])
  if (!registry?.rules) return null
  const n = registry.rules.length
  return (
    <section className="home-block">
      <h3>{t('home.infraTitle', { n })}</h3>
      <p className="infra-sub">{t('home.infraSub', { n })}</p>
      <ul className="rule-list">
        {registry.rules.map((r) => (
          <li key={r.ruleId} className={r.deprecated ? 'rule deprecated' : 'rule'}>
            <details>
              <summary>
                <code>{r.ruleId}</code> {r.title}
                {r.deprecated && <span className="rule-flag">{t('home.deprecated')}{r.supersededBy && ` → ${r.supersededBy}`}</span>}
              </summary>
              <p>{r.definition}</p>
              {r.effectiveDate && <p className="rule-meta">{t('home.effective', { d: r.effectiveDate })}</p>}
            </details>
          </li>
        ))}
      </ul>
      {evalReport?.summary && (
        <p className="eval-metrics">
          {t('home.evalMetrics', {
            q: evalReport.summary.queries,
            p: evalReport.summary.meanPrecisionAt10,
            r: evalReport.summary.meanRecallAt10,
            n: evalReport.summary.meanNdcgAt10,
          })}
          {!evalReport.summary.humanReviewed && (
            <span className="rule-flag">{t('home.evalUnreviewed')}</span>
          )}
          {' '}· <a href="/api/resources/eval" target="_blank" rel="noreferrer">{t('home.evalFull')}</a>
        </p>
      )}
      <p className="infra-links">
        {t('home.techDocs')}{' '}
        <a href="/api/resources/rules" target="_blank" rel="noreferrer">{t('home.linkRules')}</a> ·{' '}
        <a href="/api/resources/spec/tools" target="_blank" rel="noreferrer">{t('home.linkSchema')}</a> ·{' '}
        <a href="/api/resources/context" target="_blank" rel="noreferrer">{t('home.linkContext')}</a> ·{' '}
        <a href="/api/resources/shapes" target="_blank" rel="noreferrer">{t('home.linkShapes')}</a> ·{' '}
        <a href="/api/resources/prompts/build-data-plan" target="_blank" rel="noreferrer">{t('home.linkPrompt')}</a> ·{' '}
        <a href="/api/resources/privacy" target="_blank" rel="noreferrer">{t('home.linkPrivacy')}</a>
      </p>
    </section>
  )
}
