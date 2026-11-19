"""Build the review page: every slide of the deck with its four drafts, on one shareable page."""
import argparse
import html
import json
import re
from pathlib import Path

from draft_files import read_draft, scope_css

BASE_CSS = (Path(__file__).resolve().parent / "slide_base.css").read_text()

# The page's own chrome. It is deliberately plain so nothing competes with the drafts.
PAGE_CSS = """
:root { --bg: #f4f4f2; --panel: #ffffff; --ink: #1c1c1a; --muted: #6b6b66; --line: #dcdcd6; --accent: #1a6b4a; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #161615; --panel: #212120; --ink: #ecece8; --muted: #a0a09a; --line: #383836; --accent: #6fcf9f; } }
:root[data-theme="dark"] { --bg: #161615; --panel: #212120; --ink: #ecece8; --muted: #a0a09a; --line: #383836; --accent: #6fcf9f; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.5 system-ui, sans-serif; }
.rv-wrap { max-width: 1500px; margin: 0 auto; padding: 24px 16px 80px; }
.rv-top h1 { font-size: 24px; margin: 0 0 4px; }
.rv-top p { margin: 0; color: var(--muted); max-width: 70ch; }
.rv-nav { display: flex; flex-wrap: wrap; gap: 6px; margin: 16px 0 8px; }
.rv-nav a { color: var(--ink); text-decoration: none; border: 1px solid var(--line); border-radius: 999px; padding: 2px 10px; font-size: 13px; background: var(--panel); }
.rv-nav a.rv-done { color: var(--accent); border-color: var(--accent); }
.rv-slide { margin-top: 40px; }
.rv-slide > header { display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
.rv-slide h2 { font-size: 19px; margin: 0; }
.rv-status { font-size: 13px; color: var(--muted); }
.rv-status.rv-done { color: var(--accent); font-weight: 600; }
.rv-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 560px), 1fr)); gap: 20px; margin-top: 16px; }
.rv-grid.rv-one { grid-template-columns: minmax(0, 900px); }
.rv-fig { margin: 0; min-width: 0; }
.rv-frame { border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: var(--panel); }
.rv-fig figcaption { margin-top: 6px; font-size: 14px; color: var(--muted); }
.rv-fig figcaption b { color: var(--ink); }
details.rv-old { margin-top: 18px; }
details.rv-old summary { cursor: pointer; color: var(--muted); font-size: 14px; }
"""


def round_number(path):
    return int(re.search(r"r(\d+)", path.stem).group(1))


def figure(slide, label, name, scope):
    caption = f"<b>{html.escape(label)}</b>" + (f" · {html.escape(name)}" if name else "")
    return f'<figure class="rv-fig"><div class="rv-frame" data-src="{scope}">{slide["html"]}</div><figcaption>{caption}</figcaption></figure>'


def build(deck_dir, title):
    deck = Path(deck_dir)
    outline = json.loads((deck / "slides.json").read_text())
    fonts, css, sections, nav = [], [BASE_CSS], [], []
    for number, entry in enumerate(outline, start=1):
        slide_id = entry["id"]
        heading = f"{number} · {html.escape(entry['title'])}"
        locked = deck / "locked" / f"{slide_id}.html"
        rounds = sorted((deck / "drafts" / slide_id).glob("r*.html"), key=round_number)
        blocks = []
        if locked.exists():
            parts = read_draft(locked)
            scope = f"locked-{slide_id}"
            fonts += parts["fonts"]
            css.append(scope_css(parts["css"], f'[data-src="{scope}"]'))
            picked = parts["slides"][0]
            status = f'<span class="rv-status rv-done">Locked: draft {html.escape(picked["draft"].upper())}</span>'
            blocks.append(f'<div class="rv-grid rv-one">{figure(picked, f"{number}{picked["draft"].upper()}", picked["name"], scope)}</div>')
        elif rounds:
            status = f'<span class="rv-status">Round {round_number(rounds[-1])} · pick one, or say what to combine</span>'
        else:
            status = '<span class="rv-status">Not drafted yet</span>'
        # Open slides show their newest round. Older rounds, and every round of a locked slide, fold away below.
        for i, path in enumerate(reversed(rounds)):
            parts = read_draft(path)
            scope = f"{slide_id}-{path.stem}"
            fonts += parts["fonts"]
            css.append(scope_css(parts["css"], f'[data-src="{scope}"]'))
            figures = "".join(figure(s, f"{number}{s['draft'].upper()}", s["name"], scope) for s in parts["slides"])
            grid = f'<div class="rv-grid">{figures}</div>'
            if i == 0 and not locked.exists():
                blocks.append(grid)
            else:
                blocks.append(f'<details class="rv-old"><summary>Round {round_number(path)} drafts</summary>{grid}</details>')
        sections.append(f'<section class="rv-slide" id="{slide_id}"><header><h2>{heading}</h2>{status}</header>{"".join(blocks)}</section>')
        nav.append(f'<a href="#{slide_id}"{" class=\"rv-done\"" if locked.exists() else ""}>{number}</a>')
    links = "\n".join(f'<link rel="stylesheet" href="{href}">' for href in dict.fromkeys(fonts))
    done = sum(1 for e in outline if (deck / "locked" / f"{e['id']}.html").exists())
    intro = (f"{done} of {len(outline)} slides locked. Each open slide shows four drafts. "
             "Refer to a draft by its label (for example 3B) when you pick one or say what you like about it.")
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{html.escape(title)}</title>\n{links}\n<style>\n{PAGE_CSS}\n{''.join(css)}\n</style>\n</head>\n<body>\n<div class=\"rv-wrap\">\n"
            f'<div class="rv-top"><h1>{html.escape(title)}</h1><p>{intro}</p></div>\n<nav class="rv-nav">{"".join(nav)}</nav>\n'
            + "\n".join(sections) + "\n</div>\n</body>\n</html>\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("deck", help="the deck's working directory (holds slides.json, drafts/ and locked/)")
    ap.add_argument("--title", required=True, help="page title, two to four words, for example 'Launch Deck Drafts'")
    ap.add_argument("--out", help="file to write (default: <deck>/review.html)")
    args = ap.parse_args()
    out = Path(args.out) if args.out else Path(args.deck) / "review.html"
    out.write_text(build(args.deck, args.title))
    print(out)


if __name__ == "__main__":
    main()
