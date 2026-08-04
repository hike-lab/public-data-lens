import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { api, supportsPlan } from './api.js'
import { useRoute, pathFor } from './router.js'
import SearchView from './components/SearchView.jsx'
import CompareView from './components/CompareView.jsx'
import ChangesView from './components/ChangesView.jsx'
import DatasetProfile from './components/DatasetProfile.jsx'
import AboutView from './components/AboutView.jsx'
import ExploreView from './components/ExploreView.jsx'
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
// 상단은 둘러보기·소개·MCP 연결(2026-08-04 결정) — 변경 이력은 푸터(라우트는 유지)
const NAV_LINKS = [
  ...(HAS_CONCIERGE ? [{ id: 'concierge', label: 'AI 컨시어지' }] : []),
  { id: 'explore', label: '둘러보기' },
  { id: 'about', label: '소개' },
  { id: 'connect', label: 'MCP 연결' },
]

export default function App() {
  // URL이 뷰 상태의 단일 진실: 뷰·프로필·렌즈·검색 조건이 전부 URL에 담긴다
  const [route, navigate] = useRoute()
  // 프로필이 열려 있는 동안 밑판은 직전 뷰를 유지한다(변경 이력·컨시어지에서 열어도 화면 유지)
  const underlay = useRef('search')
  if (!route.profileId) underlay.current = route.view
  const view = route.profileId ? underlay.current : route.view
  const [status, setStatus] = useState(null)
  const [compareIds, setCompareIds] = useState([])
  const [searchSeed, setSearchSeed] = useState(null) // 컨시어지 보완 노드 → 검색 프리필

  // 검색 조건이 담긴 마지막 URL — 다른 뷰에 다녀와도 검색 상태가 복원된다
  const lastSearchUrl = useRef('/')
  if (view === 'search' && !route.profileId) {
    lastSearchUrl.current = window.location.pathname + window.location.search
  }

  // 컨시어지 전용 표면은 루트 진입 시 컨시어지로 (URL은 유지)
  useEffect(() => {
    if (SURFACE === 'concierge' && HAS_CONCIERGE && window.location.pathname === '/') {
      navigate('/concierge', { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const goto = (v) => navigate(v === 'search' ? lastSearchUrl.current : pathFor(v))

  // 브랜드 클릭 = 초기 홈(pristine). 마지막 검색 복원(goto('search'))과 달리 '/'로
  // 이동하고, 검색 상태는 URL이 단일 진실이므로 리마운트로 초기화한다.
  const [homeKey, setHomeKey] = useState(0)
  const goHome = () => {
    navigate('/')
    setHomeKey((k) => k + 1)
  }

  const openProfile = (id) => navigate(`/datasets/${encodeURIComponent(id)}`)
  const closeProfile = () => {
    // 앱 내부에서 열었으면 이전 화면으로(뒤로), 새 탭 직접 진입이면 검색으로
    if (window.history.state?.app) window.history.back()
    else navigate(lastSearchUrl.current, { replace: true })
  }

  const seedSearch = (q) => {
    setSearchSeed({ q, t: Date.now() })
    goto('search')
  }

  useEffect(() => {
    api.status().then(setStatus).catch(() => setStatus(null))
  }, [])

  // 계약 v1.5 기능(POST /api/plan) 게이팅 — 구버전 서버에서는 진입점을 숨긴다(P0)
  const planAvailable = supportsPlan(status)

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
        <button className="brand" onClick={goHome} aria-label="Public Data Lens 홈">
          <h1>Public Data Lens</h1>
        </button>
        <nav className="nav-links" aria-label="보조 메뉴">
          {NAV_LINKS.map((l) => (
            <button
              key={l.id}
              className={view === l.id ? 'nav-link active' : 'nav-link'}
              onClick={() => goto(l.id)}
            >
              {l.label}
            </button>
          ))}
        </nav>
      </header>

      <main>
        {view === 'search' && (
          <SearchView
            key={homeKey}
            onOpen={openProfile}
            compareIds={compareIds}
            onToggleCompare={toggleCompare}
            seed={searchSeed}
            status={status}
            planAvailable={planAvailable}
            urlParams={route.profileId ? null : route.params}
            onUrlChange={(qs) => {
              if (route.profileId) return // 프로필이 열린 동안은 URL을 건드리지 않는다
              navigate(qs ? `/?${qs}` : '/', { replace: true })
            }}
          />
        )}
        {view === 'compare' && (
          <>
            <button className="back-link" onClick={() => goto('search')}>← 데이터 찾기로</button>
            <CompareView
              ids={compareIds}
              onRemove={(id) => setCompareIds((p) => p.filter((x) => x !== id))}
              onOpen={openProfile}
            />
          </>
        )}
        {view === 'explore' && (
          <ExploreView
            onOpen={openProfile}
            planAvailable={planAvailable}
            onTryPurpose={(p) => navigate(`/?mode=purpose&purpose=${encodeURIComponent(p)}`)}
          />
        )}
        {view === 'changes' && <ChangesView onOpen={openProfile} />}
        {view === 'about' && <AboutView status={status} />}
        {view === 'connect' && <ConnectView />}
        {view === 'concierge' && ConciergeView && (
          <Suspense fallback={null}>
            <ConciergeView onOpen={openProfile} onSearch={seedSearch} />
          </Suspense>
        )}
      </main>

      {route.profileId && (
        <DatasetProfile
          recordId={route.profileId}
          onOpen={openProfile}
          planAvailable={planAvailable}
          lens={route.lens}
          onLensChange={(l) =>
            navigate(`/datasets/${encodeURIComponent(route.profileId)}?lens=${l}`, { replace: true })}
          onClose={closeProfile}
        />
      )}

      {compareIds.length > 0 && view !== 'compare' && (
        <div className="compare-bar" role="status">
          <span className="cb-count">{compareIds.length}개 선택</span>
          <button className="cb-go" onClick={() => goto('compare')}>비교하기 →</button>
          <button className="cb-clear" onClick={() => setCompareIds([])}>비우기</button>
        </div>
      )}

      {HAS_CONCIERGE && view !== 'concierge' && (
        <button
          className="frap"
          title="AI 컨시어지"
          aria-label="AI 컨시어지 열기"
          onClick={() => goto('concierge')}
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
          <button className="footer-link" onClick={() => goto('changes')}>변경 이력</button> ·
          이용 기록은 익명 수집되며 DNT/GPC로 거부할 수 있습니다.{' '}
          <a href="/api/resources/privacy" target="_blank" rel="noreferrer">개인정보·로그 고지</a>
        </p>
      </footer>
    </div>
  )
}
