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
    require('type="application/ld+json"' in path.read_text(encoding="utf-8"), f"missing VideoObject: {path}")

print(f"SEO verification passed: {len(locations)} sitemap URLs, {len(html_files)} HTML pages checked")
