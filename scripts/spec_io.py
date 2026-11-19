"""Load shape specs from a directory, in deck order."""
import json
from pathlib import Path


def load_specs(spec_dir, only=None):
    """Return [(slide_id, spec)] sorted by id; slide ids start with their number, so this is deck order."""
    specs = []
    for path in sorted(Path(spec_dir).glob("*.json")):
        if only and path.stem not in only:
            continue
        specs.append((path.stem, json.loads(path.read_text())))
    missing = set(only or []) - {slide_id for slide_id, _ in specs}
    if missing:
        raise SystemExit(f"no spec for: {', '.join(sorted(missing))}")
    return specs


def text_of(el):
    """The lines of a text element as plain strings."""
    return ["".join(run["text"] for run in line) for line in el["lines"]]
