const CANONICAL_HOST = 'www.xpeach.tv';
const APEX_HOST = 'xpeach.tv';
const MEDIA_ORIGIN = 'https://admin.xpeach.tv';

function hasAgeVerification(request) {
  return /(?:^|;\s*)age_verified=true(?:;|$)/.test(request.headers.get('Cookie') || '');
}

async function proxyMedia(request, url) {
  if (!['GET', 'HEAD'].includes(request.method)) {
    return new Response('Method Not Allowed', {status: 405, headers: {Allow: 'GET, HEAD'}});
  }
  if (!hasAgeVerification(request)) {
    return new Response('Age verification required', {
      status: 403,
      headers: {'X-Robots-Tag': 'noindex, nofollow, noarchive'},
    });
  }

  const upstreamUrl = new URL(`${url.pathname}${url.search}`, MEDIA_ORIGIN);
  const upstreamResponse = await fetch(new Request(upstreamUrl, request));
  const headers = new Headers(upstreamResponse.headers);
  headers.set('Cache-Control', 'private, max-age=3600');
  headers.set('X-Robots-Tag', 'noindex, nofollow, noarchive');
  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers,
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.hostname === APEX_HOST) {
      url.protocol = 'https:';
      url.hostname = CANONICAL_HOST;
      return Response.redirect(url.toString(), 301);
    }

    if (/^\/media\/video\/\d+$/.test(url.pathname)) {
      return proxyMedia(request, url);
    }

    const response = await env.ASSETS.fetch(request);
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
