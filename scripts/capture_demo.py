#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Capture the fly sequence headless with Playwright and write an MP4 and a GIF.

Frames are screenshotted at a fixed rate while the sequence runs (the page's own
animation is real time), then encoded with the ffmpeg bundled in imageio-ffmpeg.

  .venv\\Scripts\\python scripts/capture_demo.py --dishes "watermelon,black coffee,mapo tofu" --lang zh
  .venv\\Scripts\\python scripts/capture_demo.py --url http://localhost:8765/ --speed 2 --seconds 12
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "media"


def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def capture(args: argparse.Namespace, frames_dir: Path) -> int:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": args.width, "height": args.height}, device_scale_factor=args.scale)
        page = context.new_page()
        page.add_init_script(f"try {{ localStorage.setItem('askfly.lang', '{args.lang}'); }} catch (e) {{}}")
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_timeout(600)
        for dish in [d.strip() for d in args.dishes.split(",") if d.strip()]:
            page.fill("#option-input", dish)
            page.click(".btn-add")
        page.evaluate("(v) => { document.getElementById('speed').value = v; }", str(args.speed))
        page.click("#opposite-btn" if args.opposite else "#ask-btn")
        # Keep the scene panel at the top of the frame.
        page.evaluate("document.getElementById('scene-panel').scrollIntoView({block: 'start'})")
        interval = 1.0 / args.fps
        t_start = time.perf_counter()
        deadline = t_start + args.seconds
        count = 0
        while time.perf_counter() < deadline:
            started = time.perf_counter()
            page.screenshot(path=str(frames_dir / f"f{count:05d}.png"), clip={"x": 0, "y": 0, "width": args.width, "height": args.height})
            count += 1
            done = page.evaluate("!document.getElementById('result-panel').hidden")
            if done and args.stop_when_done and time.perf_counter() > deadline - args.tail:
                break
            remaining = interval - (time.perf_counter() - started)
            if remaining > 0:
                time.sleep(remaining)
        elapsed = time.perf_counter() - t_start
        browser.close()
    # Screenshots take longer than one frame interval, so encode at the rate
    # actually achieved to keep the clip in real time.
    return count, count / max(elapsed, 1e-6)


def encode(frames_dir: Path, fps: float, mp4: Path, gif: Path, width: int) -> None:
    exe = ffmpeg_exe()
    pattern = str(frames_dir / "f%05d.png")
    subprocess.run([exe, "-y", "-loglevel", "error", "-framerate", f"{fps:.3f}", "-i", pattern,
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(mp4)], check=True)
    palette = frames_dir / "palette.png"
    gif_scale = f"fps={min(int(fps), 15)},scale={min(width, 480)}:-1:flags=lanczos"
    subprocess.run([exe, "-y", "-loglevel", "error", "-framerate", f"{fps:.3f}", "-i", pattern,
                    "-vf", f"{gif_scale},palettegen=max_colors=128", str(palette)], check=True)
    subprocess.run([exe, "-y", "-loglevel", "error", "-framerate", f"{fps:.3f}", "-i", pattern, "-i", str(palette),
                    "-lavfi", f"{gif_scale} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3", str(gif)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8765/")
    parser.add_argument("--dishes", default="watermelon,black coffee,mapo tofu")
    parser.add_argument("--lang", choices=("en", "zh"), default="en")
    parser.add_argument("--opposite", action="store_true")
    parser.add_argument("--speed", default="1")
    parser.add_argument("--seconds", type=float, default=13.0, help="capture length (10-15 s)")
    parser.add_argument("--tail", type=float, default=2.0, help="seconds to keep after the result appears")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=430)
    parser.add_argument("--height", type=int, default=760)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--stop-when-done", action="store_true")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--name", default="demo")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="askfly-frames-") as tmp:
        frames_dir = Path(tmp)
        count, achieved_fps = capture(args, frames_dir)
        mp4 = args.out / f"{args.name}-{args.lang}.mp4"
        gif = args.out / f"{args.name}-{args.lang}.gif"
        encode(frames_dir, achieved_fps, mp4, gif, args.width * args.scale)
    print(f"{count} frames at {achieved_fps:.1f} fps ({count / achieved_fps:.1f} s) -> {mp4} ({mp4.stat().st_size / 1024:.0f} KB), {gif} ({gif.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
