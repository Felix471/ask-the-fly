#!/usr/bin/env python3
"""Local Chromium regression: approved state presentation, not new model analysis."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:8773/')
    parser.add_argument('--out', type=Path, default=Path('results/mn11-site/browser'))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = []
    cases = [('eats', 'apple,black-coffee'), ('mouth_moves', 'bacon,black-coffee'),
             ('proboscis_only', 'cappuccino,black-coffee'), ('no_response', 'beer,black-coffee')]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in ('zh', 'en'):
            for state, dishes in cases:
                page = browser.new_page(viewport={'width':390, 'height':1000})
                errors, external, failed = [], [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda request: external.append(request.url) if urlparse(request.url).netloc != urlparse(args.base).netloc else None)
                page.on('response', lambda response: failed.append(response.url) if response.status >= 400 else None)
                query = f'?d={dishes}&lang={lang}&seed=1' + ('&m=opposite' if state=='no_response' else '')
                page.goto(args.base.rstrip('/')+'/'+query)
                page.wait_for_function('(s)=>window.__askfly?.snapshot().responseState===s && !document.querySelector("#response-detail").hidden', arg=state, timeout=30000)
                page.locator('#scene-panel').screenshot(path=str(args.out/f'{lang}-{state}-action.png'))
                page.wait_for_function('()=>window.__askfly.snapshot().phase==="result"', timeout=45000)
                snapshot=page.evaluate('window.__askfly.snapshot()')
                assert len([k for k in snapshot['rasterKeys'] if k.startswith('MN11')])==4, snapshot
                if state=='no_response':
                    assert snapshot['flyHidden'], snapshot
                    assert page.locator('#fly-bubble').is_hidden()
                    assert page.locator('#scene-status').inner_text() == ('果蝇转身走了。' if lang=='zh' else 'The fly leaves.')
                else:
                    assert snapshot['responseState']==state, snapshot
                    assert not snapshot['flyHidden'], snapshot
                    assert page.locator('#fly-bubble').is_visible()
                page.screenshot(path=str(args.out/f'{lang}-{state}-result.png'),full_page=True)
                assert not errors and not external and not failed, (errors,external,failed)
                report.append({'lang':lang,'state':state,'snapshot':snapshot,'external_requests':external})
                print(f'{lang} {state}: PASS',flush=True)
                page.close()
        browser.close()
    (args.out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    main()
