"""Render a .pptx to one PNG per slide with a real office suite, so verify.py can compare it with the drafts."""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# PowerPoint for Mac is sandboxed: it reads and writes this folder without asking the user for access.
OFFICE_HOME = Path.home() / "Library/Group Containers/UBF8T346G9.Office"
POWERPOINT = Path("/Applications/Microsoft PowerPoint.app")


def pdf_with_powerpoint(pptx, pdf):
    work = OFFICE_HOME / "deck-builder"
    work.mkdir(exist_ok=True)
    src, dst = work / "render.pptx", work / "render.pdf"
    shutil.copy(pptx, src)
    dst.unlink(missing_ok=True)
    script = f'''
    tell application "Microsoft PowerPoint"
      open POSIX file "{src}"
      save active presentation in (POSIX file "{dst}") as save as PDF
      close active presentation saving no
    end tell'''
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=120)
    shutil.move(dst, pdf)
    src.unlink()


def pdf_with_libreoffice(soffice, pptx, pdf):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(pptx)], check=True, capture_output=True, timeout=180)
        shutil.move(Path(tmp) / (Path(pptx).stem + ".pdf"), pdf)


def to_pdf(pptx, pdf):
    """Prefer PowerPoint, since it is what the audience will open the file with."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if sys.platform == "darwin" and POWERPOINT.exists() and OFFICE_HOME.exists():
        pdf_with_powerpoint(pptx, pdf)
    elif soffice:
        pdf_with_libreoffice(soffice, pptx, pdf)
    else:
        raise SystemExit("Rendering a .pptx needs PowerPoint (macOS) or LibreOffice. Install one, or open the file and check it by eye.")


def pdf_to_pngs(pdf, out_dir, names, width=3200):
    """Rasterize each PDF page."""
    import pymupdf
    doc = pymupdf.open(pdf)
    paths = []
    for page, name in zip(doc, names):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(width / page.rect.width, width / page.rect.width), alpha=False)
        path = Path(out_dir) / f"{name}.png"
        pix.save(path)
        paths.append(path)
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pptx")
    ap.add_argument("--out", required=True, help="directory for the PNGs")
    args = ap.parse_args()
    from pptx import Presentation
    names = [slide.name for slide in Presentation(args.pptx).slides]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / "deck.pdf"
    to_pdf(Path(args.pptx).resolve(), pdf)
    for path in pdf_to_pngs(pdf, out, names):
        print(path)


if __name__ == "__main__":
    main()
