import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../src/web',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/predict': 'http://127.0.0.1:8000',
      '/evaluate': 'http://127.0.0.1:8000',
      '/metadata': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
});
