"""Compare a built slide's render with the draft's reference render, element by element."""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

from spec_io import load_specs, text_of

MARGIN = 0.012  # search this far (fraction of slide width) around where each element should be


def ink_box(image, background, region, threshold=48):
    """Bounding box (fractions of slide width) of pixels that differ from the background inside region."""
    width = image.size[0]
    x0, y0, x1, y1 = (max(0, round(v * width)) for v in region)
    crop = image.crop((x0, y0, min(x1, width), min(y1, image.size[1])))
    diff = ImageChops.difference(crop, Image.new("RGB", crop.size, background)).convert("L").point(lambda v: 255 if v > threshold else 0)
    box = diff.getbbox()
    if not box:
        return None
    return [(x0 + box[0]) / width, (y0 + box[1]) / width, (x0 + box[2]) / width, (y0 + box[3]) / width]


def local_background(image, region):
    """The most common color in the region: the fill the text sits on."""
    width = image.size[0]
    x0, y0, x1, y1 = (max(0, round(v * width)) for v in region)
    crop = image.crop((x0, y0, min(x1, width), min(y1, image.size[1]))).resize((64, 32))
    return max(crop.getcolors(64 * 32), key=lambda c: c[0])[1]


def compare_slide(spec, reference, built):
    """Yield (label, dx, dy, dw, dh) for every text block: how far the built ink sits from the draft's ink."""
    reference = reference.convert("RGB")
    built = built.convert("RGB").resize(reference.size, Image.LANCZOS)
    for el in spec["elements"]:
        if el["type"] != "text":
            continue
        region = (el["ink"]["x"] - MARGIN, el["y"] - MARGIN, el["ink"]["x"] + el["ink"]["w"] + MARGIN, el["y"] + el["h"] + MARGIN)
        a = ink_box(reference, local_background(reference, region), region)
        b = ink_box(built, local_background(built, region), region)
        label = " / ".join(text_of(el))[:40]
        if not a or not b:
            yield label, None
            continue
        yield label, (b[0] - a[0], b[1] - a[1], (b[2] - b[0]) - (a[2] - a[0]), (b[3] - b[1]) - (a[3] - a[1]))


def pixel_difference(reference, built):
    """Share of pixels that clearly differ, after scaling the built render to the reference."""
    reference = reference.convert("RGB")
    built = built.convert("RGB").resize(reference.size, Image.LANCZOS)
    diff = ImageChops.difference(reference, built).convert("L").point(lambda v: 255 if v > 64 else 0)
    return diff.histogram()[255] / (reference.size[0] * reference.size[1]), diff


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("specs", help="spec directory (holds <id>.json and the reference <id>.png)")
    ap.add_argument("built", help="directory of built renders named <id>.png")
    ap.add_argument("--tolerance", type=float, default=0.002, help="largest text shift allowed, as a fraction of slide width")
    ap.add_argument("--diff", help="directory to write side by side comparison images into")
    ap.add_argument("--json", action="store_true", help="print machine readable results")
    args = ap.parse_args()
    failed = False
    report = {}
    for slide_id, spec in load_specs(args.specs):
        built_path = Path(args.built) / f"{slide_id}.png"
        if not built_path.exists():
            print(f"{slide_id}: no built render")
            failed = True
            continue
        reference, built = Image.open(Path(args.specs) / f"{slide_id}.png"), Image.open(built_path)
        share, diff = pixel_difference(reference, built)
        rows = list(compare_slide(spec, reference, built))
        report[slide_id] = {"pixels": share, "text": rows}
        worst = max((max(abs(v) for v in d) for _, d in rows if d), default=0)
        missing = [label for label, d in rows if d is None]
        ok = worst <= args.tolerance and not missing
        failed |= not ok
        print(f"{'ok  ' if ok else 'FAIL'} {slide_id}: worst text shift {worst * 100:.2f}% of slide width, {share * 100:.2f}% of pixels differ")
        for label, d in rows:
            if d is None:
                print(f"    missing text: {label}")
            elif max(abs(v) for v in d) > args.tolerance:
                print(f"    dx {d[0] * 100:+.2f} dy {d[1] * 100:+.2f} dw {d[2] * 100:+.2f} dh {d[3] * 100:+.2f}  {label}")
        if args.diff:
            Path(args.diff).mkdir(parents=True, exist_ok=True)
            ref = reference.convert("RGB")
            w, h = ref.size
            sheet = Image.new("RGB", (w, h * 3), "white")
            sheet.paste(ref, (0, 0))
            sheet.paste(built.convert("RGB").resize(ref.size, Image.LANCZOS), (0, h))
            sheet.paste(diff.convert("RGB"), (0, h * 2))
            sheet.resize((w // 2, h * 3 // 2)).save(Path(args.diff) / f"{slide_id}.png")
    if args.json:
        print(json.dumps(report))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
