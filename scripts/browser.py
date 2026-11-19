"""Open draft pages in headless Chromium with slide_dom.js loaded."""
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
RENDER_WIDTH = 1600  # px; only sets measuring precision, since every spec length is a fraction of slide width


@contextmanager
def open_page(html_path, width=RENDER_WIDTH):
    """Yield a page showing html_path, with fonts loaded and window.deckBuilder ready."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1000}, device_scale_factor=2)
        page.goto(Path(html_path).resolve().as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        page.add_script_tag(path=str(HERE / "slide_dom.js"))
        try:
            yield page
        finally:
            browser.close()


def slide_count(page):
    return page.evaluate("window.deckBuilder.slides().length")
