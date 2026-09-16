const CANONICAL_HOST = 'www.xpeach.tv';
const APEX_HOST = 'xpeach.tv';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.hostname === APEX_HOST) {
      url.protocol = 'https:';
      url.hostname = CANONICAL_HOST;
      return Response.redirect(url.toString(), 301);
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
