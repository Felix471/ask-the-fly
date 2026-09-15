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
SOURCE = ROOT / 'assets/raw/mn11_preview/mn11-actions-v3.png'
OUT = ROOT / 'results/mn11_animation_preview'
STATES = ['eats', 'mouth_moves', 'proboscis_only', 'no_response']
X_BOXES = [(225, 480), (490, 750), (770, 1025), (1040, 1305)]
Y_BOXES = [(120, 300), (330, 505), (550, 740), (765, 945)]
# Index/duration pairs. Last rest is a review-loop separator, not a model event.
SEQUENCES = {
    'eats': [(0, 250), (1, 180), (2, 220), (3, 220), (2, 220),
             (3, 220), (2, 220), (3, 220), (0, 800)],
    'mouth_moves': [(0, 250), (1, 220), (2, 250), (1, 220),
                    (0, 380), (1, 220), (2, 250), (3, 1000)],
    'proboscis_only': [(0, 400), (1, 120), (2, 80), (3, 160), (0, 1600)],
    'no_response': [(0, 350), (1, 180), (2, 180), (1, 180),
                    (2, 180), (1, 180), (3, 250), (3, 180)]
                   + [(3, 70)] * 10 + [(3, 1000)],
}


def body_motion(state, step):
    """Designed scene motion in native pixels, separate from mouth pose animation."""
    if state == 'no_response' and step >= 7:
        return -min(72, (step - 7) * 8), True
    if state == 'mouth_moves':
        return [0, 2, 2, 1, 0, 2, 2, -2][step], False
    return 0, False


def motion_tile(body, state, step):
    dx, flip = body_motion(state, step)
    tile = Image.new('RGBA', (80, 64))
    if flip:
        body = body.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    tile.paste(body, (16 + dx, 8))
    return tile


def register(image):
    pixels = np.asarray(image.convert('RGB'))
    red = (pixels[:, :, 0] > 150) & (pixels[:, :, 1] < 70) & (pixels[:, :, 2] < 80)
    red[:, :int(image.width * 0.6)] = False  # Exclude warm thorax pixels left of the eye.
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
            inset_source = registered.crop((215, 100, 340, 225))
            if state == 'mouth_moves':
                # Tight short-mouth crop excludes the grounded forelegs below it.
                inset_source = registered.crop((235, 128, 285, 178))
            inset = apply_palette(downsample(inset_source, 64), palette)
            body.save(frames_dir / f'{state}_{i + 1}.png')
            inset.save(frames_dir / f'inset_{state}_{i + 1}.png')
            bodies.append(body)
            insets.append(inset)
            anchors.append(eye)
        if state == 'no_response':
            # The dedicated closed-mouth reference contains no foreleg: a leg in
            # the old full-body crop could be mistaken for an extended proboscis.
            closed = remove_background(source.crop((1342, 775, 1490, 923)), 24)
            closed = apply_palette(downsample(closed, 64), palette)
            insets = [closed] * 4  # Mouth inset deliberately static during grooming.
            for i, inset in enumerate(insets):
                inset.save(frames_dir / f'inset_{state}_{i + 1}.png')
        slides = []
        durations = []
        for step, (index, duration) in enumerate(SEQUENCES[state]):
            panel = Image.new('RGB', (620, 260), '#faf8f1')
            draw = ImageDraw.Draw(panel)
            draw.text((16, 10), state + ' / illustrative motion preview', fill='#302819')
            tile = motion_tile(bodies[index], state, step)
            zoom = tile.resize((240, 192), Image.Resampling.NEAREST)
            panel.paste(tile, (15, 85), tile)
            panel.paste(zoom, (125, 30), zoom)
            panel.paste(enlarge(insets[index], 128), (435, 50), enlarge(insets[index], 128))
            draw.text((15, 230), '48px native', fill='#302819')
            draw.text((180, 230), '3x nearest', fill='#302819')
            draw.text((450, 230), 'mouth 2x', fill='#302819')
            slides.append(panel)
            durations.append(duration)
        slides[0].save(OUT / f'{state}_v3.gif', save_all=True, append_images=slides[1:],
                       duration=durations, loop=0, disposal=2, optimize=False)
        slides[0].save(OUT / f'{state}_v3_static.png')
        records[state] = {'source_eye_centres': anchors, 'target_eye': [245, 120],
                          'sequence': SEQUENCES[state], 'body_size': [48, 48], 'inset_size': [64, 64],
                          'body_motion': [body_motion(state, i) for i in range(len(SEQUENCES[state]))]}
    manifest = {'source': str(SOURCE.relative_to(ROOT)),
                'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'status': 'motion review only; no site integration', 'states': records,
                'limitations': ['Registered generated poses retain residual body/wing differences.',
                                'Foreleg rubbing clarity requires owner review.',
                                'Insets are crops of illustrative art, not anatomical evidence.',
                                'No-response departure is a mirrored slide, not a wingbeat animation.',
                                'Four source insets per state are staging frames, not final deduplicated counts.']}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    descriptions = ['持续接触，末端反复开合', '短嘴开合，靠近后退，不伸长喙',
                    '轻碰一下即收回，之后静止', '低位搓前足，嘴不动，然后转身离开']
    cards = ''.join(f'<section><h2>{state}</h2><p>{description}</p><canvas width="620" height="260" data-state="{state}" role="img" aria-label="{description}"></canvas></section>' for state, description in zip(STATES, descriptions))
    html = '''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MN11 motion preview v3</title><style>
body{background:#faf8f1;color:#302819;font:16px system-ui;margin:24px}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,620px),1fr));gap:24px}
canvas{width:620px;max-width:100%;image-rendering:pixelated}button{padding:10px}
</style><h1>四状态动作预览 · v3 重做关键帧</h1>
<p>左：48px 原尺寸；中：三倍；右：嘴部特写。窄屏会整体缩小。仅设计示意，不是实验录像。</p>
<p>❤️ 喜欢 · 🤔 犹豫 · ··· 轻碰 · 😒 不感兴趣。气泡是拟人化设计，不是额外读出。</p>
<button id="toggle">暂停 / 播放</button><label><input id="bubbles" type="checkbox" checked>显示情绪气泡</label><main>''' + cards + '''</main><script>
const records=RECORDS_PLACEHOLDER;
const icons={eats:'❤️',mouth_moves:'🤔',proboscis_only:'···',no_response:'😒'};
let paused=matchMedia('(prefers-reduced-motion: reduce)').matches, elapsed=0, last=0;
document.querySelector('button').onclick=()=>{paused=!paused};
const load=src=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(Error(src));image.src=src});
async function start(){
const views=await Promise.all([...document.querySelectorAll('canvas')].map(async canvas=>{
const state=canvas.dataset.state;
const bodies=await Promise.all([1,2,3,4].map(i=>load(`frames/${state}_${i}.png?v=3`)));
const insets=await Promise.all([1,2,3,4].map(i=>load(`frames/inset_${state}_${i}.png?v=3`)));
return {canvas,state,bodies,insets};}));
document.body.dataset.ready='true';
function tick(now){if(last && !paused)elapsed+=Math.min(now-last,100);last=now;
for(const {canvas,state,bodies,insets} of views){
const record=records[state], seq=record.sequence;
let time=elapsed%seq.reduce((s,x)=>s+x[1],0),step=0;
while(step<seq.length-1 && time>=seq[step][1]){time-=seq[step][1];step++;}
const index=seq[step][0],[dx,flip]=record.body_motion[step];
canvas.dataset.step=step;
const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;
ctx.fillStyle='#faf8f1';ctx.fillRect(0,0,620,260);
ctx.fillStyle='#302819';ctx.font='12px system-ui';
ctx.fillText('48px native',15,242);ctx.fillText('3x nearest',180,242);ctx.fillText('mouth 2x',450,242);
for(const [x,y,scale] of [[15,85,1],[125,30,3]]){
ctx.save();ctx.beginPath();ctx.rect(x,y,80*scale,64*scale);ctx.clip();
ctx.translate(x+(16+dx)*scale,y+8*scale);
if(flip){ctx.translate(48*scale,0);ctx.scale(-1,1)}
ctx.drawImage(bodies[index],0,0,48*scale,48*scale);ctx.restore();}
ctx.drawImage(insets[index],435,50,128,128);
if(document.querySelector('#bubbles').checked && dx>-45){
const x=125+(16+dx+(flip?11:37))*3;
ctx.fillStyle='white';ctx.strokeStyle='#76664e';ctx.lineWidth=1.5;
ctx.beginPath();ctx.roundRect(x-24,37,48,35,12);ctx.fill();ctx.stroke();
ctx.beginPath();ctx.moveTo(x-6,72);ctx.lineTo(x-2,79);ctx.lineTo(x+3,72);ctx.fill();ctx.stroke();
ctx.fillStyle='#302819';ctx.textAlign='center';ctx.textBaseline='middle';
ctx.font='23px Segoe UI Emoji, Apple Color Emoji, sans-serif';ctx.fillText(icons[state],x,54);
ctx.textAlign='start';ctx.textBaseline='alphabetic';}
}requestAnimationFrame(tick);}requestAnimationFrame(tick);
}start().catch(error=>{document.body.dataset.error=error.message;console.error(error)});
</script>'''.replace('RECORDS_PLACEHOLDER', json.dumps(records))
    (OUT / 'index.html').write_text(html, encoding='utf-8')
    print(f'Wrote 16 body frames, 16 inset staging frames, four GIF loops and index.html: {OUT}')


if __name__ == '__main__':
    main()
