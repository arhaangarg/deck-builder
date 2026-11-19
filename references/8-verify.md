# Phase 6, continued: verify the build

A build is done when it matches the locked drafts and every shape is editable.
Check both, for every output.

## 1. Render what was built

**PowerPoint**

```
render_pptx.py out/deck.pptx --out out/pptx
```

This opens the file in PowerPoint (macOS) or LibreOffice and saves one PNG per slide.
PowerPoint is preferred, since it is what the audience will use.
The deck's fonts must be installed on this machine first.
If one is missing, the app swaps in another font and the check fails.

**Google Slides**

`build_gslides.py --thumbnails out/gslides` already saved Google's own render of each slide.

**PDF**

Nothing to render.
Open `out/deck.pdf` and check the page count and the fonts.

## 2. Compare with the drafts

```
verify.py spec out/pptx
verify.py spec out/gslides
```

For every text block, this measures how far the built text sits from the draft's text.
It passes when the largest shift is at most 0.2% of the slide width.

```
ok   s03_method: worst text shift 0.06% of slide width, 0.48% of pixels differ
FAIL s04_results: worst text shift 0.90% of slide width, 2.10% of pixels differ
    dx +0.00 dy +0.90 dw +0.00 dh +0.00  Results at a glance
```

- `dx`, `dy`: how far the text moved. `dw`, `dh`: how much its size changed. All in percent of the slide width.
- `missing text` means no ink was found where the text should be.
- The pixel figure is for information. Anti-aliasing alone gives up to about 1%.

Add `--diff out/diff` to save a picture of each slide: the draft, the build, and their difference, stacked.

## 3. Look at every slide yourself

Numbers miss things.
Open each diff picture, or the draft render and the built render side by side, and compare them closely.
Look at arrowheads, dashes, corner radii, stacking order, image placement and colors, since `verify.py` only measures text.

## 4. Check that it is editable

Open the built deck and confirm:

- each shape selects and moves on its own
- text is real text, in the right font
- no slide is one pasted picture

## When something fails

| What you see | Likely cause | Fix |
| --- | --- | --- |
| Every text block is wider or narrower | The font is missing in that app | Install it (PowerPoint), or pick a Google Font (Slides) and redo the slide's lock |
| One block wraps differently | A browser minimum font size, or a font that loaded late in the draft | Run `check.py` on the locked file again, then extract again |
| One block sits too high or low | Mixed font sizes in one block | Split it into one block per size in the locked file |
| A shape is missing or wrong | The draft uses something outside the vocabulary | `check.py` should have caught it. Fix the draft, and report the gap in the check |

Fix the cause, rebuild, and verify again.
Never change an approved draft just to make the numbers pass.
If a fix needs a visible change to a locked slide, show the user first.

## Report

Tell the user, per output: the link or file path, the worst text shift, and anything from [6-shape-vocabulary.md](6-shape-vocabulary.md)'s known limits that shows in this deck.
