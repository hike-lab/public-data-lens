// 단위 테스트 전용 설정 — Playwright(tests/)와 분리해 src/ 안의 *.test.jsx만 대상
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{js,jsx}'],
    globals: true,
  },
})
