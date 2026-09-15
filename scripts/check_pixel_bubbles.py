"""Check the rendered pixel bubble and every supplied line in local Chromium."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/pixel-bubbles'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    buckets = json.loads((ROOT / 'copy/fly_lines.json').read_text(encoding='utf8'))['buckets']
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in ('zh', 'en'):
            page = browser.new_page(viewport={'width':390,'height':844})
            errors=[]
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:8773/?d=apple,black-coffee&lang={lang}&seed=1')
            page.locator('#fly-bubble').wait_for(state='visible')
            page.evaluate('()=>document.fonts.ready')
            assert page.locator('.bubble-text').inner_text() == ('就这味儿。' if lang=='zh' else "That's all it is.")
            family=page.locator('.bubble-text').evaluate('(e)=>getComputedStyle(e).fontFamily')
            assert ('Fusion Pixel' if lang=='zh' else 'Pixelify Sans') in family, family
            page.locator('.scene-stage').screenshot(path=str(OUT/f'{lang}-live.png'))
            # Detach the animation's node for a stable component-only fixture;
            # the original live-state flow is independently covered by check_mn11_site.
            page.evaluate('''()=>{const b=document.querySelector('#fly-bubble');b.replaceWith(b.cloneNode(true));}''')
            for width in (360,390,430):
                page.set_viewport_size({'width':width,'height':844})
                for b in buckets:
                    for i,line in enumerate(b[lang]):
                        bounds=page.evaluate('''({line})=>{
                          const b=document.querySelector('#fly-bubble');b.style.left='8px';b.style.top='8px';b.hidden=false;
                          const t=b.querySelector('.bubble-text');t.textContent=line;
                          const r=b.getBoundingClientRect();
                          return {overflow:t.scrollWidth>t.clientWidth,right:r.right,width:innerWidth};
                        }''',{'line':line})
                        assert not bounds['overflow'] and bounds['right']<=bounds['width'], (width,b['id'],i,bounds)
                if width==390:
                    for emotion,bucket in [('happy',1),('sweat',7),('deadpan',14)]:
                        line=next(b for b in buckets if b['id']==bucket)[lang][0]
                        page.evaluate('''({emotion,line})=>{const b=document.querySelector('#fly-bubble');b.dataset.emotion=emotion;b.querySelector('.bubble-text').textContent=line;}''',{'emotion':emotion,'line':line})
                        page.locator('#fly-bubble').screenshot(path=str(OUT/f'{lang}-{emotion}.png'))
            assert not errors, errors
            print(f'{lang}: pixel font + 144 line/width cases PASS',flush=True)
            page.close()
        browser.close()


if __name__=='__main__':
    main()
