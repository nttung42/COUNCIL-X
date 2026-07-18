import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev proxy: forward /api to backend orchestrator when it exists.
// Override with VITE_API_TARGET; when running with VITE_USE_FIXTURE=true the
// proxy is never hit because apiClient short-circuits to local fixtures.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
