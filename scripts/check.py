"""Check draft slides: every element must map to a native shape, and the layout must be clean."""
import argparse
import json
import sys
from pathlib import Path

from browser import open_page


def load_rules(path):
    """Read the deck's own rules file, if the team wrote one. No rule has a default."""
    return json.loads(Path(path).read_text()) if path else {}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", nargs="+", help="draft files, each holding one or more .slide elements")
    ap.add_argument("--rules", help="rules.json with any of: minText, minPad (fractions of slide width), banned (characters)")
    args = ap.parse_args()
    rules = load_rules(args.rules)
    failed = False
    for path in args.html:
        with open_page(path) as page:
            results = page.evaluate("rules => window.deckBuilder.check(rules).map(r => ({...r, spec: undefined}))", rules)
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
