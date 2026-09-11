#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render a share card headless with Playwright from a share link, and check its QR code.

Loads the site with ?d=…&lang=… (the same link the card's QR encodes), skips the
animation, opens the card, saves the 900 x 1200 PNG the "Save image" button would,
and a phone-width screenshot of the card as displayed. With OpenCV installed the QR
is decoded from the PNG and compared with the expected link.

  .venv\\Scripts\\python scripts/export_share_card.py --dishes teriyaki-chicken,sour-plum-drink,hot-and-sour-noodles,lemon --lang zh
  .venv\\Scripts\\python scripts/export_share_card.py --url http://127.0.0.1:8765/ --out out/card.png
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://felix471.github.io/ask-the-fly/"


def render(args: argparse.Namespace) -> tuple[Path, Path]:
    from playwright.sync_api import sync_playwright

    query = f"?d={args.dishes}&lang={args.lang}" + ("&m=opposite" if args.opposite else "")
    out = Path(args.out)
    phone = out.with_name(out.stem + "-phone" + out.suffix)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": args.width, "height": 844}, device_scale_factor=3)
        page = context.new_page()
        page.goto(args.url.rstrip("/") + "/" + query, wait_until="networkidle")
        page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
        page.wait_for_timeout(800)  # sprites are loaded by the scene before it starts
        page.click("#skip-btn")
        page.wait_for_selector("#result-panel:not([hidden])", timeout=20000)
        page.click("#share-btn")
        page.wait_for_selector("#card-panel:not([hidden])", timeout=20000)
        page.wait_for_timeout(500)
        data_url = page.evaluate("document.getElementById('share-card').toDataURL('image/png')")
        out.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
        page.locator("#card-panel").screenshot(path=str(phone))
        browser.close()
    return out, phone


def decode_qr(png: Path) -> str | None:
    try:
        import cv2
    except ImportError:
        return None
    image = cv2.imread(str(png))
    text, _points, _ = cv2.QRCodeDetector().detectAndDecode(image)
    return text or ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://127.0.0.1:8765/", help="site origin (a local static server on site/)")
    parser.add_argument("--dishes", default="teriyaki-chicken,sour-plum-drink,hot-and-sour-noodles,lemon", help="comma-separated slugs, as in ?d=")
    parser.add_argument("--lang", choices=("zh", "en"), default="zh")
    parser.add_argument("--opposite", action="store_true", help="replay 'Do the opposite' instead of 'Ask the fly'")
    parser.add_argument("--width", type=int, default=390, help="viewport width in CSS px for the phone screenshot")
    parser.add_argument("--out", default=str(ROOT / "docs" / "media" / "share-card-sample.png"))
    args = parser.parse_args()

    out, phone = render(args)
    print(f"card: {out}\nphone view: {phone}")
    expected = f"{SITE_URL}?d={args.dishes}&lang={args.lang}" + ("&m=opposite" if args.opposite else "")
    decoded = decode_qr(out)
    if decoded is None:
        print("QR not checked (pip install opencv-python-headless to decode)")
        return 0
    if decoded == expected:
        print(f"QR decodes to the expected link: {decoded}")
        return 0
    print(f"QR MISMATCH\n  decoded:  {decoded!r}\n  expected: {expected!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
