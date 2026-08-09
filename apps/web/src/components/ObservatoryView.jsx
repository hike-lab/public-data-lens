// 관측 현황(2026-08-10 신설) — 현재 스냅샷에서 서버가 관측한 사실의 표현.
// 평가·순위·판정을 만들지 않는다(불변식 1·2): 모든 수치는 서버 응답 그대로이며,
// 미관측·미산출은 실패색 없이 상태로 표기한다(계약 의미 표). 변경 통계는 diff가
// 생성된 뒤부터 값이 생긴다 — 부재는 축적 단계라는 사실로 보여준다.
import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { LIST_TYPE_LABEL, FAMILY_REVIEW_LABEL, CHANGE_STATUS_LABEL } from '../labels.js'

function Bars({ buckets, max, renderExtra }) {
  const top = max || (buckets[0]?.count ?? 1)
  return (
    <ul className="obs-bars">
      {buckets.map((b) => (
        <li key={b.key ?? '(미기재)'}>
          <span className="obs-key">{b.key ?? '(미기재)'}</span>
          <span className="obs-track" aria-hidden="true">
            <span className="obs-fill" style={{ width: `${Math.max(2, (b.count / top) * 100)}%` }} />
          </span>
          <span className="obs-count">{b.count.toLocaleString()}건</span>
          {renderExtra && <span className="obs-extra">{renderExtra(b)}</span>}
        </li>
      ))}
    </ul>
  )
}

export default function ObservatoryView({ status }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.allSettled([
      api.stats('listType'),
      api.stats('completeness'),
      api.stats('theme', 8),
      api.statsBreakdown('org', 'listType', 8),
      api.stats('family'),
      api.changes({ pageSize: 1 }),
    ]).then((rs) => {
      if (rs.every((r) => r.status === 'rejected')) {
        setError(rs[0].reason?.message || '관측 현황을 불러오지 못했습니다.')
        return
      }
      const [listType, completeness, theme, orgs, family, changes] = rs.map(
        (r) => (r.status === 'fulfilled' ? r.value.data : null),
      )
      setData({ listType, completeness, theme, orgs, family, changes })
    })
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!data) return <p className="loading">불러오는 중…</p>

  const snapshot = status?.data?.currentSnapshot
  const counts = status?.data?.counts
  const coverage = status?.data?.structureCoverage
  const { listType, completeness, theme, orgs, family, changes } = data

  return (
    <section className="observatory">
      <h2 className="explore-title">관측 현황{snapshot && <> — {snapshot} 스냅샷</>}</h2>
      <p className="result-meta">
        현재 스냅샷에서 서버가 관측한 사실입니다. 평가나 순위가 아니라, 무엇이 확인되었고
        무엇이 아직 확인되지 않았는지를 보여줍니다. 모든 수치는 판정 규칙 버전과 함께
        산출됩니다.
      </p>

      <div className="home-block">
        <h3>규모와 제공 유형</h3>
        {counts && (
          <p className="result-meta">목록 {counts.datasets.toLocaleString()}건이 등재되어 있습니다.</p>
        )}
        {listType ? (
          <Bars buckets={listType.buckets.map((b) => ({ ...b, key: LIST_TYPE_LABEL[b.key] || b.key }))} />
        ) : <p className="result-meta">유형 분포를 불러오지 못했습니다.</p>}
      </div>

      <div className="home-block">
        <h3>실파일 구조 관측</h3>
        {coverage ? (
          <>
            <p className="obs-figure">
              파일형 {coverage.fileRecordsTotal.toLocaleString()}건 중{' '}
              <strong>{coverage.recordsAvailable.toLocaleString()}건</strong>의 실제 컬럼 구조가
              관측되어 있습니다.
            </p>
            <p className="result-meta">
              아직 관측되지 않은 목록은 수집 대기 상태입니다 — 데이터의 품질 문제가 아닙니다.
            </p>
          </>
        ) : <p className="result-meta">이 서버 릴리스는 구조 관측 커버리지를 제공하지 않습니다.</p>}
      </div>

      <div className="home-block">
        <h3>목록 메타데이터 완전성 — 유형별 프로파일</h3>
        <p className="result-meta">
          유형(파일/API/표준)마다 평가 항목 수가 달라 프로파일별로만 산출합니다.
          프로파일 간 합산·직접 비교는 하지 않습니다.
        </p>
        {completeness ? (
          <ul className="obs-profiles">
            {completeness.profiles.map((p) => (
              <li key={p.profile}>
                <strong>{LIST_TYPE_LABEL[p.profile] || p.profile}</strong>
                <span className="obs-count">
                  {p.average !== null ? `평균 기재율 ${(p.average * 100).toFixed(1)}%` : '산출 대상 없음'}
                </span>
              </li>
            ))}
          </ul>
        ) : <p className="result-meta">완전성 분포를 불러오지 못했습니다.</p>}
      </div>

      <div className="home-block">
        <h3>주제 분포 — 상위 {theme ? theme.buckets.length : 0}개</h3>
        {theme ? <Bars buckets={theme.buckets} /> : <p className="result-meta">주제 분포를 불러오지 못했습니다.</p>}
      </div>

      <div className="home-block">
        <h3>기관 분포 — 목록 수 상위 {orgs ? orgs.buckets.length : 0}개 기관</h3>
        <p className="result-meta">목록 수는 개방 활동의 규모이지 데이터 품질의 순위가 아닙니다.</p>
        {orgs ? (
          <Bars
            buckets={orgs.buckets}
            renderExtra={(b) =>
              b.breakdown
                ? Object.entries(b.breakdown)
                    .map(([k, n]) => `${LIST_TYPE_LABEL[k] || k} ${n.toLocaleString()}`)
                    .join(' · ')
                : null}
          />
        ) : <p className="result-meta">기관 분포를 불러오지 못했습니다.</p>}
      </div>

      <div className="home-block">
        <h3>데이터 계열 후보</h3>
        {!family ? (
          <p className="result-meta">계열 통계를 불러오지 못했습니다.</p>
        ) : family.available === false ? (
          <p className="result-meta">
            이 릴리스에는 계열 후보가 아직 산출되지 않았습니다 — 0건이라는 뜻이 아닙니다.
          </p>
        ) : (
          <>
            <p className="obs-figure">
              같은 계열로 보이는 후보 {family.familyCandidates.families.toLocaleString()}개
              (목록 {family.familyCandidates.memberRecords.toLocaleString()}건)가 자동
              탐지되어 있습니다.
            </p>
            <p className="result-meta">
              자동 탐지 후보이며 확정된 계열이 아닙니다.{' '}
              {Object.entries(family.familyCandidates.byReviewStatus || {})
                .map(([k, n]) => `${FAMILY_REVIEW_LABEL[k] || k} ${n.toLocaleString()}건`)
                .join(' · ')}
            </p>
          </>
        )}
      </div>

      <div className="home-block">
        <h3>월간 변경 관측</h3>
        {!changes ? (
          <p className="result-meta">변경 통계를 불러오지 못했습니다.</p>
        ) : changes.baseSnapshot === null ? (
          <p className="result-meta">
            월간 스냅샷이 2개 이상 축적되면 이 자리에서 신규·변경·미관측 통계를 제공합니다.
            지금은 첫 스냅샷 축적 단계입니다.
          </p>
        ) : (
          <>
            <p className="obs-figure">
              {changes.baseSnapshot} → {changes.currentSnapshot} 사이에 관측된 변경입니다.
            </p>
            {changes.summary && (
              <ul className="obs-profiles">
                {Object.entries(changes.summary).map(([k, n]) => (
                  <li key={k}>
                    <strong>{CHANGE_STATUS_LABEL[k] || k}</strong>
                    <span className="obs-count">{n.toLocaleString()}건</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="result-meta">
              스냅샷에서 관측되지 않음(MISSING_FROM_SNAPSHOT)은 폐기 확정이 아닙니다 —
              폐기는 OFFICIALLY_WITHDRAWN으로만 표기합니다.
            </p>
          </>
        )}
      </div>
    </section>
  )
}
