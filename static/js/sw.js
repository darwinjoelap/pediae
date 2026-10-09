/* =====================================================================
   Service Worker — Ginea / Pediae  ·  Fase 2A (abrir y consultar sin datos)
   ---------------------------------------------------------------------
   - Estáticos (CSS/JS/íconos/CDN): cache-first; se guardan al usarse.
   - Páginas de consulta (agenda, pacientes, ficha, nueva consulta):
       network-first. Con red → versión fresca y se guarda copia.
       Sin red o red muy lenta → copia guardada (marcada como copia).
       Sin copia → página "Sin conexión" con lo que sí está disponible.
   - Los POST nunca pasan por aquí (los maneja offline.js con su cola).
   - Al cerrar sesión / llegar al login se borran las páginas guardadas.
   ===================================================================== */
const COLOR = '#38B8D8';   // color de la app (página "Sin conexión")
const VERSION = 'v6';
const CACHE_STATIC = 'static-' + VERSION;
const CACHE_PAGINAS = 'paginas-v1';           // no cambia con la versión: no perder copias al actualizar
const TIMEOUT_CON_COPIA = 5000;               // si hay copia, esperar la red como máximo esto
const TIMEOUT_SIN_COPIA = 30000;
const DIAS_COPIA = 7;

const STATIC_ASSETS = [
  '/static/css/app.css',
  '/static/js/app.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
];

// Páginas que se guardan para usar sin conexión (ruta después de /t/<slug>)
const PAGINAS_OFFLINE = [
  /^\/agenda\/(\d{4}-\d{2}-\d{2}\/)?$/,
  /^\/pacientes\/$/,
  /^\/pacientes\/\d+\/$/,
  /^\/consultas\/nueva\/\d+\/$/,
  /^\/consultas\/\d+\/$/,
];

function rutaTenant(pathname) {
  const m = pathname.match(/^\/t\/[^/]+(\/.*)$/);
  return m ? m[1] : pathname;
}
function esPaginaOffline(url) {
  const ruta = rutaTenant(url.pathname);
  return PAGINAS_OFFLINE.some(re => re.test(ruta));
}
function esLogin(url) { return /\/(accounts|panel)\/login\//.test(url.pathname); }

/* ───────────── instalación / activación ───────────── */

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_STATIC).then(cache =>
      Promise.all(STATIC_ASSETS.map(u => cache.add(u).catch(() => null))))   // un CDN caído no impide instalar
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_STATIC && k !== CACHE_PAGINAS).map(k => caches.delete(k))
    )).then(purgarViejas)
  );
  self.clients.claim();
});

/* ───────────── mensajes desde offline.js ───────────── */

self.addEventListener('message', event => {
  const d = event.data || {};
  if (d.tipo === 'borrar-paginas') {
    event.waitUntil(caches.delete(CACHE_PAGINAS).then(() => responder(event, { ok: true })));
  } else if (d.tipo === 'listar-paginas') {
    event.waitUntil(listarPaginas().then(lista => responder(event, { ok: true, paginas: lista })));
  }
});
function responder(event, datos) {
  if (event.ports && event.ports[0]) event.ports[0].postMessage(datos);
}

/* ───────────── fetch ───────────── */

self.addEventListener('fetch', event => {
  const req = event.request;
  if (!req.url.startsWith('http') || req.method !== 'GET') return;
  const url = new URL(req.url);

  // Endpoints de offline.js: siempre red
  if (url.pathname.startsWith('/offline/')) return;

  const mismoOrigen = url.origin === self.location.origin;
  const esEstatico = (mismoOrigen && url.pathname.startsWith('/static/')) ||
    (!mismoOrigen && ['style', 'script', 'font'].includes(req.destination)) ||
    url.hostname.includes('cdn.jsdelivr.net');

  if (esEstatico) {
    event.respondWith(cacheFirst(req));
    return;
  }

  if (!mismoOrigen) return;

  const esNavegacion = req.mode === 'navigate';
  const esPrecarga = req.headers.get('X-Offline-Prefetch') === '1';

  if (esNavegacion && esLogin(url)) {
    // Llegar al login = sesión cerrada o vencida → borrar copias de historias
    event.waitUntil(caches.delete(CACHE_PAGINAS));
    return;
  }

  if ((esNavegacion || esPrecarga) && esPaginaOffline(url)) {
    event.respondWith(networkFirstPagina(event, req, url, esPrecarga));
    return;
  }

  if (esNavegacion) {
    // Otras páginas: red; si no hay red, página "Sin conexión"
    event.respondWith(fetch(req).catch(() => paginaSinConexion(url)));
  }
});

function cacheFirst(req) {
  return caches.match(req).then(cached => cached || fetch(req).then(resp => {
    if (resp && (resp.ok || resp.type === 'opaque')) {
      const copia = resp.clone();
      caches.open(CACHE_STATIC).then(c => c.put(req, copia));
    }
    return resp;
  }));
}

function guardable(resp) {
  if (!resp || !resp.ok || resp.redirected) return false;
  const ct = resp.headers.get('Content-Type') || '';
  return ct.indexOf('text/html') !== -1;
}

function guardarPagina(url, resp) {
  // Se guarda con fecha para poder mostrar "copia de las HH:MM" y purgar a los 7 días
  return resp.clone().text().then(html => {
    const headers = new Headers(resp.headers);
    headers.set('X-Offline-Guardado', String(Date.now()));
    const titulo = (html.match(/<title>([\s\S]*?)<\/title>/i) || [])[1] || '';
    headers.set('X-Offline-Titulo', encodeURIComponent(titulo.replace(/\s+/g, ' ').trim()));
    return caches.open(CACHE_PAGINAS).then(c =>
      c.put(url.href, new Response(html, { status: 200, headers })));
  });
}

function buscarCopia(url) {
  return caches.open(CACHE_PAGINAS).then(c =>
    c.match(url.href, { ignoreVary: true }).then(r => {
      if (r) return r;
      // "Nueva consulta" con otro ?cita= → sirve la misma plantilla (el POST va a la URL pedida)
      if (/\/consultas\/nueva\/\d+\/$/.test(url.pathname)) {
        return c.match(url.origin + url.pathname, { ignoreVary: true, ignoreSearch: true });
      }
      return null;
    }));
}

function marcarCopia(resp, motivo) {
  return resp.text().then(html => {
    const ts = resp.headers.get('X-Offline-Guardado') || '';
    const marca = '<script>window.__OFFLINE_COPIA={guardado:' + (Number(ts) || 0) +
      ',motivo:"' + motivo + '"};</script>';
    html = html.indexOf('</head>') !== -1 ? html.replace('</head>', marca + '</head>') : marca + html;
    const headers = new Headers(resp.headers);
    headers.set('Content-Type', 'text/html; charset=utf-8');
    return new Response(html, { status: 200, headers });
  });
}

function extender(event, promesa) {
  try { event.waitUntil(promesa); } catch (e) { /* el evento ya terminó: la promesa sigue igual */ }
  return promesa;
}

function networkFirstPagina(event, req, url, esPrecarga) {
  const red = fetch(req).then(resp => {
    if (guardable(resp)) {
      const p = extender(event, guardarPagina(url, resp));
      if (esPrecarga) return p.then(() => resp);   // la precarga espera a que quede guardada
    } else if (resp && resp.redirected && esLogin(new URL(resp.url))) {
      extender(event, caches.delete(CACHE_PAGINAS));
    }
    return resp;
  });

  if (esPrecarga) return red;   // la precarga solo llena la caché

  return buscarCopia(url).then(copia => {
    const limite = copia ? TIMEOUT_CON_COPIA : TIMEOUT_SIN_COPIA;
    const espera = new Promise(resolve => setTimeout(() => resolve('timeout'), limite));
    return Promise.race([red.catch(() => 'sin-red'), espera]).then(r => {
      if (r instanceof Response) return r;
      if (copia) return marcarCopia(copia, r === 'timeout' ? 'lento' : 'sin-red');
      if (r === 'timeout') return red.catch(() => paginaSinConexion(url));
      return paginaSinConexion(url);
    });
  });
}

/* ───────────── utilidades ───────────── */

function listarPaginas() {
  return caches.open(CACHE_PAGINAS).then(c => c.keys().then(keys => Promise.all(keys.map(k =>
    c.match(k).then(r => ({
      url: k.url,
      titulo: decodeURIComponent(r.headers.get('X-Offline-Titulo') || ''),
      guardado: Number(r.headers.get('X-Offline-Guardado')) || 0,
    }))))));
}

function purgarViejas() {
  const limite = Date.now() - DIAS_COPIA * 86400000;
  return caches.open(CACHE_PAGINAS).then(c => c.keys().then(keys => Promise.all(keys.map(k =>
    c.match(k).then(r => {
      const t = Number(r && r.headers.get('X-Offline-Guardado')) || 0;
      if (t < limite) return c.delete(k);
    })))));
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
}

function paginaSinConexion(url) {
  const prefijo = (url.pathname.match(/^\/t\/[^/]+/) || [''])[0];
  return listarPaginas().then(lista => {
    lista = lista.filter(p => new URL(p.url).pathname.startsWith(prefijo + '/'))
      .sort((a, b) => b.guardado - a.guardado);
    const items = lista.map(p => {
      const u = new URL(p.url);
      const t = (p.titulo || u.pathname).split(' - ')[0];
      return '<a class="item" href="' + esc(u.pathname + u.search) + '">' + esc(t) +
        '<small>' + esc(rutaTenant(u.pathname)) + '</small></a>';
    }).join('');
    const html = '<!doctype html><html lang="es"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Sin conexión</title>' +
      '<style>body{font-family:system-ui,sans-serif;margin:0;background:#f5f6f8;color:#222}' +
      '.box{max-width:520px;margin:0 auto;padding:24px 16px}h1{font-size:1.25rem;margin:.2rem 0 .5rem}' +
      '.chip{display:inline-block;background:#dc3545;color:#fff;border-radius:999px;padding:.25rem .7rem;font-size:.8rem;font-weight:600}' +
      'p{color:#555;line-height:1.45}.item{display:block;background:#fff;border-radius:10px;padding:.8rem 1rem;margin:.5rem 0;' +
      'color:#1e1b2e;text-decoration:none;box-shadow:0 1px 3px rgba(0,0,0,.08);font-weight:600}' +
      '.item small{display:block;color:#888;font-weight:400;margin-top:.15rem}' +
      'button{margin-top:1rem;width:100%;padding:.8rem;border:0;border-radius:10px;background:' + COLOR + ';color:#fff;font-size:1rem;font-weight:600}</style>' +
      '</head><body><div class="box"><span class="chip">Sin conexión</span>' +
      '<h1>Esta página no está guardada en el dispositivo</h1>' +
      '<p>Puedes seguir trabajando con las páginas que sí están guardadas. Lo que registres se enviará solo cuando vuelva la señal.</p>' +
      (items || '<p><em>Todavía no hay páginas guardadas. Abre la agenda con internet al menos una vez.</em></p>') +
      '<button onclick="location.reload()">Reintentar</button></div></body></html>';
    return new Response(html, { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  });
}
