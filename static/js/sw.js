const CACHE_NAME = 'ginea-v4';
const STATIC_ASSETS = [
  '/static/css/app.css',
  '/static/js/app.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const req = event.request;

  // Solo interceptar GET; dejar pasar POST, PUT, DELETE, etc.
  if (req.method !== 'GET') return;

  // Ignorar esquemas que no sean http/https (evita error con chrome-extension://)
  if (!req.url.startsWith('http')) return;

  const url = new URL(req.url);

  // Cache-first solo para assets estáticos propios y CDN
  if (url.pathname.startsWith('/static/') || url.hostname.includes('cdn.jsdelivr.net')) {
    event.respondWith(
      caches.match(req).then(cached => cached || fetch(req))
    );
    return;
  }

  // Todo lo demás (HTML dinámico, APIs) → solo red, sin cachear
  // Esto es crítico: cachear HTML causa tokens CSRF viejos
});
