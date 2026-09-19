#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build deterministic DP4 candidates; promotion requires explicit --promote.

Run with .venv\\Scripts\\python scripts/prep_male_sprites.py.
The spec's assets/ paths are browser-relative: inputs live in site/assets/.
Native canvases are 48px (fly/response) and 64px (inset), not display sizes.

Segmentation heuristic (all thresholds are design choices, not anatomy labels):
* Visible pixels have alpha > 0. Pale wing seeds have HSV saturation <= .48,
  value >= .32. Keep seed components of >= 4 pixels, fill their enclosed holes,
  and expand one pixel to protect the dark wing outline. Translucent pixels
  (alpha < 200) are also protected. Wing pixels are never recoloured.
* Remove those wings, open the remaining silhouette with a 3x3 ellipse to
  remove thin legs/antennae, and take the largest connected core. PCA on that
  core estimates the axis; reject eigenvalue ratios < 1.25.
* The largest red-eye component (hue < 16 degrees, saturation > .70, value
  > .35) orients the axis toward its centroid, excluding isolated reddish
  leg/body pixels and the smaller proboscis component. Require >= 3 eye
  pixels and separation from the
  core centre >= 15% of its axial span. No filename-based left/right guess.
* The rear third of the core's axial extent, including a one-pixel body rim,
  receives RGB * .35 (therefore luminance * .35), with alpha unchanged.
  This is a silhouette proxy for the requested posterior abdomen marking.
* Insets are cropped head/mouth views: no abdomen or whole-body axis is
  visible. Flag them for manual review and omit tip darkening, rather than
  accidentally blackening their head. Palette/size transforms still apply.

Cool uses HSV hue -8 degrees, saturation * .85, value * .88 on non-wing
visible pixels, then tip darkening. tip_small resizes the complete tip canvas
to round(90%) with nearest neighbour and centres it in the original canvas.
Ambiguous full-body frames likewise omit tip darkening and are reported.
"""

from __future__ import annotations

import csv
import argparse
import hashlib
import io
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "site" / "assets"
OUTPUT = ROOT / "assets" / "male_candidates"
VARIANTS = ("tip", "tip_small", "cool")
STATES = ("eats", "mouth_moves", "proboscis_only", "no_response")
KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))


def source_paths() -> list[Path]:
    paths = [SOURCE / "fly" / f"{state}_{i}.png"
             for state, count in (("idle", 2), ("fly", 4), ("land", 1), ("proboscis", 3))
             for i in range(1, count + 1)]
    paths += [SOURCE / "response" / f"{prefix}{state}_{i}.png"
              for prefix in ("", "inset_") for state in STATES for i in range(1, 5)]
    return paths


def largest_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count < 2:
        return np.zeros_like(mask, dtype=bool)
    return labels == (1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]))


def masks(rgba: np.ndarray, inset: bool) -> tuple[np.ndarray, np.ndarray, dict]:
    rgb = rgba[:, :, :3].astype(np.float32) / 255
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    visible = rgba[:, :, 3] > 0
    pale = visible & (hsv[:, :, 1] <= .48) & (hsv[:, :, 2] >= .32)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(pale.astype(np.uint8), 8)
    wing = np.zeros(visible.shape, dtype=np.uint8)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] >= 4:
            component = (labels == label).astype(np.uint8)
            contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(wing, contours, -1, 1, cv2.FILLED)
    wing = (cv2.dilate(wing, KERNEL) > 0) | (rgba[:, :, 3] < 200)
    body = visible & ~wing
    tip = np.zeros_like(body)
    info = {"head_end": "manual review", "reason": "", "wing_pixels": int((wing & visible).sum())}
    if inset:
        info["reason"] = "cropped head/mouth; abdomen and whole-body axis absent; tip omitted"
        return body, tip, info
    core = largest_component(cv2.morphologyEx(body.astype(np.uint8), cv2.MORPH_OPEN, KERNEL))
    yy, xx = np.nonzero(core)
    if len(xx) < 12:
        info["reason"] = "insufficient body core; tip omitted"
        return body, tip, info
    points = np.column_stack((xx, yy)).astype(float)
    centre = points.mean(axis=0)
    values, vectors = np.linalg.eigh(np.cov(points, rowvar=False))
    ratio = float(values[-1] / max(values[0], 1e-9))
    info["axis_ratio"] = round(ratio, 6)
    if ratio < 1.25:
        info["reason"] = "ambiguous PCA axis; tip omitted"
        return body, tip, info
    axis = vectors[:, -1]
    eye = largest_component(body & (hsv[:, :, 0] < 16) & (hsv[:, :, 1] > .70) & (hsv[:, :, 2] > .35))
    ey, ex = np.nonzero(eye)
    if len(ex) < 3:
        info["reason"] = "insufficient red-eye pixels; tip omitted"
        return body, tip, info
    eye_centre = np.array([ex.mean(), ey.mean()])
    projection = (points - centre) @ axis
    offset = float((eye_centre - centre) @ axis)
    if abs(offset) < .15 * np.ptp(projection):
        info["reason"] = "eye does not resolve PCA sign; tip omitted"
        return body, tip, info
    if offset < 0:
        axis = -axis
    projection = (points - centre) @ axis
    cutoff = float(projection.min() + np.ptp(projection) / 3)
    grid_y, grid_x = np.indices(body.shape)
    along = (grid_x - centre[0]) * axis[0] + (grid_y - centre[1]) * axis[1]
    rim = cv2.dilate(core.astype(np.uint8), KERNEL) > 0
    tip = body & rim & (along <= cutoff)
    direction = ("right" if axis[0] > 0 else "left") if abs(axis[0]) >= abs(axis[1]) else ("down" if axis[1] > 0 else "up")
    info.update(head_end=f"{direction} (red eye; PCA)", reason="",
                axis_xy=axis.tolist(), centre_xy=centre.tolist(), eye_xy=eye_centre.tolist(),
                eye_pixels=len(ex), tip_pixels=int(tip.sum()))
    return body, tip, info


def transform(rgba: np.ndarray, body: np.ndarray, tip: np.ndarray, variant: str) -> Image.Image:
    result = rgba.copy()
    if variant == "cool":
        hsv = cv2.cvtColor(rgba[:, :, :3].astype(np.float32) / 255, cv2.COLOR_RGB2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] - 8) % 360
        hsv[:, :, 1] *= .85
        hsv[:, :, 2] *= .88
        shifted = np.rint(cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB) * 255).clip(0, 255).astype(np.uint8)
        result[body, :3] = shifted[body]
    result[tip, :3] = np.rint(result[tip, :3].astype(float) * .35).astype(np.uint8)
    image = Image.fromarray(result)
    if variant == "tip_small":
        small = image.resize(tuple(round(d * .90) for d in image.size), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", image.size)
        canvas.paste(small, ((image.width - small.width) // 2, (image.height - small.height) // 2))
        image = canvas
    return image


def preview_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Pillow builds without WOFF2 support use the explicitly permitted fallback.
    path = SOURCE / "fonts" / "pixelify-sans.woff2"
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default(size=size)


def preview(images: dict, names: list[str], rows: list[str], target: Path, title: str) -> None:
    # Each cell has stacked light/dark patches. Every sprite uses exactly 4x
    # its native pixels; common 272px patches accommodate the 64px insets.
    label_w, cell_w, patch_h, row_h, top = 150, 280, 272, 574, 100
    sheet = Image.new("RGB", (label_w + len(names) * cell_w, top + len(rows) * row_h), "#e2ded5")
    draw = ImageDraw.Draw(sheet)
    font, small = preview_font(22), preview_font(17)
    draw.text((16, 12), title, fill="#29231c", font=font)
    draw.text((16, 43), "DP4 preview only | native pixels x4 | upper: light / lower: dark | * manual review: no abdomen in inset", fill="#29231c", font=small)
    for column, name in enumerate(names):
        draw.text((label_w + column * cell_w + 8, 74), name, fill="#29231c", font=small)
    for row, variant in enumerate(rows):
        y = top + row * row_h
        draw.text((12, y + 15), variant, fill="#29231c", font=font)
        for column, name in enumerate(names):
            x = label_w + column * cell_w
            image = images[(variant, name)]
            enlarged = image.resize((image.width * 4, image.height * 4), Image.Resampling.NEAREST)
            for index, colour in enumerate(("#fff4dc", "#252c36")):
                py = y + index * patch_h
                draw.rectangle((x + 4, py, x + cell_w - 5, py + patch_h - 5), fill=colour)
                sheet.paste(enlarged, (x + (cell_w - enlarged.width) // 2, py + (patch_h - enlarged.height) // 2), enlarged)
            if name.startswith("inset_") and variant != "female":
                draw.text((x + 8, y + 2 * patch_h), "* manual review / tip omitted", fill="#713b21", font=small)
    sheet.save(target, optimize=True)


def promote(variant: str, root: Path = ROOT) -> None:
    """Copy a chosen set unchanged; refuse either existing destination.

    Publish the config marker last so the site never probes absent image paths.
    The original female art and shared emotion atlas are never copied or changed.
    """
    if variant not in VARIANTS:
        raise ValueError(f'Unknown male sprite variant: {variant}')
    assets = root / 'site/assets'
    targets = [assets / 'fly_male', assets / 'response_male']
    for target in targets:
        if target.exists():
            raise FileExistsError(f'Refusing to overwrite: {target}')
    config_path = root / 'site/config.json'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    copies = []
    for original in source_paths():
        source = root / 'assets/male_candidates' / variant / original.name
        if not source.is_file():
            raise FileNotFoundError(source)
        with Image.open(source) as image:
            image.verify()
        copies.append((source, assets / (original.parent.name + '_male') / original.name))
    for target in targets:
        target.mkdir(parents=True)
    for source, target in copies:
        shutil.copyfile(source, target)
    config['male_sprite_variant'] = variant
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Promoted {variant}: {len(copies)} PNGs; male_sprite_variant recorded in site/config.json')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--promote', choices=VARIANTS, help='promote the owner-chosen variant; refuse existing folders')
    args = parser.parse_args()
    if args.promote:
        promote(args.promote)
        return 0
    paths = source_paths()
    # Load everything before writing, so a missing required frame fails clearly.
    originals = {path: Image.open(path).convert("RGBA") for path in paths}
    emotion = SOURCE / "response" / "emotions-v1.png"
    with Image.open(emotion) as image:
        image.load()  # Read and verify the fly-agnostic sheet, never transform/copy it.
    images, records = {}, []
    for path, original in originals.items():
        rgba = np.array(original)
        body, tip, decision = masks(rgba, path.name.startswith("inset_"))
        images[("female", path.stem)] = original
        for variant in VARIANTS:
            image = transform(rgba, body, tip, variant)
            target = OUTPUT / variant / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, optimize=True)
            images[(variant, path.stem)] = image
            # Count visible RGBA changes, not hidden RGB in transparent padding.
            changed = np.any(rgba != np.array(image), axis=2)
            visible = (rgba[:, :, 3] > 0) | (np.array(image)[:, :, 3] > 0)
            records.append({"file": path.name, "variant": variant,
                            "changed_pixels": int((changed & visible).sum()),
                            "width": image.width, "height": image.height, **decision})
    columns = ["idle_1", "fly_1", "land_1", "proboscis_2", "eats_1", "no_response_1", "inset_eats_1"]
    preview(images, columns, ["female", *VARIANTS], OUTPUT / "preview_sheet.png", "Male fly candidates / female reference")
    preview(images, [f"fly_{i}" for i in range(1, 5)] + [f"eats_{i}" for i in range(1, 5)],
            ["tip"], OUTPUT / "preview_animation.png", "tip / motion continuity / fly 1-4 and eats 1-4")
    table = io.StringIO(newline="")
    writer = csv.writer(table, delimiter="\t", lineterminator="\n")
    writer.writerow(["file", "variant", "changed_pixels", "head_end", "reason"])
    for record in records:
        writer.writerow([record[key] for key in ("file", "variant", "changed_pixels", "head_end", "reason")])
    (OUTPUT / "transform_report.tsv").write_text(table.getvalue(), encoding="utf-8")
    manifest = {"source_root": "site/assets", "heuristic": __doc__,
                "sources_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in [*paths, emotion]}, "frames": records}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(table.getvalue(), end="")
    flagged = sorted({r["file"] for r in records if r["head_end"] == "manual review"})
    print(f"{len(paths)} source frames x 3 variants = {len(records)} candidate PNGs; {len(flagged)} manual-review frames")
    print("Previews: assets/male_candidates/preview_sheet.png; assets/male_candidates/preview_animation.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
