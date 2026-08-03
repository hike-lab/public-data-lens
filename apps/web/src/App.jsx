import { lazy, Suspense, useEffect, useState } from 'react'
import { api } from './api.js'
import SearchView from './components/SearchView.jsx'
import CompareView from './components/CompareView.jsx'
import ChangesView from './components/ChangesView.jsx'
import CasesView from './components/CasesView.jsx'
import DatasetProfile from './components/DatasetProfile.jsx'

const DISCLAIMER =
  '본 결과는 공공데이터포털 목록 메타데이터 기반이며 실제 데이터의 내용·품질·결합 가능성을 보증하지 않습니다.'

// 배포 표면(빌드 시 결정): 'core' = MCP 배포 동반 웹(비생성형만),
// 'concierge' = 별도 컨시어지 서비스(컨시어지 중심 + 보조 검색), 'all' = 로컬 개발 기본
const SURFACE = import.meta.env.VITE_SURFACE || 'all'

// 컨시어지 뷰는 파일이 존재할 때만 로드한다(공개 스냅샷에는 미포함) —
// 파일 부재 시 import.meta.glob이 빈 객체를 반환해 표면 자체가 사라진다.
const _czModules = import.meta.glob('./components/ConciergeView.jsx')
const _czLoader = _czModules['./components/ConciergeView.jsx']
const ConciergeView = _czLoader ? lazy(_czLoader) : null
const HAS_CONCIERGE = ConciergeView !== null && SURFACE !== 'core'

// 표면별 테마 스위치(styles.css의 :root[data-surface] 토큰 블록과 짝):
// core(A) = 구글 톤(화이트·블루·절제), concierge/all(B·로컬) = 그린 시스템
document.documentElement.dataset.surface = SURFACE

const ALL_TABS = [
  { id: 'search', label: '검색' },
  { id: 'concierge', label: 'AI 컨시어지' },
  { id: 'compare', label: '비교' },
  { id: 'changes', label: '변경 피드' },
  { id: 'cases', label: '활용 사례' },
]
const TABS = ALL_TABS.filter((t) =>
  t.id === 'concierge' ? HAS_CONCIERGE
  : SURFACE === 'concierge' ? t.id === 'search'
  : true,
)

export default function App() {
  const [tab, setTab] = useState(SURFACE === 'concierge' && HAS_CONCIERGE ? 'concierge' : 'search')
  const [status, setStatus] = useState(null)
  const [profileId, setProfileId] = useState(null)
  const [compareIds, setCompareIds] = useState([])
  const [searchSeed, setSearchSeed] = useState(null) // 컨시어지 보완 노드 → 검색 프리필

  const seedSearch = (q) => {
    setSearchSeed({ q, t: Date.now() })
    setTab('search')
  }

  useEffect(() => {
    api.status().then(setStatus).catch(() => setStatus(null))
  }, [])

  const toggleCompare = (id) => {
    setCompareIds((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : prev.length >= 5
          ? prev
          : [...prev, id],
    )
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>공공데이터 렌즈</h1>
          <p className="tagline">
            하고 싶은 일을 말하면 AI Ready 관점으로 정밀하게 투영하는 공공데이터 초점 레이어
          </p>
        </div>
        {status && (
          <div className="status-chip" title={`릴리스 ${status.data.release}`}>
            <span>스냅샷 {status.data.currentSnapshot}</span>
            <span>{status.data.counts.datasets.toLocaleString()}건</span>
            {status.data.structureCoverage && (
              <span title="실제 파일에서 구조(원본 컬럼·예시값)가 관측된 FILE 데이터 수">
                구조 확인 {status.data.structureCoverage.recordsAvailable.toLocaleString()}건
              </span>
            )}
            <span>분석 기준 {status.data.processedAt?.slice(0, 10)}</span>
          </div>
        )}
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={tab === t.id ? 'tab active' : 'tab'}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {t.id === 'compare' && compareIds.length > 0 && (
              <span className="badge">{compareIds.length}</span>
            )}
          </button>
        ))}
      </nav>

      <main>
        {tab === 'search' && (
          <SearchView
            onOpen={setProfileId}
            compareIds={compareIds}
            onToggleCompare={toggleCompare}
            seed={searchSeed}
          />
        )}
        {tab === 'compare' && (
          <CompareView
            ids={compareIds}
            onRemove={(id) => setCompareIds((p) => p.filter((x) => x !== id))}
            onOpen={setProfileId}
          />
        )}
        {tab === 'changes' && <ChangesView onOpen={setProfileId} />}
        {tab === 'cases' && <CasesView onOpen={setProfileId} />}
        {tab === 'concierge' && ConciergeView && (
          <Suspense fallback={null}>
            <ConciergeView onOpen={setProfileId} onSearch={seedSearch} />
          </Suspense>
        )}
      </main>

      {profileId && (
        <DatasetProfile recordId={profileId} onClose={() => setProfileId(null)} />
      )}

      {HAS_CONCIERGE && tab !== 'concierge' && (
        <button
          className="frap"
          title="AI 컨시어지"
          aria-label="AI 컨시어지 열기"
          onClick={() => setTab('concierge')}
        >
          AI
        </button>
      )}

      <footer className="footer">
        <p>{DISCLAIMER}</p>
        <p>
          모든 원문 접근은{' '}
          <a href="https://www.data.go.kr" target="_blank" rel="noreferrer">
            공공데이터포털
          </a>
          로 연결됩니다. 본 서비스는 포털을 대체하지 않는 탐색·판단 계층입니다.
        </p>
        <p>
          이용 기록은 익명으로 수집되며 브라우저의 DNT/GPC 설정으로 거부할 수 있습니다.{' '}
          <a href="/api/resources/privacy" target="_blank" rel="noreferrer">
            개인정보·로그 고지
          </a>
        </p>
      </footer>
    </div>
  )
}
