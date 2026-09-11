#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Turn raw 1024x1024 PNGs into the site's pixel sprites.

Dishes: assets/raw/<key-slug>.png -> site/assets/dishes/<key-slug>.png (96x96, RGBA)
Fly:    assets/raw/fly/<state>_<n>.png (or a sheet) -> site/assets/fly/<state>_<n>.png (48x48)

Steps per image: remove the background (flood fill from the corners on near-background
colour, or use an existing alpha channel), crop to content, downsample with
nearest-neighbour, quantize to ONE shared 32-colour palette (learned from all inputs
of the batch, so every sprite reads as the same set), write RGBA PNG.
See docs/assets.md for the expected filenames.
"""

from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "assets" / "raw"
OUT_DISHES = ROOT / "site" / "assets" / "dishes"
OUT_FLY = ROOT / "site" / "assets" / "fly"
FLY_FRAMES = {"idle": 2, "fly": 4, "land": 1, "proboscis": 3}
PALETTE_SIZE = 32


def remove_background(image: Image.Image, tolerance: int) -> Image.Image:
    """Make the background transparent.

    If the image already has meaningful alpha, keep it. Otherwise flood-fill from the
    four corners: every pixel connected to a corner whose colour is within
    ``tolerance`` (per channel) of that corner's colour becomes transparent.
    """
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if alpha.getextrema()[0] < 255:
        return rgba
    width, height = rgba.size
    pixels = rgba.load()
    mask = [[False] * width for _ in range(height)]
    for corner in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        base = pixels[corner][:3]
        queue = deque([corner])
        while queue:
            x, y = queue.popleft()
            if mask[y][x]:
                continue
            r, g, b, _ = pixels[x, y]
            if max(abs(r - base[0]), abs(g - base[1]), abs(b - base[2])) > tolerance:
                continue
            mask[y][x] = True
            if x > 0:
                queue.append((x - 1, y))
            if x < width - 1:
                queue.append((x + 1, y))
            if y > 0:
                queue.append((x, y - 1))
            if y < height - 1:
                queue.append((x, y + 1))
    for y in range(height):
        row = mask[y]
        for x in range(width):
            if row[x]:
                r, g, b, _ = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)
    return rgba


def crop_and_square(image: Image.Image, margin: float) -> Image.Image:
    box = image.getchannel("A").getbbox()
    if box:
        image = image.crop(box)
    side = int(max(image.size) * (1.0 + 2.0 * margin)) or 1
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def downsample(image: Image.Image, size: int) -> Image.Image:
    return image.resize((size, size), Image.Resampling.NEAREST)


def shared_palette(images: list[Image.Image], colours: int) -> Image.Image:
    """Learn one palette from the opaque pixels of every sprite in the batch."""
    opaque = []
    for image in images:
        rgb = image.convert("RGB")
        alpha = image.getchannel("A")
        opaque.append(Image.composite(rgb, Image.new("RGB", image.size, (0, 0, 0)), alpha.point(lambda a: 255 if a > 127 else 0)))
    if not opaque:
        raise ValueError("no images to build a palette from")
    width = sum(img.width for img in opaque)
    strip = Image.new("RGB", (width, max(img.height for img in opaque)))
    x = 0
    for img in opaque:
        strip.paste(img, (x, 0))
        x += img.width
    return strip.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def apply_palette(image: Image.Image, palette: Image.Image) -> Image.Image:
    rgb = image.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE).convert("RGB")
    alpha = image.getchannel("A").point(lambda a: 255 if a > 127 else 0)
    rgb.putalpha(alpha)
    return rgb


def prepare(paths: list[Path], size: int, out_dir: Path, tolerance: int, margin: float) -> list[Path]:
    prepared = []
    for path in paths:
        image = Image.open(path)
        image = remove_background(image, tolerance)
        image = crop_and_square(image, margin)
        prepared.append(downsample(image, size))
    palette = shared_palette(prepared, PALETTE_SIZE)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for path, image in zip(paths, prepared):
        target = out_dir / (path.stem.lower() + ".png")
        apply_palette(image, palette).save(target, optimize=True)
        written.append(target)
    return written


def split_sheet(sheet: Path, frame: int) -> list[Path]:
    """Cut a horizontal sprite sheet <state>_sheet.png into <state>_<n>.png files next to it."""
    image = Image.open(sheet).convert("RGBA")
    state = sheet.stem.removesuffix("_sheet")
    count = FLY_FRAMES.get(state)
    if count is None:
        raise ValueError(f"unknown fly state {state!r}; expected one of {sorted(FLY_FRAMES)}")
    width = image.width // count
    outputs = []
    for index in range(count):
        frame_image = image.crop((index * width, 0, (index + 1) * width, image.height))
        target = sheet.with_name(f"{state}_{index + 1}.png")
        frame_image.save(target)
        outputs.append(target)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW_DIR)
    parser.add_argument("--dish-size", type=int, default=96)
    parser.add_argument("--fly-size", type=int, default=48)
    parser.add_argument("--tolerance", type=int, default=24, help="background flood-fill tolerance per channel")
    parser.add_argument("--margin", type=float, default=0.04, help="transparent margin around the content")
    parser.add_argument("--only", choices=("dishes", "fly"))
    args = parser.parse_args()

    if args.only in (None, "dishes"):
        dish_paths = sorted(p for p in args.raw.glob("*.png"))
        if dish_paths:
            written = prepare(dish_paths, args.dish_size, OUT_DISHES, args.tolerance, args.margin)
            print(f"dishes: wrote {len(written)} sprites to {OUT_DISHES}")
        else:
            print(f"dishes: no PNGs in {args.raw}")

    if args.only in (None, "fly"):
        fly_dir = args.raw / "fly"
        if fly_dir.is_dir():
            for sheet in sorted(fly_dir.glob("*_sheet.png")):
                split_sheet(sheet, args.fly_size)
            frames = sorted(p for p in fly_dir.glob("*.png") if not p.stem.endswith("_sheet"))
            expected = {f"{state}_{n}" for state, count in FLY_FRAMES.items() for n in range(1, count + 1)}
            missing = sorted(expected - {p.stem for p in frames})
            if missing:
                print(f"fly: missing frames {missing}", file=sys.stderr)
            if frames:
                written = prepare(frames, args.fly_size, OUT_FLY, args.tolerance, 0.0)
                print(f"fly: wrote {len(written)} frames to {OUT_FLY}")
        else:
            print(f"fly: no {fly_dir} directory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
