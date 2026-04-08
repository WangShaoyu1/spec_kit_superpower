import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

/** dev/preview 把 /api 转到真实后端；端口必须与 uvicorn 一致（见 .env.example）。 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = (env.VITE_DEV_API_PROXY || 'http://127.0.0.1:8006').replace(/\/$/, '')

  const apiProxy = {
    '^/api': {
      target: apiProxyTarget,
      changeOrigin: true,
    },
  }

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 4173,
      strictPort: true,
      proxy: apiProxy,
    },
    preview: {
      host: true,
      port: 4175,
      strictPort: false,
      proxy: apiProxy,
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'antd-vendor': ['antd', '@ant-design/icons'],
          },
        },
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/setupTests.js',
      include: ['src/**/*.test.{js,jsx}'],
    },
  }
})
