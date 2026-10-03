import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // Dev convenience: the Vite server proxies API calls to the FastAPI backend,
      // so the frontend works with relative URLs during development.
      '/api': 'http://localhost:8000',
    },
  },
})
