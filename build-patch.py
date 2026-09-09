#!/usr/bin/env python3
"""Build patch.html from patch.md. Edit the markdown, then run this."""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
MD = ROOT / "patch.md"
TEMPLATE = ROOT / "patch.template.html"
OUT = ROOT / "patch.html"

SLIDE_META = {
    "cover": ("Cover", "cover"),
    "what's happening": ("Happening", "happening"),
    "why we're doing it": ("Why", "why act"),
    "watch the demo": ("Demo", "demo"),
    "what's needed to switch": ("Switch", "switch"),
    "when it is happening": ("When", "when act"),
    "when and how much": ("When", "when act"),
    "next steps": ("Next", "close"),
}

LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE = re.compile(r"`([^`]+)`")
HEADING = re.compile(r"^(#{1,3})\s+(.*)$")
EMBED = re.compile(r"^\[embed:\s*(.+?)\]\s*$", re.M)
VIDEO_ID = re.compile(r'"videoId":"([A-Za-z0-9_-]{11})"')
PLAY_ICON = (
    '<span class="vid-play" aria-hidden="true">'
    '<svg viewBox="0 0 68 48" focusable="false">'
    '<rect width="68" height="48" rx="14" fill="#FF0000"/>'
    '<path d="M27 14v20l20-10z" fill="#fff"/>'
    "</svg></span>"
)


def inline(text: str) -> str:
    parts: list[str] = []
    last = 0
    for m in LINK.finditer(text):
        parts.append(html.escape(text[last : m.start()], quote=False))
        parts.append(
            f'<a href="{html.escape(m.group(2), quote=True)}">{html.escape(m.group(1), quote=False)}</a>'
        )
        last = m.end()
    parts.append(html.escape(text[last:], quote=False))
    escaped = "".join(parts)
    return CODE.sub(r'<span class="mono">\1</span>', escaped)


def paragraphs(block: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", block.strip()) if p.strip()]


def take_embed(body: str) -> tuple[str, str | None]:
    match = EMBED.search(body)
    if not match:
        return body, None
    url = match.group(1).strip()
    cleaned = (body[: match.start()] + body[match.end() :]).strip()
    return cleaned, url


def youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    if host in {"youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
        return video_id or None
    if host not in {"youtube.com", "m.youtube.com", "youtube-nocookie.com"}:
        return None
    query = parse_qs(parsed.query)
    if query.get("v"):
        return query["v"][0]
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] in {"embed", "shorts", "live"}:
        return parts[1]
    return None


def latest_youtube_video_id(url: str) -> str | None:
    try:
        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; patch-pamphlet/1.0)"},
        )
        with urlopen(req, timeout=12) as resp:
            page = resp.read().decode("utf-8", "replace")
    except OSError:
        return None
    seen: list[str] = []
    for video_id in VIDEO_ID.findall(page):
        if video_id not in seen:
            seen.append(video_id)
    return seen[0] if seen else None


def poster_thumb(video_id: str) -> str:
    safe = html.escape(video_id, quote=True)
    return (
        f'<img class="vid-thumb" src="https://i.ytimg.com/vi/{safe}/maxresdefault.jpg" alt="" '
        f"onerror=\"this.onerror=null;this.src='https://i.ytimg.com/vi/{safe}/hqdefault.jpg'\">"
    )


def render_vid(url: str) -> str:
    playable_id = youtube_video_id(url)
    thumb_id = playable_id or latest_youtube_video_id(url)
    inner = (poster_thumb(thumb_id) if thumb_id else "") + PLAY_ICON
    if playable_id:
        return (
            f'              <div class="vid" data-youtube="{html.escape(playable_id, quote=True)}">\n'
            f'                <button type="button" class="vid-poster" aria-label="Play demo">{inner}</button>\n'
            "              </div>"
        )
    return (
        f'              <a class="vid vid-poster" href="{html.escape(url, quote=True)}" '
        f'target="_blank" rel="noreferrer" aria-label="Watch demo on YouTube">{inner}</a>'
    )


def parse_slide(raw: str) -> dict:
    lines = raw.strip().splitlines()
    title = ""
    rest: list[str] = []
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m and m.group(1) == "#":
            title = m.group(2).strip()
            rest = lines[i + 1 :]
            break
        rest.append(line)
    if not title:
        raise SystemExit("Each slide needs a # heading")

    key = title.casefold()
    rail, classes = SLIDE_META.get(key, (title.split()[0], key.replace(" ", "-")))
    body = "\n".join(rest).strip()
    return {"title": title, "rail": rail, "classes": classes, "body": body}


def split_rows(body: str) -> tuple[str, list[tuple[str, str]]]:
    chunks = re.split(r"^##\s+", body, flags=re.M)
    lede = chunks[0].strip()
    rows = []
    for chunk in chunks[1:]:
        lines = chunk.splitlines()
        heading = lines[0].strip()
        text = "\n".join(lines[1:]).strip()
        rows.append((heading, text))
    return lede, rows


def render_cover(slide: dict, num: str) -> str:
    lede, rows = split_rows(slide["body"])
    note = lede
    heading = slide["title"]
    lede_html = ""
    if rows:
        heading = rows[0][0]
        lede_html = rows[0][1]
        note = lede
    return f"""          <article class="slide {slide["classes"]}" id="cover">
            <div class="rail">
              <span class="rail-label">{html.escape(slide["rail"])}</span>
              <span class="rail-num">{num}</span>
            </div>
            <div class="body-pad">
              <img class="mark" src="assets/logo-white.svg" alt="Codemagic" />
              <p class="note">{inline(note)}</p>
              <h1>{inline(heading)}</h1>
              <p class="lede">{inline(lede_html)}</p>
            </div>
          </article>"""


def render_close(slide: dict, num: str) -> str:
    body, embed_url = take_embed(slide["body"])
    video = ""
    vm = re.search(r"^:::video\s+(.+)$", body, re.M)
    if vm:
        video = vm.group(1).strip()
        body = (body[: vm.start()] + body[vm.end() :]).strip()

    links = LINK.findall(body)
    body_wo_links = LINK.sub("", body)
    lede_parts = paragraphs(body_wo_links)
    lede = " ".join(lede_parts)

    actions = ""
    if links:
        primary, rest = links[0], links[1:]
        extra = "".join(
            f'\n                <a class="textlink" href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'
            for label, href in rest
        )
        actions = f"""              <div class="actions">
                <a class="btn btn-primary" href="{html.escape(primary[1], quote=True)}">{html.escape(primary[0])}</a>{extra}
              </div>"""

    vid = ""
    if embed_url:
        vid = render_vid(embed_url) + "\n"
    elif video:
        vid = f'              <div class="vid" role="img" aria-label="{html.escape(video, quote=True)} video placeholder">{html.escape(video)}</div>\n'
    return f"""          <article class="slide {slide["classes"]}" id="close">
            <div class="rail">
              <span class="rail-label">{html.escape(slide["rail"])}</span>
              <span class="rail-num">{num}</span>
            </div>
            <div class="body-pad">
              <h2>{inline(slide["title"])}</h2>
              <p class="lede">{inline(lede)}</p>
{vid}{actions}
              <div class="colophon">
                <a href="https://patch.codemagic.io/docs/">Docs</a>
                <a href="https://github.com/codemagic-ci-cd/codemagic-patch">GitHub</a>
                <a href="https://patch.codemagic.io/docs/introduction/pricing">Pricing</a>
                <span>© Nevercode Ltd.</span>
              </div>
            </div>
          </article>"""


def render_content(slide: dict, num: str, slug: str) -> str:
    raw, embed_url = take_embed(slide["body"])
    lede, rows = split_rows(raw)
    inner: list[str] = [f"              <h2>{inline(slide['title'])}</h2>"]
    if rows:
        if lede:
            inner.append(f'              <p class="lede">{inline(lede)}</p>')
        inner.append('              <div class="rows">')
        for heading, text in rows:
            inner.append("                <div class=\"row\">")
            inner.append(f"                  <h3>{inline(heading)}</h3>")
            inner.append(f"                  <p>{inline(text)}</p>")
            inner.append("                </div>")
        inner.append("              </div>")
    else:
        inner.append('              <div class="prose">')
        for para in paragraphs(lede):
            inner.append(f"                <p>{inline(para)}</p>")
        inner.append("              </div>")
    if embed_url:
        inner.append(render_vid(embed_url))
    body = "\n".join(inner)
    return f"""          <article class="slide {slide["classes"]}" id="{html.escape(slug, quote=True)}">
            <div class="rail">
              <span class="rail-label">{html.escape(slide["rail"])}</span>
              <span class="rail-num">{num}</span>
            </div>
            <div class="body-pad">
{body}
            </div>
          </article>"""


def main() -> None:
    slides = [parse_slide(chunk) for chunk in re.split(r"\n---\n", MD.read_text())]
    articles = []
    for i, slide in enumerate(slides, start=1):
        num = f"{i:02d}"
        classes = slide["classes"]
        if classes == "cover":
            articles.append(render_cover(slide, num))
        elif "close" in classes.split():
            articles.append(render_close(slide, num))
        else:
            slug = classes.split()[0]
            articles.append(render_content(slide, num, slug))
    html_out = TEMPLATE.read_text().replace("{{deck}}", "\n\n".join(articles))
    OUT.write_text(html_out)
    print(f"Wrote {OUT.name} from {MD.name} ({len(slides)} slides)")


if __name__ == "__main__":
    main()
