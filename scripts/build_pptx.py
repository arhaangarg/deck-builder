"""Build a PowerPoint deck of native, editable shapes from shape specs."""
import argparse
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

from spec_io import load_specs

SLIDE_WIDTH = Emu(12192000)  # 13.333in, PowerPoint's own widescreen width
EMU_PER_PT = 12700
ALIGN = {"start": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "end": PP_ALIGN.RIGHT}
# Both apps draw these two presets identically: 4 on 3 off, and 1 on 3 off, in stroke widths.
DASH = {"dashed": "dash", "dotted": "dot"}
# Arrowhead (width, length) presets that come closest to the standard 3.3 x 5 stroke widths arrowhead.
# PowerPoint draws med as 3 and lg as 5. Google Slides only has three sizes, and its smallest is 3.6 x 4.9.
ARROW_SIZE = {"powerpoint": ("med", "lg"), "gslides": ("sm", "sm")}
# PowerPoint with exact line spacing, measured across fonts, sizes and spacings (see references/7-build.md):
# up to 1.2 x the font size the font's descent (a touch more) sits under the baseline and the rest above it;
# beyond that the baseline sits three quarters of the way down the line.
PPT_NATURAL = 1.2
PPT_DESCENT_SCALE = 1.045
PPT_LOOSE_BASELINE = 0.75
# Google Slides lays a line out as 1.2 x the font size at 100% spacing, whatever the font, and on import it
# reads an exact spacing as a percentage of the font size. So a file meant for import states spacing / 1.2.
GSLIDES_LINE = 1.2
GSLIDES_BASELINE = 0.96  # baseline below the top of a 100% line, in font sizes


def emu(fraction):
    return Emu(round(fraction * SLIDE_WIDTH))


def set_alpha(color_parent, alpha):
    """Add transparency to the srgbClr under a solidFill, which python-pptx has no API for."""
    if alpha >= 1:
        return
    clr = color_parent.find(".//" + qn("a:srgbClr"))
    etree.SubElement(clr, qn("a:alpha")).set("val", str(round(alpha * 100000)))


def paint(shape, fill, stroke):
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill["hex"][1:])
        set_alpha(shape.fill._xPr, fill["alpha"])
    else:
        shape.fill.background()
    if stroke:
        outline(shape.line, stroke)
    else:
        shape.line.fill.background()


def outline(line, stroke):
    line.width = emu(stroke["width"])
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor.from_string(stroke["hex"][1:])
    ln = line._get_or_add_ln()
    set_alpha(ln, stroke["alpha"])
    if stroke["dash"] in DASH:
        etree.SubElement(ln, qn("a:prstDash")).set("val", DASH[stroke["dash"]])


def no_effects(shape):
    """Stop the theme adding a shadow the draft never had."""
    sp_pr = shape._element.spPr
    if sp_pr.find(qn("a:effectLst")) is None:
        etree.SubElement(sp_pr, qn("a:effectLst"))


def add_box(slide, el):
    w, h = el["w"], el["h"]
    if el["type"] == "ellipse":
        kind = MSO_SHAPE.OVAL
    else:
        kind = MSO_SHAPE.ROUNDED_RECTANGLE if el["radius"] > 0 else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, emu(el["x"]), emu(el["y"]), emu(w), emu(h))
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        shape.adjustments[0] = min(0.5, el["radius"] / min(w, h))
    paint(shape, el["fill"], el["stroke"])
    no_effects(shape)


def add_line(slide, el, target):
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, emu(el["x1"]), emu(el["y1"]), emu(el["x2"]), emu(el["y2"]))
    outline(line.line, el["stroke"])
    ln = line.line._get_or_add_ln()
    for key, tag in (("arrowStart", "a:headEnd"), ("arrowEnd", "a:tailEnd")):
        if el[key]:
            end = etree.SubElement(ln, qn(tag))
            end.set("type", "triangle")
            end.set("w", ARROW_SIZE[target][0])
            end.set("len", ARROW_SIZE[target][1])
    no_effects(line)


def text_placement(el, target):
    """Return (top of the text box, exact line spacing), both as fractions of slide width, for the app that will show it."""
    baseline = el["y"] + el["ascent"]
    advance = el["lineAdvance"]
    size = max(run["size"] for run in el["lines"][0])
    if target == "powerpoint":
        if advance <= PPT_NATURAL * size * 1.0005:
            return baseline - (advance - PPT_DESCENT_SCALE * el["descent"]), advance
        return baseline - PPT_LOOSE_BASELINE * advance, advance
    # Spacing above 100% is added under the line; below 100% the whole line shrinks, baseline included.
    line = min(advance, GSLIDES_LINE * size)
    return baseline - GSLIDES_BASELINE / GSLIDES_LINE * line, advance / GSLIDES_LINE


def add_text(slide, el, slide_pt, target):
    """One text box per block, with the draft's own line breaks, placed so the first baseline matches."""
    top, exact = text_placement(el, target)
    spacing = exact * slide_pt
    height = el["lineAdvance"] * len(el["lines"])
    left, width = slack_box(el)
    box = slide.shapes.add_textbox(emu(left), emu(top), emu(width), emu(height))
    frame = box.text_frame
    frame.word_wrap = False
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    para = frame.paragraphs[0]
    para.alignment = ALIGN[el["align"]]
    para.line_spacing = Emu(int(spacing * EMU_PER_PT))  # rounds down, so a spacing on a threshold stays on its side
    para.space_before = para.space_after = Pt(0)
    for i, line in enumerate(el["lines"]):
        if i:
            # A bare line break takes the theme's default size, which can be taller than the text and stretch the line.
            br = etree.SubElement(para._p, qn("a:br"))
            style_run(etree.SubElement(br, qn("a:rPr")), el["lines"][i - 1][-1], slide_pt)
        for run_spec in line:
            run = para.add_run()
            run.text = run_spec["text"]
            style_run(run._r.get_or_add_rPr(), run_spec, slide_pt)
    end = etree.SubElement(para._p, qn("a:endParaRPr"))
    style_run(end, el["lines"][-1][-1], slide_pt)


def slack_box(el):
    """Left edge and width of the text box: the block's own box, widened so no app re-wraps a full line.

    Lines already carry the draft's breaks. Apps measure text a hair differently, so a box exactly as wide as
    its longest line can wrap that line again. The box grows away from the side the text is anchored to.
    """
    size = max(run["size"] for line in el["lines"] for run in line)
    need = el["ink"]["w"] * 1.04 + 0.5 * size
    extra = max(0.0, need - el["w"])
    if el["align"] == "start":
        return el["x"], el["w"] + extra
    if el["align"] == "end":
        return el["x"] - extra, el["w"] + extra
    return el["x"] - extra / 2, el["w"] + extra


def style_run(r_pr, run_spec, slide_pt):
    """Write one run's font, size, weight and color onto an <a:rPr> or <a:endParaRPr>."""
    r_pr.set("sz", str(round(run_spec["size"] * slide_pt * 100)))
    r_pr.set("b", "1" if run_spec["weight"] >= 600 else "0")
    r_pr.set("i", "1" if run_spec["italic"] else "0")
    if run_spec["underline"]:
        r_pr.set("u", "sng")
    fill = etree.SubElement(r_pr, qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr")).set("val", run_spec["color"]["hex"][1:])
    set_alpha(fill, run_spec["color"]["alpha"])
    for tag in ("a:latin", "a:ea", "a:cs"):  # the same font for every script
        etree.SubElement(r_pr, qn(tag)).set("typeface", run_spec["font"])


def draw(slide, spec, spec_dir, slide_pt, target):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = RGBColor.from_string(spec["background"]["hex"][1:])
    for el in spec["elements"]:
        if el["type"] in ("rect", "ellipse"):
            add_box(slide, el)
        elif el["type"] == "line":
            add_line(slide, el, target)
        elif el["type"] == "text":
            add_text(slide, el, slide_pt, target)
        elif el["type"] == "image":
            slide.shapes.add_picture(str(Path(spec_dir) / el["src"]), emu(el["x"]), emu(el["y"]), emu(el["w"]), emu(el["h"]))
    if spec.get("notes"):
        slide.notes_slide.notes_text_frame.text = spec["notes"]


def clear(slide):
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)


def build(spec_dir, out, only=None, target="powerpoint"):
    """Write the deck. With `only`, redraw just those slides in an existing file and leave the rest untouched.

    target="gslides" writes a file tuned for import into Google Slides, which lays text out differently.
    """
    specs = load_specs(spec_dir, only)
    out = Path(out)
    if only and out.exists():
        prs = Presentation(str(out))
    else:
        prs = Presentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = Emu(round(SLIDE_WIDTH * specs[0][1]["aspect"]))
    slide_pt = prs.slide_width / EMU_PER_PT
    by_name = {slide.name: slide for slide in prs.slides}
    blank = min(prs.slide_layouts, key=lambda layout: len(layout.placeholders))
    for slide_id, spec in specs:
        slide = by_name.get(slide_id)
        if slide is None:
            slide = prs.slides.add_slide(blank)
            slide.name = slide_id
        clear(slide)
        draw(slide, spec, spec_dir, slide_pt, target)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return [slide_id for slide_id, _ in specs]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("specs", help="directory of shape specs from extract.py")
    ap.add_argument("--out", required=True, help="the .pptx to write")
    ap.add_argument("--only", nargs="+", metavar="SLIDE_ID", help="redraw only these slides in an existing deck")
    ap.add_argument("--target", choices=["powerpoint", "gslides"], default="powerpoint", help="the app the file is tuned for (build_gslides.py uses gslides)")
    args = ap.parse_args()
    built = build(args.specs, args.out, args.only, args.target)
    print(f"{args.out}: built {', '.join(built)}")


if __name__ == "__main__":
    main()
