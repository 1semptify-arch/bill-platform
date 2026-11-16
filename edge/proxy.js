// semptify.org/bill* (+ /your-voice, /what-the-bill-changes) -> Render.
// The platform app mounts at /bill (BILL_MOUNT=/bill): /bill* paths pass
// through unchanged; the mirror's two non-/bill paths are re-mapped so
// they land inside the mounted app. One UI, one public address.
const ORIGIN = 'https://bill-platform-5873.onrender.com';
const REMAP = [/^\/your-voice(\/|$)/, /^\/what-the-bill-changes(\/|$)/];
export default {
  async fetch(request) {
    const u = new URL(request.url);
    let path = u.pathname;
    if (REMAP.some((re) => re.test(path))) path = '/bill' + path;
    const h = new Headers(request.headers);
    h.set('x-forwarded-host', u.host);
    const init = { method: request.method, headers: h, redirect: 'manual' };
    if (request.method !== 'GET' && request.method !== 'HEAD') init.body = request.body;
    return fetch(ORIGIN + path + u.search, init);
  },
  // Render free tier sleeps after ~15 min idle — ping keeps it warm so
  // the public URL never cold-starts (~720 of 750 free hours/month).
  async scheduled(event, env, ctx) {
    ctx.waitUntil(fetch(ORIGIN + '/bill/'));
  },
};
