const CACHE = 'simba-v1';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const { request } = e;
  const url = new URL(request.url);

  // Network-only for API calls
  if (url.pathname.startsWith('/api/')) return;

  // Cache-first for fingerprinted static assets
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((res) => {
            const clone = res.clone();
            caches.open(CACHE).then((c) => c.put(request, clone));
            return res;
          })
      )
    );
    return;
  }

  // Network-first for navigation (offline fallback to cache)
  if (request.mode === 'navigate') {
    e.respondWith(
      fetch(request).catch(() => caches.match(request))
    );
    return;
  }
});
