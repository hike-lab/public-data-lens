import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'
import { CoverageBlock, OpenInfraBlock } from './HomeBlocks.jsx'

export default function AboutView({ status }) {
  const { t } = useLang()
  const [themes, setThemes] = useState(null)

  useEffect(() => {
    api.stats('theme', 6).then((b) => setThemes(b.data.buckets)).catch(() => setThemes(null))
  }, [])

  const s = status?.data

  return (
    <section className="about">
      <div className="about-hero">
        <h2>{t('about.heroTitle')}</h2>
        <p>{t('about.heroBody')}</p>
        <p className="about-research">{t('about.research')}</p>
      </div>

      <h3>{t('about.catalogTitle')}</h3>
      {s ? (
        <>
          <div className="stat-tiles">
            <div className="stat-tile">
              <span className="stat-v">{s.counts.datasets.toLocaleString()}</span>
              <span className="stat-k">{t('about.statAll')}</span>
            </div>
            {s.structureCoverage && (
              <div className="stat-tile">
                <span className="stat-v">{s.structureCoverage.recordsAvailable.toLocaleString()}</span>
                <span className="stat-k">{t('about.statStruct')}</span>
              </div>
            )}
            <div className="stat-tile">
              <span className="stat-v">{s.currentSnapshot}</span>
              <span className="stat-k">{t('about.statSnapshot')}</span>
            </div>
            <div className="stat-tile">
              <span className="stat-v">{s.processedAt?.slice(0, 10)}</span>
              <span className="stat-k">{t('about.statAnalyzed')}</span>
            </div>
          </div>
          {themes && (
            <div className="theme-bars">
              {themes.map((th) => {
                const max = themes[0].count
                return (
                  <div className="theme-bar" key={th.key}>
                    {/* 주제명은 서버 버킷 키(한국어) 그대로 */}
                    <span className="tb-label">{th.key}</span>
                    <span className="tb-track"><span className="tb-fill" style={{ width: `${(th.count / max) * 100}%` }} /></span>
                    <span className="tb-count">{th.count.toLocaleString()}</span>
                  </div>
                )
              })}
            </div>
          )}
        </>
      ) : (
        <p className="loading">{t('about.loading')}</p>
      )}

      <h3>{t('about.principlesTitle')}</h3>
      <ul className="about-list">
        {t('about.principles').map((item, i) => <li key={i}>{item}</li>)}
      </ul>

      {/* 투명성 블록(2026-08-04) — 홈에서 이동: 무엇을 알고 모르는지, 판정 인프라 공개 */}
      <CoverageBlock status={status} />
      <OpenInfraBlock />
    </section>
  )
}
