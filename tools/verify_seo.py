"""Fail fast when generated public SEO files drift from the www canonical policy."""

from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
BASE = "https://www.xpeach.tv"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


robots = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
require(f"Sitemap: {BASE}/sitemap.xml" in robots, "robots sitemap URL is not canonical")
for rule in ("Disallow: /admin", "Disallow: /api/admin"):
    require(rule in robots, f"robots is missing {rule}")

tree = ElementTree.parse(PUBLIC / "sitemap.xml")
namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
locations = [item.text or "" for item in tree.findall("s:url/s:loc", namespace)]
require(locations and all(item.startswith(f"{BASE}/") for item in locations), "sitemap contains a non-www URL")
require(not any("/admin" in item for item in locations), "sitemap contains an admin URL")

html_files = sorted(PUBLIC.rglob("*.html"))
for path in html_files:
    source = path.read_text(encoding="utf-8")
    require(f'<link rel="canonical" href="{BASE}/' in source, f"non-canonical HTML: {path}")
    require('<meta name="description"' in source, f"missing description: {path}")
    require('<meta property="og:url"' in source, f"missing og:url: {path}")
    require('<meta name="twitter:card"' in source, f"missing twitter card: {path}")
    require(source.count("<h1") == 1, f"expected exactly one h1: {path}")

for path in (PUBLIC / "video").glob("*/index.html"):
    source = path.read_text(encoding="utf-8")
    require('type="application/ld+json"' in source, f"missing VideoObject: {path}")
    if 'class="public-video-player"' in source:
        require('src="https://www.xpeach.tv/media/video/' in source, f"video is not using same-origin relay: {path}")
        require('https://admin.xpeach.tv/media/video/' not in source, f"video leaks cross-subdomain source: {path}")

expected_metadata = {
    "index.html": (
        "XPeach｜Xで話題の動画を新着・人気・急上昇から探せる動画サイト",
        "XPeachは、Xで話題の動画を新着・人気・急上昇から探せる動画サイトです。気になる投稿を見つけやすく整理して紹介します。",
    ),
    "new/index.html": (
        "新着動画｜XPeach",
        "XPeachの新着動画一覧。Xで話題の最新動画を見つけやすく整理して紹介します。",
    ),
    "popular/index.html": (
        "人気動画｜XPeach",
        "XPeachで人気の動画をチェック。多く見られているX動画を見つけやすくまとめています。",
    ),
    "trending/index.html": (
        "急上昇動画｜XPeach",
        "XPeachで注目が高まっている急上昇動画をチェック。今見られているX動画を探せます。",
    ),
}
for relative_path, (title, description) in expected_metadata.items():
    source = (PUBLIC / relative_path).read_text(encoding="utf-8")
    require(f"<title>{title}</title>" in source, f"unexpected title: {relative_path}")
    require(f'<meta name="description" content="{description}">' in source, f"unexpected description: {relative_path}")
    require(f'<meta property="og:title" content="{title}">' in source, f"unexpected og:title: {relative_path}")
    require(f'<meta property="og:description" content="{description}">' in source, f"unexpected og:description: {relative_path}")
    require(f'<meta name="twitter:title" content="{title}">' in source, f"unexpected twitter:title: {relative_path}")
    require(f'<meta name="twitter:description" content="{description}">' in source, f"unexpected twitter:description: {relative_path}")

print(f"SEO verification passed: {len(locations)} sitemap URLs, {len(html_files)} HTML pages checked")
