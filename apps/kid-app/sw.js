// Offline shell for the app files only. API responses are never cached here: they hold a child's private data.
const V = 'chit-kids-v5';
const FILES = ['./', './index.html', './manifest.webmanifest', './icon-180.png', './icon-512.png', './icon.svg'];
self.addEventListener('install', e => e.waitUntil(caches.open(V).then(c => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== V).map(x => caches.delete(x)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;   // the network handles it
  // Network first so updates show straight away; the cache answers only when offline.
  e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(V).then(x => x.put(e.request, c)); return r; }).catch(() => caches.match(e.request)));
});
