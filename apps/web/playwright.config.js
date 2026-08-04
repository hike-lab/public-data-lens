// 시각 회귀 베이스라인(리디자인 런북 STEP 1) — API는 전부 고정 픽스처로 스텁되어
// 카탈로그 갱신·서버 유무와 무관하게 결정적으로 렌더된다.
//
// 스크린샷 베이스라인은 플랫폼 의존(폰트 렌더링)이라 생성 플랫폼(darwin)에서만 대조한다.
// CI(linux)는 SKIP_VISUAL=1로 스크린샷 대조를 건너뛰고 DOM 스모크(화면 구성 검증)만 수행한다
// — 의미 없는 자동 재생성 통과보다 정직한 축소가 낫다. linux 대조가 필요해지면
// Playwright 공식 Docker 이미지로 베이스라인을 재생성한다.
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  reporter: [['list']],
  timeout: 30_000,
  expect: {
    toHaveScreenshot: { animations: 'disabled', caret: 'hide', maxDiffPixels: 80 },
  },
  use: {
    contextOptions: { reducedMotion: 'reduce' },
    locale: 'ko-KR',
    timezoneId: 'Asia/Seoul',
  },
  webServer: [
    {
      command: 'npm run build:core -- --outDir dist-test-core && npx vite preview --outDir dist-test-core --host 127.0.0.1 --port 4501 --strictPort',
      url: 'http://127.0.0.1:4501',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: 'npm run build -- --outDir dist-test-all && npx vite preview --outDir dist-test-all --host 127.0.0.1 --port 4502 --strictPort',
      url: 'http://127.0.0.1:4502',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
  projects: [
    { name: 'core-desktop', testMatch: /visual-core/, use: { baseURL: 'http://127.0.0.1:4501', viewport: { width: 1280, height: 800 } } },
    { name: 'core-mobile', testMatch: /visual-core/, use: { baseURL: 'http://127.0.0.1:4501', viewport: { width: 375, height: 812 } } },
    // 컨시어지 화면(WarningPanel 통합 범위) — all 표면 빌드
    { name: 'all-desktop', testMatch: /visual-concierge/, use: { baseURL: 'http://127.0.0.1:4502', viewport: { width: 1280, height: 800 } } },
    { name: 'all-mobile', testMatch: /visual-concierge/, use: { baseURL: 'http://127.0.0.1:4502', viewport: { width: 375, height: 812 } } },
  ],
})
