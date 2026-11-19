# Phase 6: build the deck

Build only from locked slides.
Every value in the built deck comes from the locked drafts, through a shape spec.

```
locked/*.html  ->  extract.py  ->  spec/*.json  ->  build_pptx.py     ->  out/deck.pptx
                                                ->  build_gslides.py  ->  Google Slides
locked/*.html  ->  export_pdf.py  ->  out/deck.pdf
```

Run every command from the deck folder, with `<skill>/.venv/bin/python <skill>/scripts/<name>.py`.

## 1. Check that every slide is locked

`locked/` must hold one file for each entry in `slides.json`.
If a slide is still open, go back to the review loop.
Run `check.py locked/*.html` (add `--rules rules.json` if the deck has one) and fix any problem in the locked file.

## 2. Extract the shape specs

```
extract.py locked/*.html --out spec
```

This writes, for each slide:

- `spec/<id>.json`: every shape, with its position, colors, font and measured line breaks, as fractions of the slide width
- `spec/<id>.png`: a render of the draft, which `verify.py` compares against
- `spec/assets/`: the images the slides use

Run it again whenever a locked file changes.

## 3. Build what the user asked for

### PowerPoint

```
build_pptx.py spec --out out/deck.pptx
```

To rebuild some slides and leave the rest of the file untouched:

```
build_pptx.py spec --out out/deck.pptx --only s03_method s07_results
```

Use `--only` when the user has already edited other slides in PowerPoint.

### Google Slides

Creating the deck puts content in the user's Google Drive, so confirm with them first.
Sign in once: [google-auth.md](google-auth.md).

```
build_gslides.py spec --title "<Deck Name>" --state out/gslides.json --thumbnails out/gslides
```

Add `--via gws` to use the `gws` CLI instead of the OAuth client.
The command prints the deck's link.
`out/gslides.json` remembers which presentation this deck is, so every later build updates the same link.

How it works, and what follows from it:

- The deck is built as a PowerPoint file tuned for Google's text layout, then imported into Slides.
  The Slides API cannot set a corner radius, so import is the only way to keep every shape exact and native.
- **A rebuild replaces the whole deck.** There is no single slide rebuild for Google Slides.
- **Edits made in Slides are protected.** If anyone changed the deck in Slides since the last build, the script stops and says so.
  Tell the user what would be lost.
  Fold those edits into the locked drafts, then rerun with `--force`.
  Never pass `--force` without the user's word.

### PDF

```
export_pdf.py locked/*.html --out out/deck.pdf
```

This prints the locked drafts themselves, so the PDF is vector and identical to them.
It does not go through the shape spec.

## 4. Verify

Go to [8-verify.md](8-verify.md).
The build is not done until it passes.

## Changes after the build

| The user wants | Do this |
| --- | --- |
| A small edit to a slide | Edit `locked/<id>.html`, run `check.py`, extract, rebuild, verify. |
| A new layout for a slide | A hybrid round (phase 5), lock with `--replace`, then the same. |
| To keep edits they made in PowerPoint | Rebuild only the other slides with `--only`. |
| To keep edits they made in Google Slides | Fold the edits into the locked drafts first. A rebuild replaces every slide. |

The draft is the truth.
If the build and the draft differ, fix the build, never the approved draft.

## How text is matched (for maintainers)

Each app places text its own way, so `build_pptx.py` positions every text box from the draft's first baseline.
These numbers were measured across ten fonts and many sizes, and they live as constants at the top of the script.

- **Google Slides.** A line is 1.2 times the font size at 100% spacing, with the baseline 0.96 font sizes below its top.
  On import, Slides reads an exact line spacing as a percentage of the font size.
- **PowerPoint.** With exact line spacing up to 1.2 times the font size, 1.045 times the font's descent sits under the baseline.
  Above that, the baseline sits three quarters of the way down the line.
- **Both.** Lines carry the draft's own breaks, and each text box is a little wider than its text, so no app wraps a line again.
  Line breaks carry the run's font size, since a bare break falls back to the theme's size and stretches the line.
