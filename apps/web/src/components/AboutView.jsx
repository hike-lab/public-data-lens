import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { CoverageBlock, OpenInfraBlock } from './HomeBlocks.jsx'

export default function AboutView({ status }) {
  const [themes, setThemes] = useState(null)

  useEffect(() => {
    api.stats('theme', 6).then((b) => setThemes(b.data.buckets)).catch(() => setThemes(null))
  }, [])

  const s = status?.data

  return (
    <section className="about">
      <div className="about-hero">
        <h2>하고 싶은 일을 말하면, 근거와 함께 공공데이터를 찾아드립니다</h2>
        <p>
          공공데이터 렌즈는 <a href="https://www.data.go.kr" target="_blank" rel="noreferrer">공공데이터포털</a>의
          월간 목록(약 9.6만 건)을 정규화해, 어떤 데이터가 존재하고 어떤 후보가 검토할 가치가
          있는지를 <strong>근거 수준과 함께</strong> 제시하는 탐색·판단 계층입니다. 검색·비교·구조
          확인의 모든 판정은 버전이 관리되는 규칙으로 재현 가능하게 수행되며, 실제 데이터의
          내용·품질을 보증하지 않고 모든 원문 접근은 포털로 연결합니다.
        </p>
        <p className="about-research">
          중앙대학교 HIKE 연구실이 운영하는 AIRD(AI-Ready Data) 표준안 실증 프로젝트이며,
          생성형 AI 컨시어지는 별도 서비스로 제공됩니다.
        </p>
      </div>

      <h3>카탈로그 현황</h3>
      {s ? (
        <>
          <div className="stat-tiles">
            <div className="stat-tile">
              <span className="stat-v">{s.counts.datasets.toLocaleString()}</span>
              <span className="stat-k">목록 데이터셋</span>
            </div>
            {s.structureCoverage && (
              <div className="stat-tile">
                <span className="stat-v">{s.structureCoverage.recordsAvailable.toLocaleString()}</span>
                <span className="stat-k">실파일 구조 확인</span>
              </div>
            )}
            <div className="stat-tile">
              <span className="stat-v">{s.currentSnapshot}</span>
              <span className="stat-k">현재 스냅샷 (월간 갱신)</span>
            </div>
            <div className="stat-tile">
              <span className="stat-v">{s.processedAt?.slice(0, 10)}</span>
              <span className="stat-k">분석 기준일</span>
            </div>
          </div>
          {themes && (
            <div className="theme-bars">
              {themes.map((t) => {
                const max = themes[0].count
                return (
                  <div className="theme-bar" key={t.key}>
                    <span className="tb-label">{t.key}</span>
                    <span className="tb-track"><span className="tb-fill" style={{ width: `${(t.count / max) * 100}%` }} /></span>
                    <span className="tb-count">{t.count.toLocaleString()}</span>
                  </div>
                )
              })}
            </div>
          )}
        </>
      ) : (
        <p className="loading">현황을 불러오는 중…</p>
      )}

      <h3>데이터 출처와 원칙</h3>
      <ul className="about-list">
        <li>출처: 행정안전부 공공데이터포털 목록개방현황(월간). 본 서비스는 목록 메타데이터의 가공물만 다루며 실데이터를 재배포하지 않습니다.</li>
        <li>기능에 따라 근거 수준이 다릅니다 — 목록 기반(<code>CATALOG_METADATA_ONLY</code>)과 실파일 관측(<code>FILE_OBSERVATION</code>)을 구분해 표시합니다.</li>
        <li>이용 기록은 원 IP를 저장하지 않는 익명 로그로 수집되며, 브라우저 DNT/GPC로 거부할 수 있습니다. <a href="/api/resources/privacy" target="_blank" rel="noreferrer">개인정보·로그 고지</a></li>
        <li>목록 메타데이터의 오류 의심은 <a href="https://github.com/hike-lab/public-data-lens/issues" target="_blank" rel="noreferrer">GitHub Issues</a>로 제보해 주세요 — 검토 후 제공 기관에 환류합니다.</li>
      </ul>

      {/* 투명성 블록(2026-08-04) — 홈에서 이동: 무엇을 알고 모르는지, 판정 인프라 공개 */}
      <CoverageBlock status={status} />
      <OpenInfraBlock />
    </section>
  )
}
