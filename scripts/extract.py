"""Read locked slides into shape specs (JSON) plus a reference render of each, for the builders and verify."""
import argparse
import base64
import hashlib
import json
import mimetypes
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from browser import open_page


def save_image(src, assets):
    """Copy an image the slide uses into assets/ and return its file name."""
    if src.startswith("data:"):
        header, data = src.split(",", 1)
        raw = base64.b64decode(data) if ";base64" in header else urllib.parse.unquote_to_bytes(data)
        ext = mimetypes.guess_extension(header[5:].split(";")[0]) or ".bin"
    else:
        with urllib.request.urlopen(src) as response:  # file:// and https:// both work
            raw = response.read()
        ext = Path(urllib.parse.urlparse(src).path).suffix or ".bin"
    name = hashlib.sha1(raw).hexdigest()[:12] + ext
    (assets / name).write_bytes(raw)
    return name


def extract(html_path, out_dir):
    """Write <id>.json and <id>.png for every slide in html_path; return the ids."""
    out_dir = Path(out_dir)
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    ids = []
    with open_page(html_path) as page:
        results = page.evaluate("window.deckBuilder.check()")
        for r in results:
            spec = r["spec"]
            slide_id = spec["id"] or f"slide{r['index'] + 1:02d}"
            if r["problems"]:
                sys.exit(f"{html_path} [{slide_id}] is not buildable:\n  - " + "\n  - ".join(r["problems"]))
            for el in spec["elements"]:
                if el["type"] == "image":
                    if el["src"].lower().split("?")[0].endswith(".svg") or el["src"].startswith("data:image/svg"):
                        sys.exit(f"{slide_id}: SVG images cannot be placed natively. Export the image as PNG.")
                    el["src"] = "assets/" + save_image(el["src"], assets)
            (out_dir / f"{slide_id}.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False))
            page.locator(".slide").nth(r["index"]).screenshot(path=str(out_dir / f"{slide_id}.png"))
            ids.append(slide_id)
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", nargs="+", help="locked slide files")
    ap.add_argument("--out", required=True, help="directory for the specs")
    args = ap.parse_args()
    for path in args.html:
        for slide_id in extract(path, args.out):
            print(f"{slide_id}: {args.out}/{slide_id}.json")


if __name__ == "__main__":
    main()
