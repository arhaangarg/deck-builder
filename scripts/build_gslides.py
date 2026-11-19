"""Build a Google Slides deck of native, editable shapes from shape specs.

The deck is built as a PowerPoint file tuned for Google's text layout, then imported into Slides.
Import is the only route that keeps every shape exact: the Slides API cannot set a corner radius.
"""
import argparse
import json
import tempfile
from pathlib import Path

import build_pptx
from google_client import connect, download
from spec_io import load_specs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("specs", help="directory of shape specs from extract.py")
    ap.add_argument("--title", required=True, help="name of the presentation in Drive")
    ap.add_argument("--state", required=True, help="JSON file that remembers which presentation this deck is")
    ap.add_argument("--via", choices=["api", "gws"], default="api", help="Google's Python client (default) or the gws CLI")
    ap.add_argument("--client-secret", help="OAuth client file, if not at ~/.config/deck-builder/client_secret.json")
    ap.add_argument("--thumbnails", help="directory to save a render of each built slide into, for verify.py")
    ap.add_argument("--force", action="store_true", help="rebuild even if someone edited the deck in Slides since the last build")
    args = ap.parse_args()

    google = connect(args.via, args.client_secret)
    state_path = Path(args.state)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    file_id = state.get("presentationId")
    # A rebuild replaces every slide. If the deck changed in Slides since we built it, those edits would be lost.
    if file_id and not args.force and google.revision(file_id) != state.get("revision"):
        raise SystemExit(
            f"https://docs.google.com/presentation/d/{file_id} was edited in Google Slides after the last build.\n"
            "Fold those edits into the locked drafts first, then rerun with --force.")

    with tempfile.TemporaryDirectory() as tmp:
        pptx = Path(tmp) / "deck.pptx"
        build_pptx.build(args.specs, pptx, target="gslides")
        file_id = google.import_pptx(pptx, args.title, file_id)

    print(f"https://docs.google.com/presentation/d/{file_id}")

    if args.thumbnails:
        out = Path(args.thumbnails)
        out.mkdir(parents=True, exist_ok=True)
        slide_ids = [slide_id for slide_id, _ in load_specs(args.specs)]
        for slide_id, page_id in zip(slide_ids, google.page_ids(file_id)):
            download(google.thumbnail_url(file_id, page_id), out / f"{slide_id}.png")

    # Recorded last: reading thumbnails must not look like someone's edit on the next build.
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"presentationId": file_id, "revision": google.revision(file_id)}, indent=1))


if __name__ == "__main__":
    main()
