const BASE = '/api'

// §10 익명 식별자: 난수 ID(localStorage). DNT/GPC가 켜져 있으면 생성·전송하지 않는다(옵트아웃).
function anonId() {
  const optedOut = navigator.doNotTrack === '1' || window.globalPrivacyControl === true
  if (optedOut) return null
  let id = localStorage.getItem('datanav-anon-id')
  if (!id) {
    id = Array.from(crypto.getRandomValues(new Uint8Array(8)), (b) =>
      b.toString(16).padStart(2, '0')
    ).join('')
    localStorage.setItem('datanav-anon-id', id)
  }
  return id
}

export function anonHeaders() {
  const id = anonId()
  return id ? { 'X-Datanav-Anon-Id': id } : { 'X-Datanav-No-Log': '1' }
}

async function get(path, params) {
  const url = new URL(BASE + path, window.location.origin)
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    }
  }
  const res = await fetch(url, { headers: anonHeaders() })
  const body = await res.json()
  if (!res.ok) {
    const err = new Error(body?.error?.message || `HTTP ${res.status}`)
    err.code = body?.error?.code
    throw err
  }
  return body
}

export const api = {
  status: () => get('/status'),
  search: (params) => get('/search', params),
  searchColumns: (keywords, pageSize = 20) =>
    get('/search/columns', { keywords: keywords.join(','), pageSize }),
  dataset: (id, view) => get(`/datasets/${encodeURIComponent(id)}`, { view }),
  structure: (id) => get(`/datasets/${encodeURIComponent(id)}/structure`),
  compare: (ids) => get('/compare', { ids: ids.join(',') }),
  changes: (params) => get('/changes', params),
  stats: (axis, limit) => get('/stats', { axis, limit }),
}
