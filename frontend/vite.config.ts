import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { reactRouter } from '@react-router/dev/vite'
import path from 'path'

export default defineConfig(({ mode, command }) => {
  // Exclude React Router plugin for SSR builds and tests
  // React Router plugin is only needed for client-side file-based routing
  const isSSRBuild = command === 'build' && process.env.VITE_SSR === 'true'
  const isTest = mode === 'test'
  
  return {
    plugins: (isSSRBuild || isTest) ? [react()] : [reactRouter(), react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
  ssr: {
    noExternal: ['react', 'react-dom', 'react-router', 'react-router-dom'],
    resolve: {
      conditions: ['node'],
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
  }
})
