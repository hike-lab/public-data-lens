// API 스텁 — 모든 /api/* 를 고정 픽스처로 응답한다(카탈로그 갱신에 테스트가 깨지지 않게).
// 라이브 LLM 호출 금지: 컨시어지 스트림도 합성 SSE 픽스처다.
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { expect } from '@playwright/test'

const dir = path.dirname(fileURLToPath(import.meta.url))
const fx = (name) => readFileSync(path.join(dir, 'fixtures', name), 'utf-8')

// 구조 관측이 있는 고정 레코드(픽스처 캡처 시 선정) — 프로필·구조 탭 시나리오용
export const RID = fx('.rid').trim()
export const CARD_TITLE = JSON.parse(fx('dataset-card.json')).data.dataset.title
// 규칙 개수는 픽스처에서 도출(UI·테스트 모두 하드코딩 금지 — 가이드 §3.2)
export const RULES_COUNT = JSON.parse(fx('resources-rules.json')).rules.length

export async function stubApi(page) {
  const json = (body) => ({ status: 200, contentType: 'application/json', body })
  await page.route('**/api/**', (route) => {
    const url = new URL(route.request().url())
    const p = url.pathname
    if (p === '/api/status') return route.fulfill(json(fx('status.json')))
    if (p === '/api/resources/rules') return route.fulfill(json(fx('resources-rules.json')))
    if (p === '/api/resources/eval') return route.fulfill(json(fx('resources-eval.json')))
    if (p === '/api/plan') return route.fulfill(json(fx('plan.json')))
    if (p === '/api/search/columns') return route.fulfill(json(fx('search-columns.json')))
    if (p === '/api/search') {
      const q = url.searchParams.get('query')
      if (q === '존재하지않는검색어') return route.fulfill(json(fx('search-empty.json')))
      return route.fulfill(json(q ? fx('search-query.json') : fx('search-initial.json')))
    }
    if (p.endsWith('/structure')) return route.fulfill(json(fx('dataset-structure.json')))
    if (p.startsWith('/api/datasets/')) return route.fulfill(json(fx('dataset-card.json')))
    if (p === '/api/compare') return route.fulfill(json(fx('compare.json')))
    if (p === '/api/changes') return route.fulfill(json(fx('changes.json')))
    if (p === '/api/stats') return route.fulfill(json(fx('stats-theme.json')))
    if (p === '/api/concierge/status') return route.fulfill(json(fx('concierge-status.json')))
    if (p === '/api/concierge/stream') {
      return route.fulfill({ status: 200, contentType: 'text/event-stream', body: fx('concierge-stream.sse') })
    }
    return route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: '{"error":{"code":"DATASET_NOT_FOUND","message":"스텁 미정의 경로","details":{},"sourceSnapshot":null}}',
    })
  })
}

// 스크린샷 대조 — CI(linux)에서는 플랫폼 의존 렌더링 때문에 건너뛴다(설정 파일 머리 주석 참조)
export async function shoot(page, name) {
  if (process.env.SKIP_VISUAL) return
  await expect(page).toHaveScreenshot(name, { fullPage: true })
}
