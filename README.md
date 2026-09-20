# XPeach Cloudflare public edge

This repository is the public Cloudflare Workers edge for XPeach.
`wrangler.jsonc` intentionally keeps `assets.directory` set to `./public` for
immutable brand assets and a safe fallback, while public pages are proxied to
the FastAPI deployment at `admin.xpeach.tv`. FastAPI and the admin UI therefore
read the same PostgreSQL catalog, so a newly published video is visible on the
public site without exporting or committing a new HTML snapshot.

The Worker never calls the X API or AI API. It only forwards public HTTP
requests to the existing FastAPI origin; API collection remains in the
separate worker/scheduler services.

## Deployment

Push `main` to deploy the Worker. Keep the `admin.xpeach.tv` Named Tunnel and
the FastAPI Docker service running: the Worker uses that origin for `/`,
`/new`, `/popular`, `/trending`, video pages, reports, robots, sitemap and the
media relay. `/assets/*` continues to be served from the Worker asset bucket.

Only videos with `publication_status=published`, `is_public=true`, and no X
deletion timestamp are returned by the FastAPI public repository.

Published HTML uses `https://admin.xpeach.tv/media/video/{media_id}` as the
video source. That endpoint relays only saved official X MP4 URLs and rechecks
the current publication state, so stopped/deleted videos disappear without a
new X API call. The shared `age_verified=true` cookie is the only value passed
between `xpeach.tv` and the media relay subdomain. Keep the `xpeach-admin`
Named Tunnel and its Docker service running for playback.

Never commit `.env`, API tokens, authorization headers, database credentials,
or AI keys. Use Cloudflare Secrets if Worker-side secrets are introduced later.
