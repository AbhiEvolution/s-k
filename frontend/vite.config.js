import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    // The app calls relative /api/v1/... URLs. In dev, forward them to the
    // nginx gateway (docker compose up, or the local nginx config).
    proxy: {
      '/api': 'http://localhost',
    },
  },
})
