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
          공공데이터 렌즈는 <a href="https://www.data.go.kr" target="_blank" rel="noreferrer">공공데이터포털</a>에
          등록된 약 9만 6천 건의 데이터를 목적에 맞게 찾고 비교하는 서비스입니다. 데이터가
          검색된 이유와 확인된 정보의 범위를 함께 보여주어, 어떤 데이터를 먼저 검토해야 할지
          판단할 수 있게 합니다. 검색과 비교 결과는 공개된 기준에 따라 만들어집니다. 같은
          데이터와 같은 조건에는 같은 결과가 나오며, 적용된 기준과 버전도 확인할 수 있습니다.
          다만 이 서비스의 결과가 실제 데이터의 내용이나 품질을 보증하는 것은 아닙니다.
          데이터 이용과 원문 확인은 공공데이터포털에서 이루어집니다.
        </p>
        <p className="about-research">
          <a href="http://hike.cau.ac.kr" target="_blank" rel="noreferrer">중앙대학교 HIKE 연구실</a>이
          운영하며, 현재 제정 중인 AI Ready Data 표준안(정보통신단체표준)에 앞서 개발된
          독립 구현으로, 표준안의 실현 가능성을 실제 공공데이터로 검증하는 프로젝트이기도
          합니다.
        </p>
      </div>

      <h3>카탈로그 현황</h3>
      {s ? (
        <>
          <div className="stat-tiles">
            <div className="stat-tile">
              <span className="stat-v">{s.counts.datasets.toLocaleString()}</span>
              <span className="stat-k">전체 목록 수</span>
            </div>
            {s.structureCoverage && (
              <div className="stat-tile">
                <span className="stat-v">{s.structureCoverage.recordsAvailable.toLocaleString()}</span>
                <span className="stat-k">실파일 구조 확인</span>
              </div>
            )}
            <div className="stat-tile">
              <span className="stat-v">{s.currentSnapshot}</span>
              <span className="stat-k">현재 스냅샷(매월 갱신)</span>
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

      <h3>데이터 출처와 운영 원칙</h3>
      <ul className="about-list">
        <li>공공데이터포털이 매월 공개하는 <a href="https://www.data.go.kr/data/15062804/fileData.do" target="_blank" rel="noreferrer">데이터 목록</a>을 바탕으로 정보를 갱신합니다. 실제 데이터를 대신 배포하지 않으며, 데이터 이용과 원문 확인은 공공데이터포털에서 이루어집니다.</li>
        <li>목록에 등록된 설명과 실제 파일에서 확인한 구조는 구분합니다. 실제 파일을 확인하지 못하면 확인되지 않았다는 사실도 함께 표시합니다. 화면에서는 각각 목록 정보 기준(<code>CATALOG_METADATA_ONLY</code>)과 실제 파일 확인(<code>FILE_OBSERVATION</code>)으로 구분합니다.</li>
        <li>서비스 이용 기록에는 접속자의 IP 주소를 저장하지 않습니다. 브라우저의 DNT 또는 GPC 설정을 통해 수집을 거부할 수 있습니다. <a href="/api/resources/privacy" target="_blank" rel="noreferrer">개인정보·로그 안내</a></li>
        <li>목록 정보에서 오류가 의심되는 경우 <a href="https://github.com/hike-lab/public-data-lens/issues" target="_blank" rel="noreferrer">GitHub Issues</a>를 통해 알려주세요. 확인한 내용은 필요한 경우 데이터 제공 기관에 전달합니다.</li>
      </ul>

      {/* 투명성 블록(2026-08-04) — 홈에서 이동: 무엇을 알고 모르는지, 판정 인프라 공개 */}
      <CoverageBlock status={status} />
      <OpenInfraBlock />
    </section>
  )
}
