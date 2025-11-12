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
      '/api/user': {
        target: 'http://user:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/user/, ''),
      },
      '/api/event': {
        target: 'http://event:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/event/, ''),
      },
      '/api/group': {
        target: 'http://group:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/group/, ''),
      },
      '/api/rating': {
        target: 'http://rating:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/rating/, ''),
      },
      '/api/safety': {
        target: 'http://safety:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/safety/, ''),
      },
    },
  },
})
