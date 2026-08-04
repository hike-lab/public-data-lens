// 초경량 pushState 라우터 — 의존성 없이 URL을 뷰 상태의 단일 진실로 삼는다.
// nginx try_files·vite preview의 SPA 폴백이 딥링크를 이미 지원한다.
import { useCallback, useEffect, useState } from 'react'

const VIEW_PATH = {
  search: '/', explore: '/explore', compare: '/compare', changes: '/changes',
  about: '/about', connect: '/connect', concierge: '/concierge',
}
const PATH_VIEW = Object.fromEntries(Object.entries(VIEW_PATH).map(([v, p]) => [p, v]))

export const pathFor = (view) => VIEW_PATH[view] || '/'

export function parseRoute(loc = window.location) {
  const params = new URLSearchParams(loc.search)
  const m = loc.pathname.match(/^\/datasets\/([^/]+)$/)
  if (m) {
    return {
      view: 'search', // 직접 진입 시 밑판은 검색
      profileId: decodeURIComponent(m[1]),
      lens: params.get('lens') || 'overview',
      params,
    }
  }
  return { view: PATH_VIEW[loc.pathname] || 'search', profileId: null, lens: null, params }
}

export function useRoute() {
  const [route, setRoute] = useState(() => parseRoute())
  useEffect(() => {
    const onPop = () => setRoute(parseRoute())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  const navigate = useCallback((url, { replace = false } = {}) => {
    if (replace) window.history.replaceState({ app: true }, '', url)
    else window.history.pushState({ app: true }, '', url)
    setRoute(parseRoute())
  }, [])
  return [route, navigate]
}
