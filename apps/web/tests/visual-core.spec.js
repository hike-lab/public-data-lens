// 코어 표면(VITE_SURFACE=core) 시각 베이스라인 — 런북 STEP 1 대상 9화면.
// 모든 화면은 DOM 스모크(구성 검증)를 항상 수행하고, 스크린샷 대조는 SKIP_VISUAL이 아닐 때만.
import { test, expect } from '@playwright/test'
import { stubApi, shoot, CARD_TITLE, RID, RULES_COUNT } from './stub.js'

test.beforeEach(async ({ page }) => {
  await stubApi(page)
  await page.goto('/')
  await expect(page.locator('.brand h1')).toHaveText('Public Data Lens')
})

async function searchFor(page, text) {
  await page.locator('.search-shell input').fill(text)
  await page.locator('.searchbar button[type=submit]').click()
  await expect(page.locator('.result-row').first()).toBeVisible()
}

test('홈 — 검색 단독(pristine)', async ({ page }) => {
  await expect(page.locator('.hero-title')).toContainText('어떤 데이터를 찾고 계신가요')
  await expect(page.locator('.hero-sub')).toContainText('이해하고 활용하는 것으로')
  await expect(page.locator('.examples .chip').first()).toBeVisible()
  // 홈은 검색으로 끝난다 — 쇼케이스·투명성 블록은 둘러보기·소개로 이동
  await expect(page.locator('.home-block')).toHaveCount(0)
  // 상단 메뉴는 둘러보기·소개·MCP 연결 — 변경 이력은 푸터로
  await expect(page.locator('.nav-links .nav-link')).toHaveCount(3)
  await expect(page.locator('.footer .footer-link')).toContainText('변경 이력')
  await shoot(page, 'home.png')
})

test('둘러보기 — 서사·해부·구조 실물', async ({ page }) => {
  await page.locator('.nav-link', { hasText: '둘러보기' }).click()
  // §3 #3 탐색 서사 — 과정(해석→후보→한계)이 실제 plan 응답으로 렌더된다
  await expect(page.locator('.story-steps')).toContainText('목적 해석')
  await expect(page.locator('.story-block')).toContainText('DRAFT')
  // §3 #5 Dataset anatomy — 원본 컬럼명 그대로 + 관측 출처
  await expect(page.locator('.anatomy-block .structure-table')).toBeVisible()
  // §3 #4 — 구조 관측이 있는 최신 수정분 3건
  await expect(page.locator('.live-block .result-row')).toHaveCount(3)
  await shoot(page, 'explore.png')
})

test('검색 결과 — 어린이 보호구역', async ({ page }) => {
  await searchFor(page, '어린이 보호구역')
  await expect(page.locator('.toolbar .result-meta')).toContainText('총')
  // v1.6: '왜 이 결과인가' — 서버가 준 matchedFields 표시(프론트 재추정 아님)
  await expect(page.locator('.matched-columns').first()).toContainText('검색어 일치')
  await expect(page.locator('.sort-select')).toBeVisible()
  await shoot(page, 'search-results.png')
})

test('컬럼 검색 결과 — 위도, 경도', async ({ page }) => {
  await page.locator('.seg button', { hasText: '컬럼' }).click()
  await page.locator('.search-shell input').fill('위도, 경도')
  await page.locator('.searchbar button[type=submit]').click()
  await expect(page.locator('.matched-columns').first()).toBeVisible()
  await expect(page.locator('.toolbar .result-meta')).toContainText('구조가 관측된')
  await shoot(page, 'search-columns.png')
})

test('키보드 접근 — 결과 행을 포커스해 Enter로 연다 (WCAG 2.1.1)', async ({ page }) => {
  await searchFor(page, '어린이 보호구역')
  const row = page.locator('.row-main').first()
  await expect(row).toHaveAttribute('role', 'button')
  await row.focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('.profile h2')).toContainText(CARD_TITLE)
})

test('빈 결과 — 조회 범위를 명시한다 (§4.5)', async ({ page }) => {
  await page.locator('.search-shell input').fill('존재하지않는검색어')
  await page.locator('.searchbar button[type=submit]').click()
  await expect(page.locator('.empty-title')).toContainText('이 조건으로는 결과가 없습니다')
  await expect(page.locator('.empty-body')).toContainText('조회 범위')
})

test('데이터셋 프로필 — card 탭', async ({ page }) => {
  await searchFor(page, '어린이 보호구역')
  await page.locator('.row-title strong', { hasText: CARD_TITLE }).first().click()
  await expect(page.locator('.profile h2')).toContainText(CARD_TITLE)
  await shoot(page, 'profile-card.png')
})

test('데이터셋 프로필 — structure 탭', async ({ page }) => {
  await searchFor(page, '어린이 보호구역')
  await page.locator('.row-title strong', { hasText: CARD_TITLE }).first().click()
  await page.locator('.drawer-tabs .tab', { hasText: '데이터 구조' }).click()
  await expect(page.locator('.structure-table').first()).toBeVisible()
  await shoot(page, 'profile-structure.png')
})

test('데이터셋 프로필 — evidence 렌즈(§5.4)', async ({ page }) => {
  await searchFor(page, '어린이 보호구역')
  await page.locator('.row-title strong', { hasText: CARD_TITLE }).first().click()
  await page.locator('.drawer-tabs .tab', { hasText: '근거' }).click()
  await expect(page.locator('.profile h2')).toContainText('근거')
  await expect(page.locator('.profile')).toContainText('card-projection-v1.0')
  await shoot(page, 'profile-evidence.png')
})

test('활용 초안 렌즈(§5.5) — DRAFT·NOT_ASSESSED 상시 노출, fitSignals 개별', async ({ page }) => {
  await page.goto(`/datasets/${RID}?lens=uses`)
  await page.locator('.uses-form input').fill('어린이 보호구역 교통안전 분석')
  await page.locator('.uses-form button').click()
  const lens = page.locator('.uses-lens')
  await expect(lens.locator('.uses-status')).toContainText('DRAFT')
  await expect(lens.locator('.uses-status')).toContainText('NOT_ASSESSED')
  await expect(lens).toContainText('CANDIDATE_ONLY')
  await expect(lens.locator('.key-field', { hasText: '검색 관련도' }).first()).toBeVisible()
  await expect(lens).not.toContainText('추천') // '추천' 명명 금지
  await shoot(page, 'profile-uses.png')
})

test('원본 데이터 렌즈 — 기술 표현 3뷰, 정규화 기본, 포털 원문 링크 동반', async ({ page }) => {
  await page.goto(`/datasets/${RID}?lens=raw`)
  await expect(page.locator('.profile h2')).toContainText('원본 데이터')
  await expect(page.locator('.raw-tabs .tab')).toHaveCount(3)
  await expect(page.locator('.raw-tabs .tab.active')).toHaveText('정규화')
  await expect(page.locator('.json-view')).toContainText(CARD_TITLE)
  // 외부 링크는 렌즈 탭이 아니다 — tablist 밖, 같은 행
  await expect(page.locator('.drawer-head .tab-link')).toContainText('포털 원문')
  await expect(page.locator('.drawer-tabs [role=tab]')).toHaveCount(5)
  await shoot(page, 'profile-raw.png')
})

test('딥링크 — 데이터셋 URL 직접 진입과 Escape 닫기', async ({ page }) => {
  await page.goto(`/datasets/${RID}`)
  await expect(page.locator('.drawer[role=dialog]')).toBeVisible()
  await expect(page.locator('.profile h2')).toContainText(CARD_TITLE)
  await page.keyboard.press('Escape')
  await expect(page.locator('.drawer')).toHaveCount(0)
})

test('URL 복원 — 검색 상태가 주소에 담기고 재현된다', async ({ page }) => {
  await searchFor(page, '어린이 보호구역')
  await expect(page).toHaveURL(/q=/)
  const url = page.url()
  await page.goto(url) // 새 탭에 붙여넣기와 동일
  await expect(page.locator('.result-row').first()).toBeVisible()
  await expect(page.locator('.toolbar .result-meta')).toContainText('총')
})

test('비교 — 2건 선택', async ({ page }) => {
  await searchFor(page, '어린이 보호구역')
  const checks = page.locator('.compare-check input')
  await checks.nth(0).check()
  await checks.nth(1).check()
  await expect(page.locator('.compare-bar')).toContainText('2개 선택')
  await page.locator('.cb-go').click()
  await expect(page.locator('.compare-table')).toBeVisible()
  await shoot(page, 'compare.png')
})

test('변경 이력 — 푸터 진입', async ({ page }) => {
  await page.locator('.footer-link', { hasText: '변경 이력' }).click()
  await expect(page.locator('main')).toContainText('변경') // 빈 기준 스냅샷 상태도 정상 화면
  await shoot(page, 'changes.png')
})

test('소개 — 투명성 블록 포함', async ({ page }) => {
  await page.locator('.nav-link', { hasText: '소개' }).click()
  await expect(page.locator('.stat-tiles .stat-tile').first()).toBeVisible()
  await expect(page.locator('.theme-bars')).toBeVisible()
  // §3.1 Coverage — 세 숫자와 스냅샷 지연(홈에서 이동)
  const cov = page.locator('.cov-figures')
  await expect(cov).toContainText('96,056')
  await expect(cov).toContainText('83,695')
  await expect(cov).toContainText('59,395')
  await expect(page.locator('.cov-lag')).toContainText('지연')
  // §3.2 Open Infrastructure — 규칙 레지스트리(개수는 응답 length), 폐기 표시 유지
  await expect(page.locator('.rule-list .rule')).toHaveCount(RULES_COUNT)
  await expect(page.locator('.rule.deprecated .rule-flag')).toContainText('폐기')
  await shoot(page, 'about.png')
})

test('AI에 연결 — capability 데모가 설치 안내보다 먼저', async ({ page }) => {
  await page.locator('.nav-link', { hasText: 'MCP 연결' }).click()
  await expect(page.locator('.connect h2')).toContainText('MCP는 그 능력을 AI 안으로')
  await expect(page.locator('.mcp-url code')).toContainText('/projects/public-data-lens/mcp')
  await expect(page.locator('.cap-demo')).toContainText('후보')
  await expect(page.locator('.cap-demo')).not.toContainText('추천')
  // 등록 안내 4종(Claude 웹·앱 / Claude Code / ChatGPT 웹 / 기타)
  await expect(page.locator('.connect-acc summary')).toHaveCount(4)
  const gpt = page.locator('.connect-acc details', { hasText: 'ChatGPT 웹' })
  await gpt.locator('summary').click()
  await expect(gpt.locator('.connect-table')).toContainText('No Authentication')
  await expect(gpt.locator('.connect-table code')).toContainText('/projects/public-data-lens/mcp')
  await shoot(page, 'connect.png')
})

test('목적 모드 — 이름 대신 하려는 일로 탐색', async ({ page }) => {
  await page.locator('.seg button', { hasText: '목적' }).click()
  await page.locator('.search-shell input').fill('어린이 보호구역 교통안전을 분석하고 싶다')
  await page.locator('.searchbar button[type=submit]').click()
  await expect(page.locator('.plan-standalone .uses-status')).toContainText('DRAFT')
  await expect(page.locator('.plan-standalone')).toContainText('후보 데이터셋')
  await expect(page).toHaveURL(/mode=purpose/)
  await shoot(page, 'search-purpose.png')
})
