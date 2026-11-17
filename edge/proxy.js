// semptify.org/bill* -> two origins by path class:
//   STATIC reads  -> GitHub raw site/bill/* snapshot (100% Cloudflare,
//                    zero origin hours — the Render free service can sleep)
//   LIVE paths    -> Render origin (ledger reads, boards, API, POSTs,
//                    steward, non-auto screen modes)
// Deploy snapshots: python snapshot.py --deploy && git push
const ORIGIN = 'https://bill-platform-5873.onrender.com';
const SNAP = 'https://raw.githubusercontent.com/1semptify-arch/bill-platform/main/site/';
const CT = { html: 'text/html;charset=utf-8', css: 'text/css',
             svg: 'image/svg+xml', js: 'application/javascript',
             png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg' };

// Exact static paths (snapshot files). Anything else -> origin.
const STATIC = new Set([
  '/bill/', '/bill/desk', '/bill/bill',
  '/bill/teach', '/bill/calculator', '/bill/help', '/bill/legal',
  '/bill/research', '/bill/history', '/bill/providers', '/bill/brief',
  '/bill/classroom', '/bill/press', '/bill/myths',
  '/bill/what-the-bill-changes', '/bill/present',
]);
const STATIC_PREFIX = [/^\/bill\/static\//, /^\/bill\/clause\//];
// Mirror-paths outside /bill -> remapped into the mount.
const REMAP = [/^\/your-voice(\/|$)/, /^\/what-the-bill-changes(\/|$)/];

function snapFile(path, search) {
  if (path === '/bill/') return 'bill/index.html';
  if (path === '/bill/present') {
    const s = new URLSearchParams(search).get('s');
    return s ? `bill/present-s${s}.html` : 'bill/present-s1.html';
  }
  return 'bill' + path.slice(5) + (path.endsWith('/') ? 'index.html'
      : path.startsWith('/bill/static/') || path.includes('.') ? '' : '.html');
}

export default {
  async fetch(request) {
    const u = new URL(request.url);
    let path = u.pathname.replace(/\/+$/, '') || '/';
    if (REMAP.some((re) => re.test(path))) path = '/bill' + path;
    else if (path === '/bill') path = '/bill/';

    const cookie = request.headers.get('cookie') || '';
    const steward = cookie.includes('bp_steward=');
    const mode = (cookie.match(/bp_mode=([a-z]+)/) || [])[1] || 'auto';
    const isStatic = request.method === 'GET' && !steward && mode === 'auto'
      && (STATIC.has(path) || STATIC_PREFIX.some((re) => re.test(path)));

    if (isStatic) {
      const file = snapFile(path, u.search);
      const r = await fetch(SNAP + file + '?v=1',
                            { cf: { cacheTtl: 300, cacheEverything: true } });
      if (r.ok) {
        const ext = file.split('.').pop();
        const h = new Headers(r.headers);
        h.set('content-type', CT[ext] || 'application/octet-stream');
        h.set('x-bp-source', 'snapshot');
        return new Response(r.body, { headers: h });
      }
      // fall through to origin if the snapshot file is missing
    }

    const h = new Headers(request.headers);
    h.set('x-forwarded-host', u.host);
    const init = { method: request.method, headers: h, redirect: 'manual' };
    if (request.method !== 'GET' && request.method !== 'HEAD') init.body = request.body;
    const res = await fetch(ORIGIN + path + u.search, init);
    const out = new Headers(res.headers);
    out.set('x-bp-source', 'live');
    return new Response(res.body, { status: res.status, headers: out });
  },
};
