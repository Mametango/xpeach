"""Export the reviewed XPeach catalog as Cloudflare static assets.

Run this inside the existing FastAPI container, where the PostgreSQL connection
and application models are already available. The generated site never calls
the X API or the AI API while being viewed.
"""

from __future__ import annotations

import html
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, "/app")

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import engine
from app.models import Video


BASE_URL = "https://xpeach.tv"
MEDIA_BASE_URL = "https://admin.xpeach.tv"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/xpeach-public").resolve()
if OUTPUT == Path("/") or not str(OUTPUT).startswith("/tmp/"):
    raise SystemExit("The export destination must be a directory below /tmp.")


def esc(value: object | None) -> str:
    return html.escape(str(value or ""), quote=True)


def media(video: Video):
    return next((item for item in video.media_items if item.media_reference), None)


def thumbnail(video: Video) -> str | None:
    first = video.media_items[0] if video.media_items else None
    return (first.thumbnail_url if first else None) or video.preview_image_url


def creator_name(video: Video) -> str:
    return (video.source_account.display_name if video.source_account else None) or video.x_username


def published_time(video: Video):
    return video.published_at or video.x_created_at or video.registered_at


def x_posted_time(video: Video):
    return video.x_created_at or video.registered_at


def metric_score(video: Video) -> int:
    if video.view_count is None and video.like_count is None and video.repost_count is None:
        return -1
    return (video.view_count or 0) + (video.like_count or 0) * 30 + (video.repost_count or 0) * 50


def duration_label(video: Video) -> str:
    first = video.media_items[0] if video.media_items else None
    duration_ms = (first.duration_ms if first else None) or video.duration_ms
    if not duration_ms:
        return ""
    seconds = int(duration_ms / 1000)
    return f'<span class="duration">{seconds // 60}:{seconds % 60:02d}</span>'


def card(video: Video) -> str:
    playable = media(video)
    poster = thumbnail(video)
    poster_attr = f' poster="{esc(poster)}"' if poster else ""
    image = (
        f'<img src="{esc(poster)}" alt="@{esc(video.x_username)}の動画サムネイル" loading="lazy" decoding="async">'
        if poster
        else '<div class="guide-placeholder"><span>▶</span><strong>X動画クリップ</strong></div>'
    )
    if playable:
        media_url = f"{MEDIA_BASE_URL}/media/video/{playable.id}"
        visual = (
            f'<div class="media-frame inline-player"><video class="inline-card-video" controls playsinline '
            f'preload="none" aria-label="@{esc(video.x_username)}の動画を再生"'
            f'{poster_attr}>'
            f'<source src="{esc(media_url)}" type="video/mp4">動画を再生できません。</video></div>'
        )
    else:
        visual = (
            f'<a class="media-frame" href="{esc(video.x_post_url)}" target="_blank" rel="noopener noreferrer">'
            f'{image}<span class="play-mark">▶</span></a>'
        )
    username = quote(video.x_username, safe="")
    return (
        f'<article class="video-card">{visual}<a class="creator-only" href="/creator/{username}/">'
        f'<strong>{esc(creator_name(video))}</strong><span>@{esc(video.x_username)}</span></a></article>'
    )


def shell(*, title: str, description: str, canonical_path: str, content: str, og_image: str | None = None) -> str:
    canonical = f"{BASE_URL}{canonical_path}"
    og = f'<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{esc(canonical)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="XPeach">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">{og}
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src https://admin.xpeach.tv; img-src 'self' https://pbs.twimg.com data:; media-src https://admin.xpeach.tv; style-src 'self' 'unsafe-inline'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'">
  <title>{esc(title)} | XPeach</title>
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/app.css?v=20260916-4">
</head>
<body>
  <div class="age-gate" data-age-gate role="dialog" aria-modal="true" aria-labelledby="age-title">
    <div class="age-card"><img src="/assets/logo.svg" alt="" width="54" height="54"><h1 id="age-title">18歳以上ですか？</h1><p>このサイトには18歳以上を対象としたコンテンツが含まれています。</p><button type="button" data-age-accept>18歳以上です</button><a href="https://www.google.com/">18歳未満です</a></div>
  </div>
  <header class="site-header"><div class="header-inner"><a class="brand" href="/"><img src="/assets/logo.svg" alt="" width="34" height="34"><b>XPeach</b></a><nav><a href="/new/">新着</a><a href="/popular/">人気</a><a href="/trending/">急上昇</a></nav></div></header>
  <main>{content}</main>
  <footer><span>XPeach — 元投稿を尊重するクリップガイド</span></footer>
  <script src="/assets/app.js?v=20260916-4" defer></script>
</body>
</html>'''


def listing(title: str, path: str, videos: list[Video]) -> str:
    cards = "".join(card(video) for video in videos) or '<div class="empty-state">公開動画はまだありません</div>'
    heading = "" if path == "/" else f'<div class="page-heading"><h1>{esc(title)}</h1><span>{len(videos)}本</span></div>'
    return shell(
        title=title,
        description="公開審査済みのX動画を、元投稿を尊重して紹介する動画ガイドです。",
        canonical_path=path,
        content=f'<section class="catalog">{heading}<div class="video-grid">{cards}</div></section>',
        og_image=thumbnail(videos[0]) if videos else None,
    )


def detail(video: Video) -> str:
    playable = media(video)
    poster = thumbnail(video)
    if playable:
        media_url = f"{MEDIA_BASE_URL}/media/video/{playable.id}"
        poster_attr = f' poster="{esc(poster)}"' if poster else ""
        player = f'<video class="public-video-player" controls playsinline preload="metadata"{poster_attr}><source src="{esc(media_url)}" type="video/mp4">動画を再生できません。</video>'
    elif poster:
        player = f'<img class="detail-poster" src="{esc(poster)}" alt="@{esc(video.x_username)}の動画"><a class="x-button" href="{esc(video.x_post_url)}" target="_blank" rel="noopener noreferrer">Xで見る ↗</a>'
    else:
        player = f'<div class="no-player">この動画はXで視聴できます。<a class="x-button" href="{esc(video.x_post_url)}" target="_blank" rel="noopener noreferrer">Xで見る ↗</a></div>'
    creator_url = f'https://x.com/{quote(video.x_username, safe="")}'
    content = (
        f'<section class="video-detail"><div class="player-panel">{player}</div>'
        f'<a class="creator-account-card" href="{creator_url}" target="_blank" rel="noopener noreferrer">'
        f'<strong>{esc(creator_name(video))}</strong><span>@{esc(video.x_username)} ↗</span></a>'
        f'<a class="source-link" href="{esc(video.x_post_url)}" target="_blank" rel="noopener noreferrer">元のX投稿を開く ↗</a></section>'
    )
    return shell(
        title=f"@{video.x_username}の動画",
        description=f"{creator_name(video)}（@{video.x_username}）の公開動画です。",
        canonical_path=f"/video/{video.id}/",
        content=content,
        og_image=poster,
    )


def write(path: str, content: str):
    target = OUTPUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def main():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    with Session(engine) as db:
        videos = list(db.scalars(
            select(Video).options(
                selectinload(Video.media_items), selectinload(Video.source_account)
            ).where(
                Video.publication_status == "published",
                Video.is_public.is_(True),
                Video.deleted_at_x.is_(None),
            )
        ).unique())

        newest = sorted(videos, key=lambda item: (x_posted_time(item), item.id), reverse=True)
        popular = sorted(videos, key=lambda item: (metric_score(item), published_time(item), item.id), reverse=True)
        since = datetime.now(timezone.utc) - timedelta(hours=48)
        trending = [item for item in popular if published_time(item).replace(tzinfo=published_time(item).tzinfo or timezone.utc) >= since]

        write("index.html", listing("XPeach - Discover Trending Videos", "/", newest[:24]))
        write("new/index.html", listing("新着動画", "/new/", newest))
        write("popular/index.html", listing("人気動画", "/popular/", popular))
        write("trending/index.html", listing("急上昇動画", "/trending/", trending))

        creators: dict[str, list[Video]] = {}
        for video in newest:
            creators.setdefault(video.x_username, []).append(video)
            write(f"video/{video.id}/index.html", detail(video))
        for username, creator_videos in creators.items():
            write(
                f"creator/{quote(username, safe='')}/index.html",
                listing(f"@{username}の動画", f"/creator/{quote(username, safe='')}/", creator_videos),
            )

        write("suggest-account/index.html", shell(
            title="アカウント申請",
            description="XPeachへの掲載アカウント申請についてご案内します。",
            canonical_path="/suggest-account/",
            content='<section class="message-page"><h1>アカウント申請</h1><p>申請受付は現在準備中です。</p><a href="/">トップへ戻る</a></section>',
        ))
        write("404.html", shell(
            title="ページが見つかりません",
            description="指定されたページは見つかりませんでした。",
            canonical_path="/404",
            content='<section class="message-page"><h1>404</h1><p>ページが見つかりません。</p><a href="/">トップへ戻る</a></section>',
        ))

        urls = ["/", "/new/", "/popular/", "/trending/"]
        urls += [f"/video/{video.id}/" for video in newest]
        urls += [f"/creator/{quote(username, safe='')}/" for username in creators]
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
            f"  <url><loc>{BASE_URL}{path}</loc></url>\n" for path in urls
        ) + "</urlset>\n"
        write("sitemap.xml", sitemap)
        write("robots.txt", f"User-agent: *\nDisallow: /admin\nDisallow: /report-received\nSitemap: {BASE_URL}/sitemap.xml\n")

    assets = OUTPUT / "assets"
    assets.mkdir()
    shutil.copy("/app/app/static/brand/logo.svg", assets / "logo.svg")
    shutil.copy("/app/app/static/brand/favicon.svg", assets / "favicon.svg")
    shutil.copy(PROJECT_ROOT / "public/assets/app.css", assets / "app.css")
    shutil.copy(PROJECT_ROOT / "public/assets/app.js", assets / "app.js")
    print(f"Exported {len(videos)} published videos to {OUTPUT}")


if __name__ == "__main__":
    main()
