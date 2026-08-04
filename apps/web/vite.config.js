import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // DATANAV_API_PROXY로 대상 API를 바꿀 수 있다(기본: 로컬 8000)
      '/api': process.env.DATANAV_API_PROXY || 'http://127.0.0.1:8000',
    },
  },
})
