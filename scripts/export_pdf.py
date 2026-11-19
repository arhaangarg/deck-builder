"""Export locked slides straight to a vector PDF, one slide per page, exactly as the drafts render."""
import argparse
from pathlib import Path

import pymupdf
from playwright.sync_api import sync_playwright

PAGE_WIDTH_IN = 13.333


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", nargs="+", help="locked slide files, in deck order")
    ap.add_argument("--out", required=True, help="the .pdf to write")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        pages = []
        merged = pymupdf.open()
        for path in args.html:
            page.goto(Path(path).resolve().as_uri())
            page.wait_for_load_state("networkidle")
            page.evaluate("document.fonts.ready")
            count = page.locator(".slide").count()
            for i in range(count):
                aspect = page.evaluate(
                    """i => {
                        const slides = [...document.querySelectorAll('.slide')];
                        const r = slides[i].getBoundingClientRect();
                        slides.forEach((s, k) => { s.style.display = k === i ? '' : 'none'; });
                        document.documentElement.style.cssText = 'margin:0;padding:0';
                        document.body.style.cssText = 'margin:0;padding:0';
                        slides[i].style.width = '100vw';
                        slides[i].style.margin = '0';
                        return r.height / r.width;
                    }""", i)
                pdf = page.pdf(width=f"{PAGE_WIDTH_IN}in", height=f"{PAGE_WIDTH_IN * aspect}in", print_background=True,
                               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
                with pymupdf.open(stream=pdf, filetype="pdf") as one:
                    merged.insert_pdf(one, from_page=0, to_page=0)
                pages.append(path)
                page.reload()
                page.wait_for_load_state("networkidle")
        merged.save(str(out))
        browser.close()
    print(f"{out}: {len(pages)} pages")


if __name__ == "__main__":
    main()
