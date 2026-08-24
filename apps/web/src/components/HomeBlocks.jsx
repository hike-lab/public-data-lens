// 홈 하단 블록(가이드 §3) — 전부 기존 응답으로 채운다. 표에 없는 데이터를 가정하지 않는다.
import { useEffect, useState } from 'react'
import { api } from '../api.js'
import CoverageIndicator from './CoverageIndicator.jsx'
import EvidenceRow from './EvidenceRow.jsx'

const pct = (a, b) => (b ? ((a / b) * 100).toFixed(1) : null)

// §3 #3 탐색 예시 — 결과가 아니라 과정을 보여준다. /api/plan(결정론 조립기)의 실제
// 응답을 축약 서사로 렌더한다: 목적 해석 → 후보 → 한계 → 다음 확인. 날조 없음.
const STORY_PURPOSE = '어린이 보호구역 교통안전을 분석하고 싶다'

export function ExplorationStoryBlock({ onTryPurpose }) {
  const [body, setBody] = useState(null)
  useEffect(() => {
    api.plan(STORY_PURPOSE, undefined, 3).then(setBody).catch(() => setBody(null))
  }, [])
  const plan = body?.data
  if (!plan) return null
  return (
    <section className="home-block story-block">
      <h3>이렇게 탐색합니다</h3>
      <p className="story-purpose">“{STORY_PURPOSE}”</p>
      <ol className="story-steps">
        <li>
          <strong>목적 파악</strong> — 질문에서 {plan.interpretedPurpose.searchTerms.map((t) => `‘${t}’`).join(', ')}을 핵심어로 찾습니다
          {plan.interpretedPurpose.regionApplied && <> · 지역 {plan.interpretedPurpose.regionApplied}(문장에서 추출)</>}
        </li>
        <li>
          <strong>후보 찾기</strong> — {plan.recommendedDatasets.map((c) => c.title).join(' · ')}
        </li>
        <li>
          <strong>예상 역할과 선정 근거</strong> — 각 데이터가 분석에서 어떤 역할을 할 수
          있는지와 후보로 선정된 근거를 보여줍니다. 여러 정보를 하나의 점수로 합쳐 순위를
          매기지는 않습니다.
        </li>
        <li>
          <strong>한계 확인</strong> — {plan.nextChecks[0]}
        </li>
      </ol>
      <p className="story-note">
        이 결과는 생성형 AI가 작성한 답변이 아닙니다. 정해진 규칙(<code>plan-assembly-v1.0</code>)에
        따라 만들어지며, 같은 데이터와 같은 입력에는 같은 결과를 제공합니다. 데이터 품질을
        판정한 결과가 아니므로(<code>NOT_ASSESSED</code>), 실제 활용 전에 검토가 필요한
        초안(<code>DRAFT</code>)입니다.
      </p>
      {onTryPurpose && (
        <button type="button" className="link story-cta" onClick={() => onTryPurpose(STORY_PURPOSE)}>
          내 목적에 맞는 데이터 찾기 →
        </button>
      )}
    </section>
  )
}

// §3 #5 Dataset anatomy — 구조 관측이 있는 실제 레코드 1건을 해부해 보여준다.
// 원본 컬럼명은 그대로(§5.3), 예시값 정책·관측 출처도 함께.
export function AnatomyBlock({ items, onOpen }) {
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
      <h3>데이터셋은 이렇게 읽힙니다</h3>
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
            <tr><th>원본 컬럼명</th><th>관측 유형</th><th>고유값</th></tr>
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
        전체 구조·근거 보기 →
      </button>
    </section>
  )
}

// §3.1 Coverage — 세 숫자를 함께(분모 규칙), 스냅샷 지연을 숨기지 않는다(§2 원칙 5)
export function CoverageBlock({ status }) {
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
      <h3>구조 관측 커버리지</h3>
      <div className="cov-figures">
        <div className="cov-fig">
          <strong>{total.toLocaleString()}</strong>
          <span>목록 전체</span>
        </div>
        <div className="cov-fig">
          <strong>{fileRecordsTotal.toLocaleString()}</strong>
          <span>FILE 유형</span>
        </div>
        <div className="cov-fig">
          <strong>{recordsAvailable.toLocaleString()}</strong>
          <span>구조 관측 확보</span>
        </div>
      </div>
      <p className="cov-note">
        구조 관측 확보분은 FILE의 {pct(recordsAvailable, fileRecordsTotal)}% ·
        전체의 {pct(recordsAvailable, total)}%입니다. API·STD 유형은 아직 구조 관측
        대상이 아닙니다(API_STRUCTURE_NOT_SUPPORTED_YET).
      </p>
      <p className="cov-lag">
        현재 스냅샷 {d.currentSnapshot} · 배포 {d.deployedAt?.slice(0, 10)}
        {lagDays != null && <> — 스냅샷 기준월 시작으로부터 {lagDays}일 지연</>}
        {' '}· 릴리스 <code>{d.release}</code>
      </p>
    </section>
  )
}

// §3.2 Open Infrastructure — 판정 규칙 레지스트리 전체(개수 하드코딩 금지).
// 폐기 규칙(deprecated)은 숨기지 않고 표시한다 — 버전 관리의 증거.
export function OpenInfraBlock() {
  const [registry, setRegistry] = useState(null)
  const [evalReport, setEvalReport] = useState(null)
  useEffect(() => {
    api.rules().then(setRegistry).catch(() => setRegistry(null))
    // 검색 품질 지표(v1.5) — 라우트가 없는 구버전 서버에서는 조용히 생략
    api.evalReport().then(setEvalReport).catch(() => setEvalReport(null))
  }, [])
  if (!registry?.rules) return null
  return (
    <section className="home-block">
      <h3>공개된 검색·비교 기준 — {registry.rules.length}개 규칙</h3>
      <p className="infra-sub">
        데이터를 찾고 비교할 때 적용하는 {registry.rules.length}개 규칙을 공개하고 있습니다.
        각 결과에는 적용한 규칙과 버전이 기록되므로, 어떤 기준으로 결과가 만들어졌는지
        확인하고 다시 검증할 수 있습니다.
      </p>
      <ul className="rule-list">
        {registry.rules.map((r) => (
          <li key={r.ruleId} className={r.deprecated ? 'rule deprecated' : 'rule'}>
            <details>
              <summary>
                <code>{r.ruleId}</code> {r.title}
                {r.deprecated && <span className="rule-flag"> 폐기{r.supersededBy && ` → ${r.supersededBy}`}</span>}
              </summary>
              <p>{r.definition}</p>
              {r.effectiveDate && <p className="rule-meta">시행일 {r.effectiveDate}</p>}
            </details>
          </li>
        ))}
      </ul>
      {evalReport?.summary && (
        <p className="eval-metrics">
          검색 성능 참고값({evalReport.summary.queries}개 검색 질문으로 측정):
          {' '}P@10 {evalReport.summary.meanPrecisionAt10}
          {' '}· R@10 {evalReport.summary.meanRecallAt10}
          {' '}· nDCG@10 {evalReport.summary.meanNdcgAt10}
          {!evalReport.summary.humanReviewed && (
            <span className="rule-flag"> — 질문은 자동 생성되었으며 아직 사람이 검토하지 않은 결과입니다</span>
          )}
          {' '}· <a href="/api/resources/eval" target="_blank" rel="noreferrer">전체 리포트</a>
        </p>
      )}
      <p className="infra-links">
        기술 자료:{' '}
        <a href="/api/resources/rules" target="_blank" rel="noreferrer">규칙 레지스트리</a> ·{' '}
        <a href="/api/resources/spec/tools" target="_blank" rel="noreferrer">도구 스키마</a> ·{' '}
        <a href="/api/resources/context" target="_blank" rel="noreferrer">JSON-LD Context</a> ·{' '}
        <a href="/api/resources/shapes" target="_blank" rel="noreferrer">SHACL</a> ·{' '}
        <a href="/api/resources/prompts/build-data-plan" target="_blank" rel="noreferrer">예시 프롬프트</a> ·{' '}
        <a href="/api/resources/privacy" target="_blank" rel="noreferrer">개인정보·로그 안내</a>
      </p>
    </section>
  )
}
