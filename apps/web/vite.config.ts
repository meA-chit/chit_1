import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const root = fileURLToPath(new URL('../..', import.meta.url));
const hub = `http://127.0.0.1:${process.env.CHIT_PORT ?? 8765}`; // ADR-0007: loopback only

export default defineConfig({
  root: fileURLToPath(new URL('.', import.meta.url)),
  plugins: [react()],
  resolve: {
    alias: [
      { find: '@chit/core/styles', replacement: `${root}core/web/src/theme/index.css` },
      { find: '@chit/core', replacement: `${root}core/web/src/index.ts` },
    ],
  },
  server: {
    port: 5173,
    fs: { allow: [root] },
    proxy: { '/api': hub, '/legacy': hub },
  },
  build: { outDir: 'dist', emptyOutDir: true, target: 'es2022' },
  test: {
    root,
    include: ['core/web/**/*.test.ts', 'modules/*/submodules/*/web/**/*.test.ts', 'modules/*/shared/**/*.test.ts'],
  },
});
