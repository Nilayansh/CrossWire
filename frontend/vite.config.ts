import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/incidents': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/tickets': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/intake': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/traffic': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/scenarios': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
