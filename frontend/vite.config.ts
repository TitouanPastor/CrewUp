import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/api/v1/users': {
        target: 'http://localhost:8005',
        changeOrigin: true,
      },
      '/api/v1/events': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/v1/groups': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api/v1/ws/groups': {
        target: 'ws://localhost:8002',
        ws: true,
      },
      '/api/v1/ratings': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/api/v1/safety': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
      '/api/v1/moderation': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
    },
  },
})
