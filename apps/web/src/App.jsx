import { lazy, Suspense, useEffect, useState } from 'react'
import { api } from './api.js'
import SearchView from './components/SearchView.jsx'
import CompareView from './components/CompareView.jsx'
import ChangesView from './components/ChangesView.jsx'
import DatasetProfile from './components/DatasetProfile.jsx'
import AboutView from './components/AboutView.jsx'
import ConnectView from './components/ConnectView.jsx'

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
// core(A) = 라이트 블루 시스템, concierge/all(B·로컬) = 그린 시스템
document.documentElement.dataset.surface = SURFACE

// IA: 주 표면은 '데이터 찾기' 하나. 나머지는 우측 유틸리티 내비(조용한 링크),
// 비교는 선택이 생겼을 때만 하단 컨텍스트 바로 등장한다.
// '활용 사례'는 자동 생성 v0(인간 검토 전)이라 상용 표면에서 내렸다 — 검수 후 복귀.
const NAV_LINKS = [
  ...(HAS_CONCIERGE ? [{ id: 'concierge', label: 'AI 컨시어지' }] : []),
  { id: 'changes', label: '변경 이력' },
  { id: 'about', label: '소개' },
]

export default function App() {
  const [view, setView] = useState(SURFACE === 'concierge' && HAS_CONCIERGE ? 'concierge' : 'search')
  const [status, setStatus] = useState(null)
  const [profileId, setProfileId] = useState(null)
  const [compareIds, setCompareIds] = useState([])
  const [searchSeed, setSearchSeed] = useState(null) // 컨시어지 보완 노드 → 검색 프리필

  const seedSearch = (q) => {
    setSearchSeed({ q, t: Date.now() })
    setView('search')
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
      <header className="topnav">
        <button className="brand" onClick={() => setView('search')} aria-label="데이터 찾기로 이동">
          <h1>공공데이터 렌즈</h1>
        </button>
        <nav className="nav-links" aria-label="보조 메뉴">
          {NAV_LINKS.map((l) => (
            <button
              key={l.id}
              className={view === l.id ? 'nav-link active' : 'nav-link'}
              onClick={() => setView(l.id)}
            >
              {l.label}
            </button>
          ))}
          <button className="mcp-cta" onClick={() => setView('connect')}>AI에 연결</button>
        </nav>
      </header>

      <main>
        {view === 'search' && (
          <SearchView
            onOpen={setProfileId}
            compareIds={compareIds}
            onToggleCompare={toggleCompare}
            seed={searchSeed}
          />
        )}
        {view === 'compare' && (
          <>
            <button className="back-link" onClick={() => setView('search')}>← 데이터 찾기로</button>
            <CompareView
              ids={compareIds}
              onRemove={(id) => setCompareIds((p) => p.filter((x) => x !== id))}
              onOpen={setProfileId}
            />
          </>
        )}
        {view === 'changes' && <ChangesView onOpen={setProfileId} />}
        {view === 'about' && <AboutView status={status} />}
        {view === 'connect' && <ConnectView />}
        {view === 'concierge' && ConciergeView && (
          <Suspense fallback={null}>
            <ConciergeView onOpen={setProfileId} onSearch={seedSearch} />
          </Suspense>
        )}
      </main>

      {profileId && (
        <DatasetProfile recordId={profileId} onClose={() => setProfileId(null)} />
      )}

      {compareIds.length > 0 && view !== 'compare' && (
        <div className="compare-bar" role="status">
          <span className="cb-count">{compareIds.length}개 선택</span>
          <button className="cb-go" onClick={() => setView('compare')}>비교하기 →</button>
          <button className="cb-clear" onClick={() => setCompareIds([])}>비우기</button>
        </div>
      )}

      {HAS_CONCIERGE && view !== 'concierge' && (
        <button
          className="frap"
          title="AI 컨시어지"
          aria-label="AI 컨시어지 열기"
          onClick={() => setView('concierge')}
        >
          AI
        </button>
      )}

      <footer className="footer">
        <p>
          본 결과는 공공데이터포털 목록 메타데이터 기반이며 실제 데이터의 내용·품질·결합
          가능성을 보증하지 않습니다. 모든 원문 접근은{' '}
          <a href="https://www.data.go.kr" target="_blank" rel="noreferrer">공공데이터포털</a>로
          연결됩니다.
        </p>
        <p>
          {status && <>스냅샷 {status.data.currentSnapshot} · 목록 {status.data.counts.datasets.toLocaleString()}건 · </>}
          이용 기록은 익명 수집되며 DNT/GPC로 거부할 수 있습니다.{' '}
          <a href="/api/resources/privacy" target="_blank" rel="noreferrer">개인정보·로그 고지</a>
        </p>
      </footer>
    </div>
  )
}
