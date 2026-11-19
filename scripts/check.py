"""Check draft slides: every element must map to a native shape, and the layout must be clean."""
import argparse
import json
import sys
from pathlib import Path

from browser import open_page


def load_rules(path):
    """Read the deck's own rules file, if the team wrote one. No rule has a default."""
    return json.loads(Path(path).read_text()) if path else {}


def save_shots(page, results, stem, out):
    """Save one PNG per slide, named after the file and the draft."""
    out.mkdir(parents=True, exist_ok=True)
    for r in results:
        name = f"{stem}_{r['draft'] or r['index'] + 1}.png"
        page.locator(".slide").nth(r["index"]).screenshot(path=str(out / name))
        print(f"     {out / name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", nargs="+", help="draft files, each holding one or more .slide elements")
    ap.add_argument("--rules", help="rules.json with any of: minText, minPad (fractions of slide width), banned (characters)")
    ap.add_argument("--shots", help="directory to save a picture of every slide into, so you can look at them")
    args = ap.parse_args()
    rules = load_rules(args.rules)
    failed = False
    for path in args.html:
        with open_page(path) as page:
            results = page.evaluate("rules => window.deckBuilder.check(rules).map(r => ({...r, spec: undefined}))", rules)
            if args.shots:
                save_shots(page, results, Path(path).stem, Path(args.shots))
        if not results:
            print(f"{path}: no .slide element found")
            failed = True
        for r in results:
            name = f"{path} [{r['id'] or r['index']}{'/' + r['draft'] if r['draft'] else ''}]"
            if r["problems"]:
                failed = True
                print(f"FAIL {name}")
                for problem in r["problems"]:
                    print(f"  - {problem}")
            else:
                print(f"ok   {name}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
