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
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = json.loads((ROOT / "site" / "config.json").read_text(encoding="utf-8"))["site_url"]


def render(args: argparse.Namespace) -> tuple[Path, Path]:
    from playwright.sync_api import sync_playwright

    query = "?v=2&d=" + ",".join("k." + d for d in args.dishes.split(",")) + f"&lang={args.lang}" + ("&m=opposite" if args.opposite else "")
    if args.fly != "female":
        query += "&f=" + args.fly
    out = Path(args.out)
    phone = out.with_name(out.stem + "-phone" + out.suffix)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": args.width, "height": 844}, device_scale_factor=3)
        page = context.new_page()
        page.add_init_script('''
          window.__cardTextBounds=[];
          const original=CanvasRenderingContext2D.prototype.fillText;
          CanvasRenderingContext2D.prototype.fillText=function(text,x,y,...rest){
            if(this.canvas.id==='share-card') {
              const m=this.measureText(text);
              window.__cardTextBounds.push({text,y,bottom:y+m.actualBoundingBoxDescent,height:this.canvas.height});
            }
            return original.call(this,text,x,y,...rest);
          };
        ''')
        page.goto(args.url.rstrip("/") + "/" + query, wait_until="networkidle")
        page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
        page.wait_for_timeout(800)  # sprites are loaded by the scene before it starts
        page.click("#skip-btn")
        page.wait_for_selector("#result-panel:not([hidden])", timeout=20000)
        page.click("#share-btn")
        page.wait_for_selector("#card-dialog[open]", timeout=20000)
        page.wait_for_timeout(500)
        overflow=page.evaluate('window.__cardTextBounds.filter(b=>b.y<0 || b.bottom>b.height)')
        assert not overflow, f'Share-card text outside canvas: {overflow}'
        data_url = page.evaluate("document.getElementById('share-card').toDataURL('image/png')")
        out.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
        page.screenshot(path=str(phone))  # the modal as the phone shows it
        browser.close()
    return out, phone


def decode_qr(png: Path) -> str | None:
    try:
        import cv2
    except ImportError:
        return None
    image = cv2.imread(str(png))
    detector = cv2.QRCodeDetector()
    text, _points, _ = detector.detectAndDecode(image)
    if not text:
        # The detector sometimes locks onto the dark brain snapshot; the QR sits
        # in the bottom-right quadrant, so try that crop on its own.
        h, w = image.shape[:2]
        text, _points, _ = detector.detectAndDecode(image[h // 2:, w // 2:])
    return text or ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://127.0.0.1:8765/", help="site origin (a local static server on site/)")
    parser.add_argument("--dishes", default="teriyaki-chicken,sour-plum-drink,hot-and-sour-noodles,lemon", help="comma-separated slugs, as in ?d=")
    parser.add_argument("--lang", choices=("zh", "en"), default="zh")
    parser.add_argument("--fly", choices=("female", "male", "both"), default="female")
    parser.add_argument("--opposite", action="store_true", help="replay 'Do the opposite' instead of 'Ask the fly'")
    parser.add_argument("--width", type=int, default=390, help="viewport width in CSS px for the phone screenshot")
    parser.add_argument("--out", default=str(ROOT / "docs" / "media" / "share-card-sample.png"))
    args = parser.parse_args()

    out, phone = render(args)
    print(f"card: {out}\nphone view: {phone}")
    # Legacy input links use the deterministic presentation seed 0 in v1.2.
    expected = f"{SITE_URL}?v=2&d=" + ",".join("k." + d for d in args.dishes.split(",")) + f"&lang={args.lang}" + ("&m=opposite" if args.opposite else "") + "&seed=0"
    if args.fly != "female":
        expected += "&f=" + args.fly
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
