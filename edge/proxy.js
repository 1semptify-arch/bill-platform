// platform.semptify.org -> bill-platform-5873.onrender.com
// Thin pass-through so the platform gets a branded URL entirely via
// API (no Render-dashboard custom-domain step, no DNS-edit needed).
// Replace with a real CNAME + Render custom domain when convenient.
const ORIGIN = 'https://bill-platform-5873.onrender.com';
export default {
  async fetch(request) {
    const u = new URL(request.url);
    const h = new Headers(request.headers);
    h.set('x-forwarded-host', u.host);
    const init = { method: request.method, headers: h, redirect: 'manual' };
    if (request.method !== 'GET' && request.method !== 'HEAD') init.body = request.body;
    return fetch(ORIGIN + u.pathname + u.search, init);
  },
};
