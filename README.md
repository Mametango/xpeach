# XPeach Cloudflare static catalog

This repository is the public, static Cloudflare Workers deployment for XPeach.
`wrangler.jsonc` intentionally keeps `assets.directory` set to `./public`.

The published catalog is a snapshot exported from the reviewed PostgreSQL data.
Viewing the site does not call the X API or AI API. Administration, collection,
account submissions, and reports remain in the private FastAPI deployment and
must not be copied into `public`.

## Refreshing the catalog

Run `tools/export_snapshot.py` inside the existing FastAPI container, copy the
generated `/tmp/xpeach-public` directory to `public`, then review and push it.
Only videos with `publication_status=published`, `is_public=true`, and no X
deletion timestamp are exported.

Never commit `.env`, API tokens, authorization headers, database credentials,
or AI keys. Use Cloudflare Secrets if Worker-side secrets are introduced later.
