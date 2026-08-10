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
        이 페이지는 현재 스냅샷에서 확인된 사실을 보여줍니다. 평가하거나 순위를 매기는 것이
        아니라, 무엇을 확인했고 무엇을 아직 확인하지 못했는지를 구분합니다. 모든 수치에는
        적용한 규칙과 버전이 기록됩니다.
      </p>

      <div className="home-block">
        <h3>데이터 규모와 제공 유형</h3>
        {counts && (
          <p className="result-meta">공공데이터포털의 목록 {counts.datasets.toLocaleString()}건이 반영되어 있습니다.</p>
        )}
        {listType ? (
          <Bars buckets={listType.buckets.map((b) => ({ ...b, key: LIST_TYPE_LABEL[b.key] || b.key }))} />
        ) : <p className="result-meta">유형 분포를 불러오지 못했습니다.</p>}
      </div>

      <div className="home-block">
        <h3>실제 파일 구조 확인 현황</h3>
        {coverage ? (
          <>
            <p className="obs-figure">
              파일로 제공되는 {coverage.fileRecordsTotal.toLocaleString()}건 가운데{' '}
              <strong>{coverage.recordsAvailable.toLocaleString()}건</strong>은 실제 컬럼 구조를
              확인했습니다.
            </p>
            <p className="result-meta">
              아직 확인하지 못한 목록은 수집 대기 상태입니다. 데이터 품질이 낮다는 뜻은 아닙니다.
            </p>
          </>
        ) : <p className="result-meta">현재 서비스 버전에서는 실제 파일 구조를 확인한 범위를 제공하지 않습니다.</p>}
      </div>

      <div className="home-block">
        <h3>목록 정보 기재 현황 — 제공 유형별</h3>
        <p className="result-meta">
          파일·API·표준데이터는 확인하는 항목 수가 서로 다릅니다. 따라서 같은 유형 안에서만
          산출하며, 유형 간 수치를 합치거나 직접 비교하지 않습니다.
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
        <h3>주제별 분포 — 목록 수 상위 {theme ? theme.buckets.length : 0}개</h3>
        {theme ? <Bars buckets={theme.buckets} /> : <p className="result-meta">주제 분포를 불러오지 못했습니다.</p>}
      </div>

      <div className="home-block">
        <h3>제공 기관별 분포 — 목록 수 상위 {orgs ? orgs.buckets.length : 0}개 기관</h3>
        <p className="result-meta">목록 수는 기관의 데이터 개방 규모를 보여줄 뿐, 데이터 품질 순위는 아닙니다.</p>
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
        <h3>같은 계열로 보이는 데이터</h3>
        {!family ? (
          <p className="result-meta">계열 통계를 불러오지 못했습니다.</p>
        ) : family.available === false ? (
          <p className="result-meta">
            현재 서비스 버전에서는 같은 계열로 보이는 데이터 후보를 아직 산출하지 않았습니다.
            후보가 0건이라는 뜻은 아닙니다.
          </p>
        ) : (
          <>
            <p className="obs-figure">
              같은 계열로 보이는 후보 묶음 {family.familyCandidates.families.toLocaleString()}개
              (목록 {family.familyCandidates.memberRecords.toLocaleString()}건)를 자동으로
              찾았습니다.
            </p>
            <p className="result-meta">
              자동으로 찾은 후보이며, 같은 계열로 확정한 것은 아닙니다.{' '}
              {Object.entries(family.familyCandidates.byReviewStatus || {})
                .map(([k, n]) => `${FAMILY_REVIEW_LABEL[k] || k} ${n.toLocaleString()}건`)
                .join(' · ')}
            </p>
          </>
        )}
      </div>

      <div className="home-block">
        <h3>월별 변경 현황</h3>
        {!changes ? (
          <p className="result-meta">변경 통계를 불러오지 못했습니다.</p>
        ) : changes.baseSnapshot === null ? (
          <p className="result-meta">
            월간 스냅샷이 두 개 이상 쌓이면 신규·변경·미관측 통계를 제공합니다. 현재는 첫
            스냅샷을 축적하는 단계입니다.
          </p>
        ) : (
          <>
            <p className="obs-figure">
              {changes.baseSnapshot}부터 {changes.currentSnapshot}까지 확인된 변경입니다.
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
              ‘스냅샷에서 확인되지 않음(MISSING_FROM_SNAPSHOT)’은 데이터가 폐기되었다는 뜻이
              아닙니다. 공식적으로 폐기된 경우에만 ‘공식 폐기(OFFICIALLY_WITHDRAWN)’로
              표시합니다.
            </p>
          </>
        )}
      </div>
    </section>
  )
}
