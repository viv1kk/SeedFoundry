/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Fixed ports (OQ-8). Vite proxies /api to the backend, so the browser sees one origin.
const BACKEND = 'http://127.0.0.1:8100'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5273,
    strictPort: true,
    proxy: { '/api': BACKEND },
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.ts'],
  },
})
