/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Fixed ports (OQ-8). Vite proxies /api to the backend, so the browser sees one origin. The
// rehearsal (scripts/rehearse.ts, D-77) runs an isolated copy on spare ports: it passes `--port`
// and points the proxy at its own backend with SEEDFOUNDRY_API_URL. `python run.py` sets neither.
const BACKEND = process.env.SEEDFOUNDRY_API_URL ?? 'http://127.0.0.1:8100'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5273,
    strictPort: true,
    proxy: { '/api': BACKEND },
  },
  build: {
    rolldownOptions: {
      // ECharts in its own chunk (D-59): the app's own code stays small, both load from this origin.
      output: { manualChunks: (id) => (/node_modules[\\/](echarts|zrender)[\\/]/.test(id) ? 'echarts' : undefined) },
    },
    // That chunk is about 580 kB minified (195 kB gzipped), only the charts the dashboard uses.
    chunkSizeWarningLimit: 600,
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.ts'],
  },
})
