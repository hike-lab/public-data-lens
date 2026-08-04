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
  return unwrap(res)
}

// 오류 모델 언랩 — HTTP 상태 코드 원문을 사용자에게 노출하지 않는다(P0).
// 서버 오류 봉투(error.message)가 있으면 그 문안을, 없으면(구버전 서버·라우트 부재 등)
// 사용자 언어의 폴백을 쓴다. 프로그램 분기는 err.code/err.status로 한다.
async function unwrap(res) {
  let body = null
  try { body = await res.json() } catch { body = null }
  if (!res.ok) {
    const err = new Error(
      body?.error?.message
      || (res.status === 404
        ? '이 기능을 서버가 아직 제공하지 않습니다 — 서버가 이전 버전일 수 있습니다. 키워드·컬럼 탐색은 계속 사용할 수 있습니다.'
        : `요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요. (오류 코드 ${res.status})`),
    )
    err.code = body?.error?.code
    err.status = res.status
    throw err
  }
  return body
}

async function post(path, payload) {
  const res = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...anonHeaders() },
    body: JSON.stringify(payload),
  })
  return unwrap(res)
}

// 서버 계약 버전 게이팅(P0) — 구버전 서버에 신계약 기능(POST /api/plan 등)을 노출하지
// 않는다. 진입점 표시에만 쓰고, 딥링크는 시도 후 사용자 문안 오류로 우아하게 강등한다.
export function supportsPlan(status) {
  const v = status?.meta?.schemaVersion
  if (!v) return false
  const [maj, min] = v.split('.').map(Number)
  return maj > 1 || (maj === 1 && min >= 5)
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
  // 판정 규칙 레지스트리 전문(§3.2) — /api/status에는 규칙 목록이 없어 이 라우트가 정본
  rules: () => get('/resources/rules'),
  // 검색 품질 지표(§3.2, v1.5) — humanReviewed 플래그를 함께 표기할 것
  evalReport: () => get('/resources/eval'),
  // 활용 계획 초안(v1.5) — 항상 DRAFT·NOT_ASSESSED, '추천'이 아니라 후보다
  plan: (purpose, region, maxCandidates = 5) => post('/plan', { purpose, region, maxCandidates }),
}
