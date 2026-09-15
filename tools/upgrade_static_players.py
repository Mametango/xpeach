"""Upgrade an existing static export to native HTML5 card players."""

from pathlib import Path
import re


PUBLIC = Path(__file__).resolve().parent.parent / "public"
PATTERN = re.compile(
    r'<div class="media-frame inline-player" data-inline-player>'
    r'<button[^>]*data-video-src="([^"]+)"'
    r'(?: data-poster="([^"]+)")?[^>]*>.*?</button></div>',
    re.DOTALL,
)


def replace(match: re.Match[str]) -> str:
    source, poster = match.groups()
    poster_attr = f' poster="{poster}"' if poster else ""
    return (
        '<div class="media-frame inline-player">'
        '<video class="inline-card-video" controls playsinline preload="none"'
        f'{poster_attr}><source src="{source}" type="video/mp4">'
        '動画を再生できません。</video></div>'
    )


changed = 0
players = 0
for path in PUBLIC.rglob("*.html"):
    before = path.read_text(encoding="utf-8")
    after, count = PATTERN.subn(replace, before)
    after = after.replace('/assets/app.css">', '/assets/app.css?v=20260916-2">')
    after = after.replace('/assets/app.js" defer>', '/assets/app.js?v=20260916-2" defer>')
    if after != before:
        path.write_text(after, encoding="utf-8", newline="\n")
        changed += 1
        players += count

print(f"Updated {players} card players across {changed} HTML files")
