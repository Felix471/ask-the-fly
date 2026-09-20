#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check the longest plate names in Chromium and save the six viewport screenshots.

Run against the local site server. --baseline records the original canvas labels
and exits nonzero when their painted bounds overlap. A normal run checks full DOM
labels/titles, clipping, language changes, resize and reset, without changing data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FONT = "600 13px system-ui, -apple-system, 'Segoe UI', 'PingFang SC', 'Noto Sans CJK SC', sans-serif"
INIT = """() => {
  window.__platePaint = {};
  const original = CanvasRenderingContext2D.prototype.fillText;
  CanvasRenderingContext2D.prototype.fillText = function(text, x, y, ...rest) {
    if (this.canvas.id === 'scene-canvas') {
      const m = this.measureText(text), t = this.getTransform();
      const rect = this.canvas.getBoundingClientRect();
      const sx = this.canvas.clientWidth / this.canvas.width;
      const sy = this.canvas.clientHeight / this.canvas.height;
      window.__platePaint[text] = {
        left: rect.left + this.canvas.clientLeft + (t.a * (x - m.width / 2) + t.e) * sx,
        top: rect.top + this.canvas.clientTop + (t.d * (y - m.actualBoundingBoxAscent) + t.f) * sy,
        width: m.width * t.a * sx,
        height: (m.actualBoundingBoxAscent + m.actualBoundingBoxDescent) * t.d * sy
      };
    }
    return original.call(this, text, x, y, ...rest);
  };
}"""


def intersect(a, b):
    return (min(a["left"] + a["width"], b["left"] + b["width"]) > max(a["left"], b["left"])
            and min(a["top"] + a["height"], b["top"] + b["height"]) > max(a["top"], b["top"]))


def inspect_labels(page, names):
    return page.evaluate("""names => {
      const canvas = document.querySelector('#scene-canvas');
      const labels = [...document.querySelectorAll('.plate-label')];
      return {
        height: canvas.getBoundingClientRect().height,
        labels: labels.map(el => {
          const name = el.querySelector('.plate-name') || el;
          const badge = el.querySelector('.not-food-badge');
          const r = name.getBoundingClientRect(), s = getComputedStyle(name);
          const outer = el.getBoundingClientRect();
          return {text: name.textContent, title: el.title, left: r.left, top: r.top,
            width: r.width, height: r.height, clipped: name.scrollWidth > name.clientWidth,
            outer: {left:outer.left,top:outer.top,width:outer.width,height:outer.height},
            badge: badge?.textContent || '', badgeFits: !badge || (badge.scrollWidth <= badge.clientWidth && badge.getBoundingClientRect().bottom <= outer.bottom),
            overflow: s.overflow, textOverflow: s.textOverflow, whiteSpace: s.whiteSpace};
        }),
        paint: names.map(name => window.__platePaint[name] || null)
      };
    }""", names)


def assert_labels(state, names):
    labels = state["labels"]
    assert [item["text"] for item in labels] == names, "display names changed or missing"
    assert [item["title"] for item in labels] == [name + (' — ' + item['badge'] if item['badge'] else '')
                                                for name, item in zip(names, labels)], "full-name titles changed or missing"
    assert all(item["overflow"] == "hidden" and item["textOverflow"] == "ellipsis"
               and item["whiteSpace"] == "nowrap" for item in labels), "labels are not clipped"
    assert len({item["height"] for item in labels}) == 1, "label row heights differ"
    assert not any(intersect(a, b) for i, a in enumerate(labels) for b in labels[i + 1:]), "label boxes overlap"
    assert all(item['badgeFits'] for item in labels), 'not-food badge clipped'
    assert not any(intersect(a['outer'], b['outer']) for i, a in enumerate(labels) for b in labels[i + 1:]), 'caption boxes overlap'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8765/")
    parser.add_argument("--out", type=Path, default=ROOT / "results/plate-labels/after")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--compare", type=Path, help="baseline report.json for scene-height comparison")
    parser.add_argument("--dishes", help="comma-separated keys to check instead of the automatically selected longest names")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    dishes = json.loads((ROOT / "data/dishes.json").read_text(encoding="utf-8"))
    before = json.loads(args.compare.read_text(encoding="utf-8")) if args.compare else {}
    report, failures = {}, []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        measure_page = browser.new_page()
        for lang in ("en", "zh"):
            widths = measure_page.evaluate("""({names, font}) => {
              const ctx = document.createElement('canvas').getContext('2d'); ctx.font = font;
              return names.map(name => ctx.measureText(name).width);
            }""", {"names": [d["display"][lang] for d in dishes], "font": FONT})
            ranked = sorted(zip(dishes, widths), key=lambda pair: (-len(pair[0]["display"][lang]), -pair[1], pair[0]["key"]))
            by_key = {d['key']: d for d in dishes}
            selected = [by_key[key] for key in args.dishes.split(',')] if args.dishes else [d for d, _ in ranked[:3]]
            names = [d["display"][lang] for d in selected]
            print(f"{lang} longest: " + json.dumps(names, ensure_ascii=False), flush=True)
            for width in (360, 390, 430):
                key = f"{lang}-{width}"
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.add_init_script(f"({INIT})()")
                errors = []
                external = []
                origin = urlsplit(args.base).netloc
                page.on("request", lambda request: external.append(request.url)
                        if urlsplit(request.url).netloc not in ("", origin) else None)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                query = urlencode({"d": ",".join(d["key"] for d in selected), "lang": lang}, safe=",")
                page.goto(args.base.rstrip("/") + "/?" + query, wait_until="domcontentloaded")
                try:
                    page.locator("#scene-panel").wait_for(state="visible", timeout=20000)
                    assert page.evaluate("window.__askfly.snapshot().phase") == "tasting"
                except Exception:
                    print(page.evaluate("({state: window.__askfly?.snapshot(), text: document.body.innerText})"), flush=True)
                    print(errors, flush=True)
                    raise
                page.locator("#scene-canvas").scroll_into_view_if_needed()
                page.evaluate("document.fonts.ready")
                initial = inspect_labels(page, names)
                if not args.baseline:
                    assert_labels(initial, names)
                page.click("#skip-btn")
                page.locator("#result-panel").wait_for(state="visible")
                assert page.evaluate("window.__askfly.snapshot().phase") == "result"
                scene = page.locator(".scene-stage" if page.locator(".scene-stage").count() else "#scene-canvas")
                scene.screenshot(path=str(args.out / f"{key}.png"))
                state = inspect_labels(page, names)
                state["names"] = names
                state["keys"] = [d["key"] for d in selected]
                report[key] = state
                if args.baseline:
                    assert all(state["paint"]), "original labels were not painted"
                    overlap = any(intersect(a, b) for i, a in enumerate(state["paint"]) for b in state["paint"][i + 1:])
                    state["overlap"] = overlap
                    if overlap:
                        failures.append(key)
                    print(f"{key}: overlap={overlap}, scene_height={state['height']}", flush=True)
                else:
                    assert_labels(state, names)
                    assert state["height"] == initial["height"], "skip changed scene height"
                    if before:
                        assert state["height"] == before[key]["height"], "scene height changed from baseline"
                    page.click("#lang-toggle")
                    other_names = [d["display"]["zh" if lang == "en" else "en"] for d in selected]
                    assert_labels(inspect_labels(page, other_names), other_names)
                    assert inspect_labels(page, other_names)["height"] == state["height"], "language changed scene height"
                    if width == 430:
                        page.set_viewport_size({"width": 360, "height": 900})
                        assert_labels(inspect_labels(page, other_names), other_names)
                    page.click("#again-btn")
                    assert page.locator("#scene-panel").is_hidden(), "reset did not hide labels"
                    page.click("#ask-btn")
                    page.locator("#scene-panel").wait_for(state="visible")
                    assert page.evaluate("window.__askfly.snapshot().phase") == "tasting"
                    assert_labels(inspect_labels(page, other_names), other_names)
                    print(f"{key}: PASS, scene_height={state['height']}, clipped={[x['clipped'] for x in state['labels']]}", flush=True)
                assert not errors, errors
                assert not external, f"third-party requests: {external}"
                page.close()
        browser.close()
    (args.out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        print("Reproduced overlapping labels: " + ", ".join(failures), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
