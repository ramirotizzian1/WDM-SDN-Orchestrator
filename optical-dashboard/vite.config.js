
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/onos/api': {
        target: 'http://localhost:30181',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/onos\/api/, '/onos/v1')
      }
    }
  }
})
