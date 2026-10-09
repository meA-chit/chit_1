import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig, type Plugin } from 'vite';

const root = fileURLToPath(new URL('../..', import.meta.url));
const lan = process.env.CHIT_LAN === '1'; // opt-in: serve the web client to the local network (the hub itself stays on loopback)
const hub = `http://127.0.0.1:${process.env.CHIT_PORT ?? 8765}`; // ADR-0007: loopback only

// The sign-in page (public/auth) is plain HTML; give /auth/ the folder-index behaviour a static host would have, so Vite's
// single-page fallback does not answer with the app instead (ADR-0014).
const authPage: Plugin = {
  name: 'chit-auth-page',
  configureServer(server) {
    server.middlewares.use((request, _response, next) => {
      if (request.url === '/auth' || request.url === '/auth/' || request.url?.startsWith('/auth/?')) request.url = '/auth/index.html';
      next();
    });
  },
};

export default defineConfig({
  root: fileURLToPath(new URL('.', import.meta.url)),
  plugins: [react(), authPage],
  resolve: {
    alias: [
      { find: '@chit/core/styles', replacement: `${root}core/web/src/theme/index.css` },
      { find: '@chit/core', replacement: `${root}core/web/src/index.ts` },
    ],
  },
  server: {
    port: 5173,
    host: lan ? true : 'localhost',
    allowedHosts: lan ? true : undefined, // lets a hostname such as my-mac.local through, not just an IP
    fs: { allow: [root] },
    proxy: { '/api': hub, '/legacy': hub },
  },
  build: { outDir: 'dist', emptyOutDir: true, target: 'es2022' },
  test: {
    root,
    include: ['core/web/**/*.test.ts', 'modules/*/submodules/*/web/**/*.test.ts', 'modules/*/shared/**/*.test.ts'],
  },
});
