"""Read draft files into self-contained parts: remote font links, CSS text, and each slide's HTML."""
import base64
import mimetypes
import re
import urllib.parse
import urllib.request
from pathlib import Path

from browser import open_page

COLLECT = """() => ({
  fonts: [...document.querySelectorAll('link[rel="stylesheet"]')].map(l => l.href).filter(h => h.startsWith('http')),
  localSheets: [...document.querySelectorAll('link[rel="stylesheet"]')].map(l => l.href).filter(h => h.startsWith('file:')),
  styles: [...document.querySelectorAll('style')].map(s => s.textContent),
  slides: [...document.querySelectorAll('.slide')].map(s => ({
    id: s.dataset.slide || '', draft: s.dataset.draft || '', name: s.dataset.name || '', html: s.outerHTML,
    images: [...s.querySelectorAll('img')].map(i => [i.getAttribute('src'), i.src])
      .concat([...s.querySelectorAll('image')].map(i => [i.getAttribute('href'), i.href.baseVal && new URL(i.href.baseVal, document.baseURI).href])),
  })),
})"""


def data_uri(url):
    """Turn a local file URL into a data URI so the page that embeds it needs no other file."""
    path = Path(urllib.request.url2pathname(urllib.parse.urlparse(url).path))
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def read_draft(path):
    """Return {"fonts", "css", "slides"} for one draft file, with local stylesheets and images inlined."""
    with open_page(path) as page:
        parts = page.evaluate(COLLECT)
    css = [Path(urllib.request.url2pathname(urllib.parse.urlparse(url).path)).read_text() for url in parts["localSheets"]]
    css += parts["styles"]
    for slide in parts["slides"]:
        for written, resolved in slide.pop("images"):
            if written and resolved and resolved.startswith("file:"):
                slide["html"] = slide["html"].replace(f'"{written}"', f'"{data_uri(resolved)}"')
    return {"fonts": parts["fonts"], "css": "\n".join(css), "slides": parts["slides"]}


def scope_css(css, selector):
    """Confine a draft's CSS to its own slides, so drafts from different agents cannot restyle each other.

    Rules are nested under `selector` (CSS nesting). At-rules that cannot be nested stay at the top level.
    Rules written for html, body or :root are pointed at the scope itself, so what slides inherit still arrives.
    """
    hoisted = []

    def lift(match):
        hoisted.append(match.group(0))
        return ""

    css = re.sub(r"@import[^;]+;", lift, css)
    css = re.sub(r"@(font-face|keyframes\s+[\w-]+)\s*\{(?:[^{}]|\{[^{}]*\})*\}", lift, css)
    css = re.sub(r"(^|[{};,]\s*)(?:html|body|:root)(?=\s*[,{])", r"\1&", css, flags=re.M)
    return "\n".join(hoisted) + f"\n{selector} {{\n{css}\n}}\n"


def standalone_page(title, fonts, css, body):
    links = "\n".join(f'<link rel="stylesheet" href="{href}">' for href in dict.fromkeys(fonts))
    return f"<!doctype html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n<title>{title}</title>\n{links}\n<style>\n{css}\n</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
