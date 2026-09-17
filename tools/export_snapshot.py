"""Export the reviewed XPeach catalog as Cloudflare static assets.

Run this inside the existing FastAPI container, where the PostgreSQL connection
and application models are already available. The generated site never calls
the X API or the AI API while being viewed.
"""

from __future__ import annotations

import html
import base64
import hashlib
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, "/app")

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import engine
from app.models import Report, Video


BASE_URL = "https://www.xpeach.tv"
MEDIA_BASE_URL = BASE_URL
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


def media_dimensions(video: Video) -> str:
    first = video.media_items[0] if video.media_items else None
    if first and first.width and first.height:
        return f' width="{first.width}" height="{first.height}"'
    return ""


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


def video_title(video: Video) -> str:
    return (video.display_title or "").strip() or f"{creator_name(video)}の動画"


def video_description(video: Video) -> str:
    category_names = [item.name for item in video.categories if item.is_active]
    category_text = f" カテゴリ: {'、'.join(category_names)}。" if category_names else ""
    curator_text = f" {video.curator_note.strip()}" if video.curator_note and video.curator_note.strip() else ""
    return f"{creator_name(video)}（@{video.x_username}）の公開審査済み動画です。{category_text}{curator_text}"[:240]


def card(video: Video) -> str:
    playable = media(video)
    poster = thumbnail(video)
    poster_attr = f' poster="{esc(poster)}"' if poster else ""
    dimensions = media_dimensions(video)
    image = (
        f'<img src="{esc(poster)}" alt="@{esc(video.x_username)}の動画サムネイル" loading="lazy" decoding="async"{dimensions}>'
        if poster
        else '<div class="guide-placeholder"><span>▶</span><strong>X動画クリップ</strong></div>'
    )
    if playable:
        media_url = f"{MEDIA_BASE_URL}/media/video/{playable.id}"
        visual = (
            f'<div class="media-frame inline-player" data-inline-player '
            f'data-video-src="{esc(media_url)}" data-video-label="@{esc(video.x_username)}の動画を再生"'
            f' data-video-poster="{esc(poster or "")}">'
            f'<button class="inline-play-button" type="button" aria-label="@{esc(video.x_username)}の動画を再生">'
            f'{image}<span class="play-mark" aria-hidden="true">▶</span></button></div>'
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


def shell(*, title: str, description: str, canonical_path: str, content: str,
          og_image: str | None = None, og_type: str = "website", structured_data: dict | None = None,
          robots: str = "index,follow,max-image-preview:large", exact_title: bool = False) -> str:
    canonical = f"{BASE_URL}{canonical_path}"
    document_title = title if exact_title else f"{title} | XPeach"
    og = f'<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    twitter_image = f'<meta name="twitter:image" content="{esc(og_image)}">' if og_image else ""
    structured_json = json.dumps(structured_data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") if structured_data else ""
    structured_script = f'<script type="application/ld+json">{structured_json}</script>' if structured_json else ""
    script_hash = ""
    if structured_json:
        digest = base64.b64encode(hashlib.sha256(structured_json.encode()).digest()).decode()
        script_hash = f" 'sha256-{digest}'"
    nav_items = (("New", "/new/"), ("Popular", "/popular/"), ("Trending", "/trending/"))
    active_nav = "/new/" if canonical_path == "/" else canonical_path
    nav_links = "".join(
        f'<a class="menu-pill{" is-active" if active_nav.startswith(path) else ""}" href="{path}"'
        f'{" aria-current=\"page\"" if active_nav.startswith(path) else ""}>{label}</a>'
        for label, path in nav_items
    )
    return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="{esc(robots)}">
  <link rel="canonical" href="{esc(canonical)}">
  <meta property="og:type" content="{esc(og_type)}">
  <meta property="og:site_name" content="XPeach">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">{og}
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">{twitter_image}
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src https://admin.xpeach.tv; img-src 'self' https://pbs.twimg.com data:; media-src 'self' https://admin.xpeach.tv; style-src 'self' 'unsafe-inline'; script-src 'self'{script_hash}; base-uri 'self'; form-action 'self'; frame-ancestors 'none'">
{structured_script}
  <title>{esc(document_title)}</title>
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/app.css?v=20260916-8">
</head>
<body>
  <div class="age-gate" data-age-gate role="dialog" aria-modal="true" aria-labelledby="age-title">
    <div class="age-card"><img src="/assets/logo.svg" alt="" width="54" height="54"><p class="age-title" id="age-title" role="heading" aria-level="2">18歳以上ですか？</p><p>このサイトには18歳以上を対象としたコンテンツが含まれています。</p><button type="button" data-age-accept>18歳以上です</button><a href="https://www.google.com/">18歳未満です</a></div>
  </div>
  <header class="site-header"><div class="header-inner"><a class="brand" href="/"><img src="/assets/logo.svg" alt="" width="34" height="34"><b>XPeach</b></a><nav aria-label="Video menu">{nav_links}</nav></div></header>
  <main>{content}</main>
  <footer><span>XPeach — 元投稿を尊重するクリップガイド</span></footer>
  <script src="/assets/app.js?v=20260916-7" defer></script>
</body>
</html>'''


def listing(title: str, path: str, videos: list[Video], *, seo_title: str | None = None,
            description: str = "公開審査済みのX動画を、元投稿を尊重して紹介する動画ガイドです。") -> str:
    cards = "".join(card(video) for video in videos) or '<div class="empty-state">公開動画はまだありません</div>'
    display_heading = "新着動画" if path == "/" else title
    heading = f'<div class="page-heading"><h1>{esc(display_heading)}</h1><span>{len(videos)}本</span></div>'
    return shell(
        title=seo_title or title,
        description=description,
        canonical_path=path,
        content=f'<section class="catalog">{heading}<div class="video-grid">{cards}</div></section>',
        og_image=thumbnail(videos[0]) if videos else None,
        exact_title=seo_title is not None,
    )


def detail(video: Video) -> str:
    playable = media(video)
    poster = thumbnail(video)
    dimensions = media_dimensions(video)
    if playable:
        media_url = f"{MEDIA_BASE_URL}/media/video/{playable.id}"
        poster_attr = f' poster="{esc(poster)}"' if poster else ""
        player = f'<video class="public-video-player" controls playsinline preload="metadata"{poster_attr}{dimensions}><source src="{esc(media_url)}" type="video/mp4">動画を再生できません。</video>'
    elif poster:
        player = f'<img class="detail-poster" src="{esc(poster)}" alt="@{esc(video.x_username)}の動画" loading="eager" decoding="async"{dimensions}><a class="x-button" href="{esc(video.x_post_url)}" target="_blank" rel="noopener noreferrer">Xで見る ↗</a>'
    else:
        player = f'<div class="no-player">この動画はXで視聴できます。<a class="x-button" href="{esc(video.x_post_url)}" target="_blank" rel="noopener noreferrer">Xで見る ↗</a></div>'
    creator_url = f'https://x.com/{quote(video.x_username, safe="")}'
    title = video_title(video)
    description = video_description(video)
    upload_date = x_posted_time(video)
    if upload_date.tzinfo is None:
        upload_date = upload_date.replace(tzinfo=timezone.utc)
    structured_data = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": title,
        "description": description,
        "uploadDate": upload_date.isoformat(),
    }
    if poster:
        structured_data["thumbnailUrl"] = [poster]
    if playable:
        structured_data["contentUrl"] = f"{MEDIA_BASE_URL}/media/video/{playable.id}"
        duration_ms = playable.duration_ms or video.duration_ms
        if duration_ms:
            total_seconds = max(1, int(duration_ms / 1000))
            minutes, seconds = divmod(total_seconds, 60)
            structured_data["duration"] = f"PT{minutes}M{seconds}S"
    content = (
        f'<section class="video-detail"><div class="player-panel">{player}</div>'
        f'<a class="creator-account-card" href="{creator_url}" target="_blank" rel="noopener noreferrer">'
        f'<h1>{esc(title)}</h1><span>@{esc(video.x_username)} ↗</span></a>'
        f'<a class="source-link" href="{esc(video.x_post_url)}" target="_blank" rel="noopener noreferrer">元のX投稿を開く ↗</a></section>'
    )
    return shell(
        title=title,
        description=description,
        canonical_path=f"/video/{video.id}/",
        content=content,
        og_image=poster,
        og_type="video.other",
        structured_data=structured_data,
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
                selectinload(Video.media_items), selectinload(Video.source_account),
                selectinload(Video.categories), selectinload(Video.tags),
            ).where(
                Video.publication_status == "published",
                Video.status != "blocked",
                Video.is_public.is_(True),
                Video.deleted_at_x.is_(None),
                ~Video.reports.any(Report.status.in_(("open", "reviewing"))),
            )
        ).unique())

        newest = sorted(videos, key=lambda item: (x_posted_time(item), item.id), reverse=True)
        popular = sorted(videos, key=lambda item: (metric_score(item), published_time(item), item.id), reverse=True)
        since = datetime.now(timezone.utc) - timedelta(hours=48)
        trending = [item for item in popular if published_time(item).replace(tzinfo=published_time(item).tzinfo or timezone.utc) >= since]

        write("index.html", listing(
            "新着動画", "/", newest[:24],
            seo_title="XPeach｜Xで話題の動画を新着・人気・急上昇から探せる動画サイト",
            description="XPeachは、Xで話題の動画を新着・人気・急上昇から探せる動画サイトです。気になる投稿を見つけやすく整理して紹介します。",
        ))
        write("new/index.html", listing(
            "新着動画", "/new/", newest,
            seo_title="新着動画｜XPeach",
            description="XPeachの新着動画一覧。Xで話題の最新動画を見つけやすく整理して紹介します。",
        ))
        write("popular/index.html", listing(
            "人気動画", "/popular/", popular,
            seo_title="人気動画｜XPeach",
            description="XPeachで人気の動画をチェック。多く見られているX動画を見つけやすくまとめています。",
        ))
        write("trending/index.html", listing(
            "急上昇動画", "/trending/", trending,
            seo_title="急上昇動画｜XPeach",
            description="XPeachで注目が高まっている急上昇動画をチェック。今見られているX動画を探せます。",
        ))

        creators: dict[str, list[Video]] = {}
        categories: dict[str, tuple[object, list[Video]]] = {}
        for video in newest:
            creators.setdefault(video.x_username, []).append(video)
            for category in video.categories:
                if category.is_active:
                    categories.setdefault(category.slug, (category, []))[1].append(video)
            write(f"video/{video.id}/index.html", detail(video))
        for username, creator_videos in creators.items():
            write(
                f"creator/{quote(username, safe='')}/index.html",
                listing(f"@{username}の動画", f"/creator/{quote(username, safe='')}/", creator_videos),
            )
        category_links = "".join(
            f'<a class="creator-account-card" href="/category/{quote(slug, safe="")}/"><h2>{esc(category.name)}</h2><span>{len(items)}本</span></a>'
            for slug, (category, items) in sorted(categories.items(), key=lambda item: (item[1][0].sort_order, item[1][0].name))
        ) or '<p>公開中のカテゴリはまだありません。</p>'
        write("categories/index.html", shell(
            title="動画カテゴリ",
            description="XPeachで公開審査済みの動画をカテゴリから探せます。",
            canonical_path="/categories/",
            content=f'<section class="message-page"><h1>動画カテゴリ</h1>{category_links}</section>',
        ))
        for slug, (category, category_videos) in categories.items():
            write(
                f"category/{quote(slug, safe='')}/index.html",
                listing(f"{category.name}の動画", f"/category/{quote(slug, safe='')}/", category_videos),
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
            robots="noindex,nofollow",
        ))

        generated_at = datetime.now(timezone.utc)

        def sitemap_url(path: str, modified: datetime | None = None) -> str:
            value = modified or generated_at
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return f"  <url><loc>{BASE_URL}{path}</loc><lastmod>{value.date().isoformat()}</lastmod></url>\n"

        urls = [(path, generated_at) for path in ("/", "/new/", "/popular/", "/trending/", "/categories/")]
        urls += [(f"/video/{video.id}/", video.updated_at or published_time(video)) for video in newest]
        urls += [
            (f"/creator/{quote(username, safe='')}/", max((item.updated_at or published_time(item)) for item in items))
            for username, items in creators.items()
        ]
        urls += [
            (f"/category/{quote(slug, safe='')}/", max((item.updated_at or published_time(item)) for item in items))
            for slug, (_, items) in categories.items()
        ]
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
            sitemap_url(path, modified) for path, modified in urls
        ) + "</urlset>\n"
        write("sitemap.xml", sitemap)
        write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /admin/\nDisallow: /api/admin\nDisallow: /api/admin/\nDisallow: /report-received\n\nSitemap: {BASE_URL}/sitemap.xml\n")

    assets = OUTPUT / "assets"
    assets.mkdir()
    shutil.copy("/app/app/static/brand/logo.svg", assets / "logo.svg")
    shutil.copy("/app/app/static/brand/favicon.svg", assets / "favicon.svg")
    shutil.copy(PROJECT_ROOT / "public/assets/app.css", assets / "app.css")
    shutil.copy(PROJECT_ROOT / "public/assets/app.js", assets / "app.js")
    shutil.copy(PROJECT_ROOT / "public/_headers", OUTPUT / "_headers")
    print(f"Exported {len(videos)} published videos to {OUTPUT}")


if __name__ == "__main__":
    main()
