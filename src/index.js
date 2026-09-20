const CANONICAL_HOST = 'www.xpeach.tv';
const APEX_HOST = 'xpeach.tv';
// The FastAPI deployment is the source of truth for both the admin catalog and
// the public catalog.  Keeping this origin in one place prevents the Worker
// from serving a stale HTML snapshot after new videos are published.
const APP_ORIGIN = 'https://admin.xpeach.tv';

async function proxyApp(request, url) {
  if (!['GET', 'HEAD'].includes(request.method)) {
    // Public report/event and age-gate forms are POST requests and must reach
    // FastAPI as well.  Other methods are passed through unchanged.
  }

  const upstreamUrl = new URL(`${url.pathname}${url.search}`, APP_ORIGIN);
  const requestHeaders = new Headers(request.headers);
  // Do not let the internal hostname affect generated absolute URLs or
  // redirect decisions.  Cookies remain host-only on the public hostname,
  // which is intentional and avoids sharing them with the admin hostname.
  requestHeaders.set('X-Forwarded-Host', url.host);
  requestHeaders.set('X-Forwarded-Proto', 'https');
  requestHeaders.delete('Host');
  const init = {method: request.method, headers: requestHeaders, redirect: 'manual'};
  if (!['GET', 'HEAD'].includes(request.method)) init.body = request.body;
  const upstreamResponse = await fetch(new Request(upstreamUrl, init));
  const responseHeaders = new Headers(upstreamResponse.headers);
  // FastAPI may emit an absolute redirect using the internal origin when it
  // normalizes `/new/`, `/video/123/`, or sends an age-gate redirect. Keep the
  // browser on the public hostname while preserving path and query string.
  const location = responseHeaders.get('location');
  if (location) {
    const internalPrefix = `${APP_ORIGIN}`;
    if (location === internalPrefix || location.startsWith(`${internalPrefix}/`)) {
      responseHeaders.set('location', `https://${url.host}${location.slice(internalPrefix.length)}`);
    }
  }
  // HTML and cookie-dependent responses must never be cached as a snapshot.
  if ((responseHeaders.get('content-type') || '').includes('text/html') || responseHeaders.has('set-cookie')) {
    responseHeaders.set('Cache-Control', 'private, no-store');
  }
  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}

function isAssetRequest(pathname) {
  return pathname.startsWith('/assets/') || pathname === '/favicon.ico';
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.hostname === APEX_HOST) {
      url.protocol = 'https:';
      url.hostname = CANONICAL_HOST;
      return Response.redirect(url.toString(), 301);
    }

    // Only immutable brand assets remain on the static Worker bucket. All
    // pages, media relay requests, forms, robots and sitemap are read from the
    // FastAPI/PostgreSQL deployment so admin and public counts cannot diverge.
    if (isAssetRequest(url.pathname)) return env.ASSETS.fetch(request);

    const response = await proxyApp(request, url);
    const headers = new Headers(response.headers);
    if (url.pathname === '/admin' || url.pathname.startsWith('/admin/') ||
        url.pathname === '/api/admin' || url.pathname.startsWith('/api/admin/')) {
      headers.set('X-Robots-Tag', 'noindex, nofollow, noarchive');
    }
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
