#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Measure replay load time and brain-view frame timing with Playwright on a phone viewport.

Runs the three-dish sequence against a served copy of site/ (default: the LAN server
http://192.168.1.160:8765/), samples requestAnimationFrame intervals while the brain
view plays, and reports the replay fetch time, dropped frames (interval > 34 ms) and the
worst interval. Also plays the heaviest replay cell directly through the BrainView.
"""

from __future__ import annotations

import argparse
import json
import statistics

from playwright.sync_api import sync_playwright

PROBE = """
window.__frames = [];
window.__armed = false;
(function loop(now) {
  if (window.__armed) window.__frames.push(now);
  requestAnimationFrame(loop);
})(performance.now());
"""


def summarize(frames: list[float]) -> dict:
    gaps = [b - a for a, b in zip(frames, frames[1:])]
    if not gaps:
        return {"frames": 0}
    return {
        "frames": len(frames),
        "median_ms": round(statistics.median(gaps), 1),
        "p95_ms": round(sorted(gaps)[int(len(gaps) * 0.95)], 1),
        "max_ms": round(max(gaps), 1),
        "dropped_over_34ms": sum(g > 34 for g in gaps),
        "seconds": round((frames[-1] - frames[0]) / 1000, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://192.168.1.160:8765/")
    parser.add_argument("--dishes", default="honey,black coffee,water")
    parser.add_argument("--device", default="iPhone 13")
    parser.add_argument("--speed", default="1")
    parser.add_argument("--heavy-cell", default="G_slow_blow_whigh_ihigh")
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        device = p.devices[args.device]
        context = browser.new_context(**device)
        page = context.new_page()
        page.add_init_script(PROBE)
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_function("document.getElementById('ask-btn') && !document.getElementById('ask-btn').disabled || true")
        page.wait_for_timeout(500)
        for dish in [d.strip() for d in args.dishes.split(",") if d.strip()]:
            page.fill("#option-input", dish)
            page.click(".btn-add")
        page.evaluate("(v) => { document.getElementById('speed').value = v; }", args.speed)
        page.evaluate("window.__armed = true")
        page.click("#ask-btn")
        page.wait_for_function("!document.getElementById('result-panel').hidden", timeout=120000)
        page.evaluate("window.__armed = false")
        frames = page.evaluate("window.__frames")
        resources = page.evaluate("""performance.getEntriesByType('resource')
            .filter(e => e.name.includes('/data/replay/') || e.name.includes('neurons.json'))
            .map(e => ({name: e.name.split('/').pop(), ms: Math.round(e.duration), kb: Math.round((e.transferSize || e.encodedBodySize || 0) / 1024)}))""")
        sequence = summarize(frames)

        # Heaviest cell, played directly through the brain view.
        heavy = page.evaluate("""async (cellId) => {
            const brain = await import('./brain.js');
            const canvas = document.getElementById('brain-canvas');
            const neurons = brain.decodeNeurons(await (await fetch('data/neurons.json')).json());
            const view = new brain.BrainView(canvas, neurons);
            const t0 = performance.now();
            const replay = await brain.makeReplayLoader('data/replay/')(cellId);
            const fetchMs = performance.now() - t0;
            view.setReplay(replay);
            window.__frames = []; window.__armed = true;
            await view.play(1);
            window.__armed = false;
            return {fetchMs: Math.round(fetchMs), nSpikes: replay.header.n_spikes, frames: window.__frames};
        }""", args.heavy_cell)
        heavy_summary = summarize(heavy.pop("frames"))
        browser.close()

    report = {
        "device": args.device, "url": args.url, "dishes": args.dishes, "speed": args.speed,
        "sequence_frames": sequence, "resources": resources,
        "heavy_cell": {"cell": args.heavy_cell, **heavy, **heavy_summary},
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
