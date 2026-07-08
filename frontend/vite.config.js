import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The proxy forwards any request starting with /api to Flask on :5000.
// This means the frontend can just call "/api/..." with no CORS drama in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
})
