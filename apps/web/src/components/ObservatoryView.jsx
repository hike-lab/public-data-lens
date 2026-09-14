// 관측 현황(2026-08-10 신설) — 현재 스냅샷에서 서버가 관측한 사실의 표현.
// 평가·순위·판정을 만들지 않는다(불변식 1·2): 모든 수치는 서버 응답 그대로이며,
// 미관측·미산출은 실패색 없이 상태로 표기한다(계약 의미 표). 변경 통계는 diff가
// 생성된 뒤부터 값이 생긴다 — 부재는 축적 단계라는 사실로 보여준다.
import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'

function Bars({ buckets, max, renderExtra }) {
  const { t } = useLang()
  const top = max || (buckets[0]?.count ?? 1)
  return (
    <ul className="obs-bars">
      {buckets.map((b) => (
        <li key={b.key ?? '(null)'}>
          {/* 버킷 키는 서버 값(주제명·기관명은 한국어 원문) — null만 '미기재'로 표기 */}
          <span className="obs-key">{b.key ?? t('obs.unspecified')}</span>
          <span className="obs-track" aria-hidden="true">
            <span className="obs-fill" style={{ width: `${Math.max(2, (b.count / top) * 100)}%` }} />
          </span>
          <span className="obs-count">{t('obs.count', { n: b.count.toLocaleString() })}</span>
          {renderExtra && <span className="obs-extra">{renderExtra(b)}</span>}
        </li>
      ))}
    </ul>
  )
}

export default function ObservatoryView({ status }) {
  const { t, L } = useLang()
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
        setError(rs[0].reason?.message || t('obs.loadFail'))
        return
      }
      const [listType, completeness, theme, orgs, family, changes] = rs.map(
        (r) => (r.status === 'fulfilled' ? r.value.data : null),
      )
      setData({ listType, completeness, theme, orgs, family, changes })
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!data) return <p className="loading">{t('common.loading')}</p>

  const snapshot = status?.data?.currentSnapshot
  const counts = status?.data?.counts
  const coverage = status?.data?.structureCoverage
  const { listType, completeness, theme, orgs, family, changes } = data

  return (
    <section className="observatory">
      <h2 className="explore-title">{t('obs.title')}{snapshot && t('obs.titleSnapshot', { s: snapshot })}</h2>
      <p className="result-meta">{t('obs.intro')}</p>

      <div className="home-block">
        <h3>{t('obs.sizeTitle')}</h3>
        {counts && (
          <p className="result-meta">{t('obs.sizeIntro', { n: counts.datasets.toLocaleString() })}</p>
        )}
        {listType ? (
          <Bars buckets={listType.buckets.map((b) => ({ ...b, key: L.LIST_TYPE_LABEL[b.key] || b.key }))} />
        ) : <p className="result-meta">{t('obs.typeFail')}</p>}
      </div>

      <div className="home-block">
        <h3>{t('obs.structTitle')}</h3>
        {coverage ? (
          <>
            <p className="obs-figure">
              {t('obs.structFigure', {
                total: coverage.fileRecordsTotal.toLocaleString(),
                n: coverage.recordsAvailable.toLocaleString(),
              })}
            </p>
            <p className="result-meta">{t('obs.structNote')}</p>
          </>
        ) : <p className="result-meta">{t('obs.structUnavailable')}</p>}
      </div>

      <div className="home-block">
        <h3>{t('obs.complTitle')}</h3>
        <p className="result-meta">{t('obs.complIntro')}</p>
        {completeness ? (
          <ul className="obs-profiles">
            {completeness.profiles.map((p) => (
              <li key={p.profile}>
                <strong>{L.LIST_TYPE_LABEL[p.profile] || p.profile}</strong>
                <span className="obs-count">
                  {p.average !== null ? t('obs.avgRate', { p: (p.average * 100).toFixed(1) }) : t('obs.noTarget')}
                </span>
              </li>
            ))}
          </ul>
        ) : <p className="result-meta">{t('obs.complFail')}</p>}
      </div>

      <div className="home-block">
        <h3>{t('obs.themeTitle', { n: theme ? theme.buckets.length : 0 })}</h3>
        {theme ? <Bars buckets={theme.buckets} /> : <p className="result-meta">{t('obs.themeFail')}</p>}
      </div>

      <div className="home-block">
        <h3>{t('obs.orgTitle', { n: orgs ? orgs.buckets.length : 0 })}</h3>
        <p className="result-meta">{t('obs.orgNote')}</p>
        {orgs ? (
          <Bars
            buckets={orgs.buckets}
            renderExtra={(b) =>
              b.breakdown
                ? Object.entries(b.breakdown)
                    .map(([k, n]) => `${L.LIST_TYPE_LABEL[k] || k} ${n.toLocaleString()}`)
                    .join(' · ')
                : null}
          />
        ) : <p className="result-meta">{t('obs.orgFail')}</p>}
      </div>

      <div className="home-block">
        <h3>{t('obs.familyTitle')}</h3>
        {!family ? (
          <p className="result-meta">{t('obs.familyFail')}</p>
        ) : family.available === false ? (
          <p className="result-meta">{t('obs.familyUnavailable')}</p>
        ) : (
          <>
            <p className="obs-figure">
              {t('obs.familyFigure', {
                f: family.familyCandidates.families.toLocaleString(),
                m: family.familyCandidates.memberRecords.toLocaleString(),
              })}
            </p>
            <p className="result-meta">
              {t('obs.familyNote')}
              {Object.entries(family.familyCandidates.byReviewStatus || {})
                .map(([k, n]) => t('obs.familyStatus', { label: L.FAMILY_REVIEW_LABEL[k] || k, n: n.toLocaleString() }))
                .join(' · ')}
            </p>
          </>
        )}
      </div>

      <div className="home-block">
        <h3>{t('obs.changesTitle')}</h3>
        {!changes ? (
          <p className="result-meta">{t('obs.changesFail')}</p>
        ) : changes.baseSnapshot === null ? (
          <p className="result-meta">{t('obs.changesAccumulating')}</p>
        ) : (
          <>
            <p className="obs-figure">
              {t('obs.changesFigure', { base: changes.baseSnapshot, cur: changes.currentSnapshot })}
            </p>
            {changes.summary && (
              <ul className="obs-profiles">
                {Object.entries(changes.summary).map(([k, n]) => (
                  <li key={k}>
                    <strong>{L.CHANGE_STATUS_LABEL[k] || k}</strong>
                    <span className="obs-count">{t('obs.count', { n: n.toLocaleString() })}</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="result-meta">{t('obs.changesNote')}</p>
          </>
        )}
      </div>
    </section>
  )
}
