import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  // Where the FastAPI backend lives. Override when it isn't on the default
  // localhost:8001, e.g.:  VB_BACKEND_URL=http://127.0.0.1:8001 npm run dev
  const env = loadEnv(mode, process.cwd(), '')
  const backendUrl = (
    process.env.VB_BACKEND_URL || env.VB_BACKEND_URL || 'http://localhost:8001'
  ).replace(/\/$/, '')

  return {
    plugins: [vue(), tailwindcss()],
    server: {
      port: 5174,
      // Allow the ngrok tunnel hostname. The leading-dot entry also covers
      // any future *.ngrok-free.dev hostname; host validation stays on
      // (no `allowedHosts: true`).
      allowedHosts: ['itinerary-rehire-ramrod.ngrok-free.dev', '.ngrok-free.dev'],
      proxy: {
        // Dev convenience: the Vite server proxies API calls to the FastAPI
        // backend, so the frontend works with relative URLs during development.
        '/api': backendUrl,
      },
    },
  }
})
