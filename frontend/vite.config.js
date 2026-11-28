import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    // Зібрані файли роздає Django: /static/frontend/app.js
    rolldownOptions: {
      output: {
        entryFileNames: 'app.js',
        chunkFileNames: '[name].js',
        assetFileNames: 'app[extname]',
      },
    },
  },
  server: {
    host: '127.0.0.1',
    // /api і /accounts передаються Django; Host лишається :5173,
    // тож перевірка Origin у CsrfViewMiddleware проходить
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false },
      '/accounts': { target: 'http://127.0.0.1:8000', changeOrigin: false },
    },
  },
})
