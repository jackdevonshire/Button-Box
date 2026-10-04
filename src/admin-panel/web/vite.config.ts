import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The built app is served by Flask from app/static/web, so asset URLs live under /static/web/.
// In development (npm run dev) API calls are proxied to the Flask server running on port 80.
export default defineConfig({
  base: '/static/web/',
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  build: {
    outDir: '../app/static/web',
    emptyOutDir: true,
    // Served locally, so one bundle is fine
    chunkSizeWarningLimit: 1000,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:80',
    },
  },
})
