"""Stage animations from the approved pose board; never writes site assets.

Uses the existing prep_assets background/palette/downsampling pipeline. The
red-eye registration keeps a common head anchor, not independent content crops.
This is a motion-review prototype, not a production animation acceptance test.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scripts.prep_assets import remove_background, downsample, palette_from_sprites, apply_palette

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/raw/mn11_preview/mn11-pose-preview-v2.png'
OUT = ROOT / 'results/mn11_animation_preview'
STATES = ['eats', 'mouth_moves', 'proboscis_only', 'no_response']
X_BOXES = [(225, 480), (490, 750), (770, 1025), (1040, 1305)]
Y_BOXES = [(120, 300), (330, 505), (550, 740), (765, 945)]
# Index/duration pairs. Last rest is a review-loop separator, not a model event.
SEQUENCES = {
    'eats': [(0, 220), (1, 160), (2, 420), (1, 160), (3, 900)],
    'mouth_moves': [(0, 180), (1, 180), (2, 240), (3, 220),
                    (0, 180), (1, 180), (2, 240), (3, 900)],
    'proboscis_only': [(0, 400), (1, 120), (2, 80), (3, 160), (0, 900)],
    'no_response': [(0, 180), (1, 180), (2, 140), (1, 140),
                    (2, 140), (1, 140), (3, 900)],
}


def register(image):
    pixels = np.asarray(image.convert('RGB'))
    red = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 115) & (pixels[:, :, 2] < 95)
    red[100:] = False  # Exclude the red proboscis pad below the eye.
    ys, xs = np.where(red)
    if len(xs) < 20:
        raise ValueError('Red eye anchor not found')
    eye = (int(round(float(np.median(xs)))), int(round(float(np.median(ys)))))
    clean = remove_background(image, 24)
    canvas = Image.new('RGBA', (320, 320))
    offset = (245 - eye[0], 120 - eye[1])
    box = clean.getbbox()
    if box is None or min(box[0] + offset[0], box[1] + offset[1]) < 0 or max(box[2] + offset[0], box[3] + offset[1]) > 320:
        raise ValueError('Registered frame would clip')
    canvas.alpha_composite(clean, offset)
    return canvas, eye


def enlarge(frame, size):
    return frame.resize((size, size), Image.Resampling.NEAREST)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames_dir = OUT / 'frames'
    frames_dir.mkdir(exist_ok=True)
    source = Image.open(SOURCE).convert('RGBA')
    if source.size != (1536, 1024):
        raise ValueError('Pose board coordinates require the approved 1536x1024 source')
    palette = palette_from_sprites(ROOT / 'site/assets/fly', 32)
    records = {}
    for row, state in enumerate(STATES):
        bodies, insets, anchors = [], [], []
        for i, (left, right) in enumerate(X_BOXES):
            top, bottom = Y_BOXES[row]
            registered, eye = register(source.crop((left, top, right, bottom)))
            body = apply_palette(downsample(registered, 48), palette)
            # Fixed square window relative to the registered head, not AI anatomy.
            inset_source = registered.crop((195, 75, 320, 200))
            inset = apply_palette(downsample(inset_source, 64), palette)
            body.save(frames_dir / f'{state}_{i + 1}.png')
            inset.save(frames_dir / f'inset_{state}_{i + 1}.png')
            bodies.append(body)
            insets.append(inset)
            anchors.append(eye)
        if state == 'no_response':
            insets = [insets[0]] * 4  # Mouth inset deliberately static during grooming.
            for i, inset in enumerate(insets):
                inset.save(frames_dir / f'inset_{state}_{i + 1}.png')
        slides = []
        durations = []
        for index, duration in SEQUENCES[state]:
            panel = Image.new('RGB', (520, 250), '#faf8f1')
            draw = ImageDraw.Draw(panel)
            draw.text((16, 10), state + ' / illustrative motion preview', fill='#302819')
            panel.paste(bodies[index], (35, 90), bodies[index])
            panel.paste(enlarge(bodies[index], 144), (115, 45), enlarge(bodies[index], 144))
            panel.paste(enlarge(insets[index], 128), (335, 45), enlarge(insets[index], 128))
            draw.text((30, 205), '48px native       3x nearest             mouth 2x', fill='#302819')
            slides.append(panel)
            durations.append(duration)
        slides[0].save(OUT / f'{state}.gif', save_all=True, append_images=slides[1:],
                       duration=durations, loop=0, disposal=2, optimize=False)
        bodies[0].save(OUT / f'{state}_static.png')
        records[state] = {'source_eye_centres': anchors, 'target_eye': [245, 120],
                          'sequence': SEQUENCES[state], 'body_size': [48, 48], 'inset_size': [64, 64]}
    manifest = {'source': str(SOURCE.relative_to(ROOT)),
                'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'status': 'motion review only; no site integration', 'states': records,
                'limitations': ['Registered generated poses retain residual body/wing differences.',
                                'Foreleg rubbing clarity requires owner review.',
                                'Insets are crops of illustrative art, not anatomical evidence.',
                                'No-response departure is not included in this stationary loop.',
                                'Four source insets per state are staging frames, not final deduplicated counts.']}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    cards = ''.join(f'<section><h2>{state}</h2><img src="{state}.gif" alt="{state} motion preview"><p>Motion review only</p></section>' for state in STATES)
    html = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>MN11 motion preview</title><style>body{background:#faf8f1;color:#302819;font:16px system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px}img{max-width:100%;image-rendering:pixelated}button{padding:10px}</style><h1>四状态动作预览</h1><p>左：48px 原尺寸；中：三倍；右：嘴部特写。仅设计示意，不是实验录像。</p><button id="toggle">暂停 / 播放</button><main>' + cards + '</main><script>let paused=matchMedia("(prefers-reduced-motion: reduce)").matches;function update(){document.querySelectorAll("section").forEach(s=>{const state=s.querySelector("h2").textContent;s.querySelector("img").src=state+(paused?"_static.png":".gif")})}document.querySelector("button").onclick=()=>{paused=!paused;update()};update();</script>'
    (OUT / 'index.html').write_text(html, encoding='utf-8')
    print(f'Wrote 16 body frames, 16 inset staging frames, four GIF loops and index.html: {OUT}')


if __name__ == '__main__':
    main()
