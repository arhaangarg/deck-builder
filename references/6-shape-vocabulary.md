# The shape vocabulary

A draft may only contain things that PowerPoint and Google Slides can draw as native shapes.
That is what lets the built deck match the draft exactly and stay editable.
`check.py` enforces this list.
Anything outside it fails, with a message that names the element.

This file sets no style.
It only says which building blocks exist.

## The draft file

One file holds the four drafts of one slide.

```html
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=...">
<link rel="stylesheet" href="<skill>/scripts/slide_base.css">
<link rel="stylesheet" href="../../deck.css">
<style>
  /* this slide's own layout rules */
</style>
</head>
<body>
<div class="slide" data-slide="s03_method" data-draft="a" data-name="Big number" data-notes="Speaker notes."> ... </div>
<div class="slide" data-slide="s03_method" data-draft="b" data-name="Timeline"> ... </div>
<div class="slide" data-slide="s03_method" data-draft="c" data-name="Comparison"> ... </div>
<div class="slide" data-slide="s03_method" data-draft="d" data-name="Diagram"> ... </div>
</body>
</html>
```

- `data-slide` is the slide id from `slides.json`. `data-draft` is `a`, `b`, `c` or `d`. `data-name` is a two or three word name for the idea.
- `data-notes` is optional. It becomes the slide's speaker notes.
- Use the absolute path of `slide_base.css`. It makes each `.slide` a 16:9 box and turns on `cqw` units.
- Size and place everything in `cqw` (1cqw is 1% of the slide width), or inside an SVG `viewBox`. Never use `px`.
- Elements stack in source order: later elements sit on top. `z-index` is not allowed.

## What you can use

| Building block | Write it as | Becomes |
| --- | --- | --- |
| Rectangle | Any HTML element with a `background-color`, a `border`, or both. Or SVG `<rect>`. | Rectangle |
| Rounded rectangle | The same, with `border-radius` (HTML) or `rx` (SVG). | Rounded rectangle with that radius |
| Circle | A square HTML element with `border-radius: 50%`. Or SVG `<circle>`. | Ellipse |
| Oval | SVG `<ellipse>`. | Ellipse |
| Line | SVG `<line>`, at any angle. | Straight line |
| Arrow | SVG `<line>` with the standard arrowhead on either end or both (below). | Line with a native arrowhead |
| Text | Any HTML element that holds text directly. Or a one line SVG `<text>`. | Text box |
| Image | `<img>` or SVG `<image>`, PNG or JPEG. | Picture |

An HTML element with a background and text becomes two shapes: a box, and a text box on top of it.

## Rules for each block

**Boxes**

- Fills are flat colors. Transparency is fine: use `opacity` or an `rgba()` color.
- A border must be `solid`, and the same width and color on all four sides. For a line on one side only, draw an SVG `<line>`.
- All four corners share one radius.
- For a dashed outline, draw an SVG `<rect>`, `<circle>` or `<ellipse>` with a standard dash pattern (below).
- A non-square HTML element with `border-radius: 50%` becomes a pill, not an oval.

**Text**

- A text block holds text and inline tags only: `<b>`, `<i>`, `<u>`, `<span>` with a color, `<br>`.
  Do not nest a block or an inline block inside it.
- The build keeps the draft's line breaks exactly, so a paragraph may wrap freely.
- Use one font size per block. Start a new block for a different size.
- Bold means a font weight of 600 or more. Lighter weights all become regular.
- Alignment is left, center or right.
- Not allowed: `letter-spacing`, `text-transform` (type the final letters), text shadows, justified text, vertical text, a background on inline text, a word that breaks across two lines.
- SVG `<text>` is one line. Use one `<text>` per line, and `text-anchor` to align it.

**Lines and arrows**

- Lines have flat ends: leave `stroke-linecap` at its default.
- The only arrowhead is this marker. Copy it as it is, and change only the `id`.

```html
<defs>
  <marker id="arrow" markerUnits="strokeWidth" markerWidth="5" markerHeight="3.3" viewBox="0 0 5 3.3"
          refX="0" refY="1.65" orient="auto-start-reverse">
    <path d="M0,0 L5,1.65 L0,3.3 z" fill="context-stroke"/>
  </marker>
</defs>
<line x1="100" y1="80" x2="500" y2="80" stroke="..." stroke-width="4" marker-end="url(#arrow)"/>
```

- The head starts where the line ends, so stop the line five stroke widths short of where the tip should land.
- The only dash patterns are these two, as multiples of the stroke width:

| Pattern | `stroke-dasharray` | Example at `stroke-width="3"` |
| --- | --- | --- |
| Dashed | 4 on, 3 off | `stroke-dasharray="12 9"` |
| Dotted | 1 on, 3 off | `stroke-dasharray="3 9"` |

The arrowhead and the two dash patterns are fixed because they are the only ones both apps draw the same way.
They were measured in both.

**Images**

- The box must have the image's own aspect ratio. Crop the file, not the box.
- No rounded corners and no opacity on an image. Bake both into the file.
- SVG files cannot be placed. Export them to PNG, or redraw them from the blocks above.

**SVG**

- `<svg>` and `<g>` are fine as containers. `transform` on them may move and scale evenly, but not rotate or skew.
- Only `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<text>` and `<image>` draw anything.

## What is never allowed

| Not allowed | Use instead |
| --- | --- |
| `<path>`, `<polygon>`, `<polyline>`, curves | Lines, boxes and ellipses, or an image |
| Gradients, background images | A flat color, or an `<img>` |
| Shadows, filters, blur | Nothing. Use a flat fill or a border for separation |
| Clip paths and masks | Crop the image file |
| CSS `transform`, rotated shapes | Lay it out without rotation. Only lines may sit at an angle |
| `::before` and `::after` content | A real element |
| `outline` | `border` |
| `<canvas>`, `<video>`, `<iframe>`, form controls | An image |
| Content clipped by `overflow` | Make it fit |

Charts and icons follow the same rule.
Build a bar chart from rectangles, lines and text.
If a visual needs curves, make it an image.

## Layout checks

`check.py` also fails a draft when:

- text runs off the slide
- two text blocks overlap
- text spills out of the box it sits in
- a font did not load
- the draft breaks a rule in the deck's `rules.json`, if the team wrote one

## Known limits

- **Fonts.** Google Slides only has Google Fonts. PowerPoint only has fonts installed on the machine that opens the file.
- **Thin arrows in PowerPoint.** On a line thinner than 2pt (0.21% of the slide width), PowerPoint draws the head as if the line were 2pt.
- **Arrowhead width in Slides.** Its head is 3.6 stroke widths wide, not 3.3. The length matches.
- **Dashed outlines.** The pattern matches, but where the first dash starts on a shape's outline can differ.
