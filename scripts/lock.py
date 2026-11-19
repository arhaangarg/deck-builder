"""Lock a picked draft: copy that one slide into its own file, so later rounds can never change it."""
import argparse
import sys
from pathlib import Path

from draft_files import read_draft, standalone_page

BASE_CSS = (Path(__file__).resolve().parent / "slide_base.css").read_text()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", help="the draft file holding the picked slide")
    ap.add_argument("--draft", required=True, help="the picked draft's data-draft value, for example b")
    ap.add_argument("--out", required=True, help="the locked file to write, for example locked/s03_method.html")
    ap.add_argument("--replace", action="store_true", help="overwrite an existing lock (only when the user picked again)")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists() and not args.replace:
        sys.exit(f"{out} is already locked. Edit it directly for small changes, or pass --replace if the user picked a different draft.")
    parts = read_draft(args.html)
    picked = [s for s in parts["slides"] if s["draft"] == args.draft]
    if len(picked) != 1:
        sys.exit(f"{args.html} has {len(picked)} slides with data-draft=\"{args.draft}\" (found: {[s['draft'] for s in parts['slides']]})")
    css = parts["css"] if BASE_CSS.strip() in parts["css"] else BASE_CSS + parts["css"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(standalone_page(out.stem, parts["fonts"], "body { margin: 0; }\n" + css, picked[0]["html"]))
    print(f"locked {picked[0]['id'] or out.stem} draft {args.draft} -> {out}")


if __name__ == "__main__":
    main()
