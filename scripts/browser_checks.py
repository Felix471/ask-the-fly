#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Browser regression checks for the audit tickets, driven through the real UI with Playwright.

Each check reproduces one ticket's trigger (delayed or failing replay files, out-of-order
requests, reset during a pending await, language switch mid-animation, IME composition)
and asserts the observable outcome; console errors, page errors and unhandled rejections
fail every check. Runs against a static server of site/ (python -m http.server 8765
--directory site).

  .venv\\Scripts\\python scripts/browser_checks.py               # all checks
  .venv\\Scripts\\python scripts/browser_checks.py --only F02,F05
"""

from __future__ import annotations

import argparse
import sys
import time
import re
from urllib.parse import quote

BASE = "http://127.0.0.1:8765/"
INIT = """
window.__rejections = [];
window.addEventListener('unhandledrejection', (e) => window.__rejections.push(String(e.reason)));
// The checks written before the guess step are about the run itself: unless a check sets
// window.__guess to something else, the step is passed through its own "Just watch" button.
window.__guess = 'watch';
setInterval(() => {
  if (window.__guess !== 'watch') return;
  const button = document.querySelector('[data-panel="guess-watch"]:not([hidden])');
  if (button && button.offsetParent) button.click();
}, 40);
"""


class Hold:
    """Defers matching requests until release(); Playwright leaves unanswered routes pending."""

    def __init__(self, page, pattern):
        self.page = page
        self.pattern = pattern
        self.routes = []
        page.route(pattern, lambda route: self.routes.append(route))

    def release(self):
        for route in self.routes:
            try:
                route.continue_()
            except Exception:  # noqa: BLE001 - a released page may have navigated away
                pass
        self.routes.clear()

    def stop(self):
        self.release()
        self.page.unroute(self.pattern)


def open_page(browser, query, width=390, init=None):
    # bypass_csp: the page's CSP (verified separately) would block Playwright's evaluated predicates
    page = browser.new_page(viewport={"width": width, "height": 900}, bypass_csp=True)
    page.add_init_script(INIT + (init or ''))
    errors = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(BASE + query, wait_until="domcontentloaded")
    return page, errors, requests


def debug(page):
    return page.evaluate("window.__askfly ? window.__askfly.snapshot() : null")


def wait_result(page, timeout=90000):
    page.wait_for_function("!document.getElementById('result-panel').hidden", timeout=timeout)


def replay_requests(requests):
    return [u for u in requests if ("/data/replay/" in u or "/data/replay_v1_2/" in u) and u.endswith(".bin")]


def finish(page, errors, problems):
    rejections = page.evaluate("window.__rejections")
    if rejections:
        problems.append(f"unhandled rejections: {rejections}")
    if errors:
        problems.append(f"errors: {errors}")
    page.close()
    return problems


# ---------------------------------------------------------------- checks

def check_F02(browser):
    """More neurons toggle must not replay anything; it only expands the list (aria-expanded)."""
    page, errors, requests = open_page(browser, "?d=hotpot,black-coffee&lang=en")
    problems = []
    page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
    page.wait_for_function("document.getElementById('brain-caption').textContent.length > 0", timeout=30000)
    page.click("#skip-btn")
    wait_result(page)
    page.evaluate("document.getElementById('brain-details').open = true")
    page.click("text=Silence Clavicle")
    page.wait_for_function("document.getElementById('brain-caption').textContent.includes('clavicle')", timeout=20000)
    page.wait_for_timeout(300)
    before = page.evaluate("document.getElementById('brain-caption').textContent")
    n_before = len(replay_requests(requests))
    pressed_before = page.evaluate("[...document.querySelectorAll('#silence-controls button[aria-pressed=true]')].map(b => b.textContent)")
    page.click("text=More neurons")
    page.wait_for_timeout(600)
    after = page.evaluate("document.getElementById('brain-caption').textContent")
    pressed_after = page.evaluate("[...document.querySelectorAll('#silence-controls button[aria-pressed=true]')].map(b => b.textContent)")
    expanded = page.evaluate("(document.querySelector('#silence-controls button[aria-expanded]') || {}).getAttribute ? document.querySelector('#silence-controls button[aria-expanded]').getAttribute('aria-expanded') : null")
    if after != before:
        problems.append(f"caption changed on expand: {before!r} -> {after!r}")
    if pressed_after != pressed_before:
        problems.append(f"pressed variant changed: {pressed_before} -> {pressed_after}")
    if len(replay_requests(requests)) != n_before:
        problems.append("expanding issued a replay request")
    if expanded != "true":
        problems.append(f"toggle aria-expanded is {expanded!r}, expected 'true'")
    return finish(page, errors, problems)


def check_F03(browser):
    """A slow older variant request must not overwrite the newer selection."""
    page, errors, requests = open_page(browser, "?d=hotpot,black-coffee&lang=en")
    problems = []
    page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
    page.wait_for_function("document.getElementById('brain-caption').textContent.length > 0", timeout=30000)
    page.click("#skip-btn")
    wait_result(page)
    page.evaluate("document.getElementById('brain-details').open = true")
    hold = Hold(page, "**/*_silence_roundup.bin")
    page.click("text=Silence Roundup")  # A: held
    page.wait_for_timeout(200)
    page.click("text=Silence Clavicle")  # B: fast
    page.wait_for_function("document.getElementById('brain-caption').textContent.includes('clavicle')", timeout=20000)
    page.wait_for_timeout(200)
    hold.release()
    page.wait_for_timeout(1200)
    caption = page.evaluate("document.getElementById('brain-caption').textContent")
    pressed = page.evaluate("[...document.querySelectorAll('#silence-controls button[aria-pressed=true]')].map(b => b.textContent)")
    silence_caption = page.evaluate("document.getElementById('silence-caption').textContent")
    if "roundup" in caption.lower():
        problems.append(f"late Roundup response overwrote the view: caption={caption!r}")
    if pressed != ["Silence Clavicle"]:
        problems.append(f"pressed buttons after late response: {pressed}")
    if "Roundup" in silence_caption:
        problems.append(f"silence caption from the stale request: {silence_caption!r}")
    hold.stop()
    return finish(page, errors, problems)


def check_F04(browser):
    """Silencing buttons are disabled while the auto-taste sequence runs, enabled after."""
    page, errors, requests = open_page(browser, "?d=hotpot,black-coffee,pho&lang=en")
    problems = []
    page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
    page.wait_for_function("document.querySelectorAll('#silence-controls button').length > 0", timeout=20000)
    page.wait_for_timeout(800)
    enabled_during = page.evaluate("[...document.querySelectorAll('#silence-controls button')].filter(b => !b.disabled).map(b => b.textContent)")
    if enabled_during:
        problems.append(f"enabled during tasting: {enabled_during}")
    page.click("#skip-btn")
    wait_result(page)
    page.wait_for_timeout(300)
    disabled_after = page.evaluate("[...document.querySelectorAll('#silence-controls button')].filter(b => b.disabled).map(b => b.textContent)")
    if disabled_after:
        problems.append(f"still disabled after the run: {disabled_after}")
    return finish(page, errors, problems)


def check_F05(browser):
    """Reset during a pending replay: the late response must not touch the new view or leave run state behind."""
    page, errors, requests = open_page(browser, "?d=hotpot,black-coffee&lang=en")
    problems = []
    hold = Hold(page, "**/data/replay_v1_2/G_*.bin")
    page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
    page.wait_for_timeout(1500)  # the fly reaches the first plate and waits for its replay
    page.click("#skip-btn")
    wait_result(page)
    page.click("#again-btn")  # reset and discard
    page.wait_for_timeout(200)
    snap_before = debug(page)
    hold.release()
    page.wait_for_timeout(1500)
    snap = debug(page)
    if not page.evaluate("document.getElementById('scene-panel').hidden"):
        problems.append("scene panel reappeared after reset")
    if not page.evaluate("document.getElementById('result-panel').hidden"):
        problems.append("result panel reappeared after reset")
    if page.evaluate("document.getElementById('brain-caption').textContent"):
        problems.append("brain caption written by the stale request")
    if not page.evaluate("document.getElementById('mn9-pill').hidden"):
        problems.append("MN9 pill shown by the stale request")
    if snap is None:
        problems.append("no debug accessor (window.__askfly)")
    else:
        if not page.evaluate("!document.getElementById('input-panel').hidden"):
            problems.append("input panel not shown after reset")
        if snap.get("currentCell"):
            problems.append(f"currentCell not cleared: {snap.get('currentCell')!r}")
        if snap.get("sceneRunning"):
            problems.append("hidden scene animation running after reset")
        if snap.get("brainPlaying"):
            problems.append("brain replay playing after reset")
    # a new round still works
    page.click("#ask-btn")
    page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
    page.click("#skip-btn")
    wait_result(page)
    hold.stop()
    return finish(page, errors, problems)


def check_F06(browser):
    """Switching language mid-animation must not reveal the result."""
    page, errors, requests = open_page(browser, "?d=hotpot,black-coffee,pho&lang=en")
    problems = []
    hold = Hold(page, "**/data/replay_v1_2/G_*.bin")
    page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
    page.wait_for_timeout(1200)
    page.click("#lang-toggle")
    page.wait_for_timeout(400)
    if not page.evaluate("document.getElementById('result-panel').hidden"):
        problems.append("result panel shown after a language switch during tasting")
    if page.evaluate("document.getElementById('scene-panel').hidden"):
        problems.append("scene hidden after a language switch during tasting")
    snap = debug(page)
    if not snap or snap.get("phase") != "tasting":
        problems.append(f"phase after switch: {(snap or {}).get('phase')!r} (expected an explicit 'tasting' phase)")
    chips = page.evaluate("[...document.querySelectorAll('#option-list li span')].map(e => e.textContent)")
    if chips != ["火锅", "黑咖啡", "越南河粉"]:
        problems.append(f"chips not relabelled in zh: {chips}")
    hold.release()
    hold.stop()
    return finish(page, errors, problems)


def check_F08(browser):
    """A share request whose snapshot is still pending must not open the dialog after reset."""
    page, errors, requests = open_page(browser, "?d=hotpot,black-coffee&lang=en")
    problems = []
    warnings = []
    page.on("console", lambda m: warnings.append(m.text) if m.type == "warning" else None)
    hold = Hold(page, "**/data/replay_v1_2/G_*.bin")
    page.wait_for_selector("#scene-panel:not([hidden])", timeout=20000)
    page.wait_for_timeout(300)
    page.click("#skip-btn")
    wait_result(page)
    page.click("#share-btn")  # snapshot waits for the held winner replay
    page.wait_for_timeout(300)
    if page.evaluate("document.getElementById('card-dialog').open"):
        problems.append("dialog opened before the snapshot resolved (cannot test the race)")
    page.click("#again-btn")  # reset cancels the open intent
    page.wait_for_timeout(200)
    hold.release()
    page.wait_for_timeout(1500)
    if page.evaluate("document.getElementById('card-dialog').open"):
        problems.append("stale share request opened the dialog after reset")
    href = page.evaluate("document.getElementById('download-link').getAttribute('href')")
    if href:
        problems.append("stale download link left after reset")
    if any("share" in w.lower() for w in warnings):
        problems.append(f"share request failed silently (console warning): {[w for w in warnings if 'share' in w.lower()]}")
    hold.stop()
    return finish(page, errors, problems)


def check_F15(browser):
    """Enter during IME composition must not submit the option form."""
    page, errors, requests = open_page(browser, "?lang=zh")
    problems = []
    page.wait_for_function("document.querySelectorAll('#popular-row .tile').length > 0", timeout=20000)
    page.fill("#option-input", "huo")
    prevented = page.evaluate("""() => {
      const input = document.getElementById('option-input');
      input.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }));
      const ev = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 229, isComposing: true, bubbles: true, cancelable: true });
      input.dispatchEvent(ev);
      const prevented = ev.defaultPrevented;
      input.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: '火锅' }));
      return prevented;
    }""")
    page.wait_for_timeout(200)
    chips = page.evaluate("document.querySelectorAll('#option-list li').length")
    if not prevented:
        problems.append("Enter during composition was not prevented")
    if chips != 0:
        problems.append(f"composition Enter added {chips} option(s)")
    # after composition ends, Enter still works
    page.fill("#option-input", "火锅")
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    if page.evaluate("document.querySelectorAll('#option-list li').length") != 1:
        problems.append("Enter after composition did not add the dish")
    return finish(page, errors, problems)


def check_F16(browser):
    """Fly selection is lazy, keyboard accessible, persistent, and old links stay female."""
    page, errors, requests = open_page(browser, "")
    problems = []
    page.wait_for_function("document.querySelectorAll('#popular-row .tile').length > 0")
    if any('_male' in u for u in requests):
        problems.append('female-only page fetched male data')
    radio = page.locator('input[name="fly"][value="female"]')
    radio.focus()
    page.keyboard.press('ArrowRight')
    page.wait_for_function("window.__askfly.snapshot().panels.male")
    if debug(page)['fly'] != 'male' or page.evaluate("localStorage.getItem('askfly.fly')") != 'male':
        problems.append('keyboard selection did not persist male')
    page.reload()
    page.wait_for_function("window.__askfly.snapshot().panels.male")
    if debug(page)['fly'] != 'male':
        problems.append('male preference not restored')
    page.goto(BASE + '?d=candy,steak&lang=en')
    page.wait_for_selector('#scene-panel:not([hidden])')
    if debug(page)['fly'] != 'female':
        problems.append('old link inherited male preference')
    page.click('#skip-btn')
    wait_result(page)
    page.click('#again-btn')
    page.locator('input[name="fly"][value="both"]').check()
    page.wait_for_function("window.__askfly.snapshot().panels.male")
    page.locator('input[name="fly"][value="male"]').check()
    page.locator('#how').evaluate('el => el.open = true')
    if not page.locator('#how [data-i18n="howMale"]').is_visible():
        problems.append('male how-it-works copy is not rendered')
    page.locator('#how').evaluate('el => el.open = false')
    page.click('#ask-btn')
    page.wait_for_selector('#scene-panel:not([hidden])')
    page.wait_for_function("window.__askfly.snapshot().panels.male.currentCell")
    if page.locator('#scene-panel [data-panel="layout-note"]').inner_text().find('228') < 0:
        problems.append('male layout placeholder count absent')
    if 'grid trial 0' not in page.locator('#scene-panel [data-panel="mn11-replay-note"]').inner_text():
        problems.append('male trial-0 note not visible')
    if page.locator('#scene-panel [data-panel="silence-controls"]').is_visible():
        problems.append('male silencing controls visible')
    page.click('#skip-btn')
    wait_result(page)
    if 'Male fly' not in page.locator('#table-fly').text_content():
        problems.append('male table heading missing')
    page.click('#again-btn')
    page.locator('input[name="fly"][value="female"]').check()
    page.click('#ask-btn')
    page.wait_for_selector('#scene-panel:not([hidden])')
    page.wait_for_function("window.__askfly.snapshot().panels.female.currentCell")
    if debug(page)['panels']['male']['brainPlaying']:
        problems.append('male replay leaked into female round')
    return finish(page, errors, problems)


def check_F17(browser):
    """Both scenes run independently, show honest disagreement, and share f=both."""
    page, errors, requests = open_page(browser, '?d=brownie,steak&lang=en&f=both', width=1280)
    problems = []
    page.wait_for_function("Object.values(window.__askfly.snapshot().panels).length === 2 && Object.values(window.__askfly.snapshot().panels).every(p=>p.sceneRunning)")
    if page.locator('.scene-panel:visible').count() != 2:
        problems.append('two scenes not visible')
    if page.locator('#skip-btn-male').inner_text() != 'Skip':
        problems.append('cloned male controls were not translated')
    if not page.locator('#scene-panel-male [data-i18n="legendSugar"]').inner_text():
        problems.append('cloned male legend missing')
    page.wait_for_function("Object.values(window.__askfly.snapshot().panels).every(p=>p.currentCell)")
    page.click('#skip-btn')
    wait_result(page)
    if not page.locator('#disagreement').is_visible():
        problems.append('brownie/steak disagreement absent')
    sentence = page.locator('#disagreement span').inner_text()
    if 'sex, reconstruction, cell typing, sign assignment, weight, or stimulus protocol' not in sentence:
        problems.append('commitment 4 not rendered verbatim')
    if page.locator('#results-table-male th').count() != 10:
        problems.append('male table does not have 10 columns')
    for fly in ['female','male']:
        if debug(page)['panels'][fly]['brainPlaying']:
            problems.append(f'{fly} replay still playing after skip')
    page.click('#share-btn')
    page.wait_for_selector('#card-dialog[open]')
    parsed = page.evaluate("""async () => {
      const app=await import('./app.js');
      return app.parseShareParams(app.shareParams({known:[],misses:[{name:'a'}],mode:'ask',fly:'both'},'en')).fly;
    }""")
    if parsed != 'both':
        problems.append('both share selection not round-tripped')
    page.click('#close-card-btn')
    page.click('#again-btn')
    if any(p['sceneRunning'] or p['brainPlaying'] for p in debug(page)['panels'].values()):
        problems.append('reset left a panel running')
    page.goto(BASE + '?d=candy,steak&lang=en&f=both')
    page.wait_for_selector('#scene-panel:not([hidden])')
    page.click('#skip-btn')
    wait_result(page)
    if page.locator('#disagreement').is_visible():
        problems.append('agreeing candy/steak pair has disagreement line')
    return finish(page, errors, problems)


def check_F18(browser):
    """Male and both language changes preserve phase, notes, and state explanation."""
    page, errors, requests = open_page(browser, '?d=candy,steak&lang=en&f=male')
    problems = []
    page.wait_for_selector('#scene-panel:not([hidden])')
    page.click('#lang-toggle')
    if debug(page)['phase'] != 'tasting':
        problems.append('male language switch revealed result')
    wait_result(page)
    note=page.locator('#scene-panel [data-panel="male-state-note"]')
    if not note.is_visible() or '400' not in note.inner_text():
        problems.append('male state note absent beneath state explanation')
    if '30' not in page.locator('#scene-panel [data-panel="mn11-replay-note"]').inner_text():
        problems.append('male replay note lost on language switch')
    page.click('#again-btn')
    page.locator('input[name="fly"][value="both"]').check()
    page.click('#ask-btn')
    page.wait_for_function("Object.values(window.__askfly.snapshot().panels).every(p=>p.sceneRunning)")
    page.click('#lang-toggle')
    if debug(page)['phase'] != 'tasting':
        problems.append('both language switch revealed result')
    page.click('#skip-btn-male')
    wait_result(page)
    if any(p['brainPlaying'] for p in debug(page)['panels'].values()):
        problems.append('secondary skip did not stop both replays')
    return finish(page, errors, problems)


def check_F19(browser):
    """A broken male bundle reports a notice, never substitutes female data, and retries."""
    page, errors, requests = open_page(browser, '')
    problems = []
    page.wait_for_function("document.querySelectorAll('#popular-row .tile').length > 0")
    warnings = []
    page.on('console', lambda m: warnings.append(m.text) if m.type == 'warning' else None)
    pattern = '**/data/lookup_table_male.json'
    page.route(pattern, lambda route: route.fulfill(status=200, content_type='application/json', body='{}'))
    page.locator('input[name="fly"][value="male"]').check()
    page.wait_for_selector('#notice:not([hidden])')
    if debug(page)['panels'].get('male'):
        problems.append('broken male lookup was accepted')
    if not any('scene disabled:' in message for message in warnings):
        problems.append('male bundle error was swallowed')
    page.unroute(pattern)
    page.locator('input[name="fly"][value="female"]').check()
    page.locator('input[name="fly"][value="male"]').check()
    page.wait_for_function("window.__askfly.snapshot().panels.male")
    page.fill('#option-input', 'candy,steak')
    page.locator('#option-form').dispatch_event('submit')
    page.click('#ask-btn')
    page.wait_for_selector('#scene-panel:not([hidden])')
    page.click('#skip-btn')
    wait_result(page)
    # Male and female provenance must not be exchanged when rebinding the first block.
    table_commit = page.evaluate("async()=> (await (await fetch('data/lookup_table_male.json')).json()).git_commit.slice(0,7)")
    if table_commit not in page.locator('#table-meta').inner_text():
        problems.append('male view has female lookup metadata')
    return finish(page, errors, problems)


def check_F20(browser):
    """Reset cancels a delayed male replay while the independent female scene runs."""
    page, errors, requests = open_page(browser, '')
    problems = []
    hold = Hold(page, '**/data/replay_male/G_*.bin')
    page.goto(BASE + '?d=brownie,steak&lang=en&f=both')
    page.wait_for_selector('#scene-panel:not([hidden])')
    page.wait_for_function("window.__askfly.snapshot().panels.female.currentCell")
    page.click('#skip-btn-male')
    wait_result(page)
    page.click('#again-btn')
    hold.release()
    page.wait_for_timeout(1000)
    if debug(page)['phase'] != 'input':
        problems.append('late male replay changed the reset view')
    for key, panel in debug(page)['panels'].items():
        if panel['currentCell'] or panel['brainPlaying'] or panel['sceneRunning']:
            problems.append(f'{key} retained run state after reset')
    hold.stop()
    return finish(page, errors, problems)


def check_F21(browser):
    """A failed male replay has a visible notice while the female replay remains independent."""
    page, errors, requests = open_page(browser, '')
    problems = []
    page.route('**/data/replay_male/G_*.bin', lambda route: route.fulfill(status=200, body=b'bad replay'))
    page.goto(BASE + '?d=brownie,steak&lang=en&f=both')
    page.wait_for_selector('#notice:not([hidden])', timeout=20000)
    if not page.locator('#brain-caption-male').inner_text():
        problems.append('male failed replay has no panel failure caption')
    page.wait_for_function("window.__askfly.snapshot().panels.female.currentCell")
    if debug(page)['panels']['male']['currentCell']:
        problems.append('failed male replay was presented as loaded')
    page.click('#skip-btn')
    wait_result(page)
    if not page.locator('#notice').is_visible():
        problems.append('male replay failure notice disappeared at result')
    return finish(page, errors, problems)


def check_F22(browser):
    """Both inset boxes match single-fly sizing/alignment and draw full source frames."""
    problems = []
    for width in (1280, 390):
        for lang in ('en', 'zh'):
            references = {}
            for fly in ('female', 'male', 'both'):
                page, errors, _ = open_page(browser,
                    f'?d=mapo-tofu,dumplings,xiaolongbao&lang={lang}&f={fly}', width=width)
                wait_result(page)
                page.evaluate('document.fonts.ready')
                boxes = page.locator('.scene-panel:visible').evaluate_all('''async panels => {
                  const results=[];
                  for(const panel of panels) {
                    const el=panel.querySelector('[data-panel="mouth-inset"]');
                    const row=el.parentElement, text=row.querySelector('[data-panel="response-description"]');
                    const box=el.getBoundingClientRect(), parent=row.getBoundingClientRect();
                    const kind=panel.querySelector('[data-panel="fly-name"]').textContent.includes('MaleCNS')?'male':'female';
                    // Compare the actual backing pixels to a full-frame draw of
                    // each approved source frame. This detects clipping that a
                    // bounding-box-only test would miss.
                    const actual=el.getContext('2d').getImageData(0,0,el.width,el.height).data;
                    let fullFrame=false;
                    for(const state of ['eats','mouth_moves','proboscis_only','no_response']) {
                      for(let i=1;i<=4;i++) {
                        const image=new Image();
                        image.src=`assets/response${kind==='male'?'_male':''}/inset_${state}_${i}.png`;
                        await image.decode();
                        const expected=document.createElement('canvas');
                        expected.width=128; expected.height=128;
                        const ctx=expected.getContext('2d');ctx.imageSmoothingEnabled=false;
                        ctx.drawImage(image,0,0,128,128);
                        const pixels=ctx.getImageData(0,0,128,128).data;
                        if(pixels.length===actual.length && pixels.every((v,j)=>v===actual[j])) fullFrame=true;
                      }
                    }
                    results.push({kind,width:box.width,height:box.height,
                      left:box.left-parent.left,center:box.y+box.height/2-(parent.y+parent.height/2),
                      textLeft:text.getBoundingClientRect().left-box.right,
                      backing:[el.width,el.height],fullFrame,visible:!row.hidden,
                      noteInside:row.contains(panel.querySelector('[data-panel="male-state-note"]'))});
                  }
                  return results;
                }''')
                for box in boxes:
                    label=f'{width}/{lang}/{fly}/{box["kind"]}'
                    if not box['visible'] or not box['fullFrame'] or box['backing'] != [128, 128]:
                        problems.append(f'{label}: inset frame hidden/clipped/changed: {box}')
                    if box['kind']=='male' and box['noteInside']:
                        problems.append(f'{label}: extra male note shifts inset centering within the state row')
                    if box['width'] != 96 or box['height'] != 96 or abs(box['center']) > 1 or box['left'] != 0 or box['textLeft'] != 16:
                        problems.append(f'{label}: inset sizing/alignment changed: {box}')
                    if fly == 'both':
                        reference=references[box['kind']]
                        for key in ('width','height','left','center','textLeft','backing'):
                            if box[key] != reference[key]:
                                problems.append(f'{label}: {key} differs from single-fly box')
                        status=page.locator('.scene-panel:visible').nth(0 if box['kind']=='female' else 1).locator('[data-panel="scene-status"]').inner_text()
                        name=('female fly' if box['kind']=='female' else 'male fly') if lang=='en' else ('雌蝇' if box['kind']=='female' else '雄蝇')
                        if name not in status:
                            problems.append(f'{label}: status does not name the fly')
                    else:
                        references[box['kind']]=box
                problems=finish(page,errors,problems)
    return problems


def check_F23(browser):
    """All 15 bilingual library tabs fit, wrap and remain clickable at 390 px."""
    problems = []
    for lang in ('zh', 'en'):
        page, errors, _ = open_page(browser, f'?lang={lang}', width=390)
        page.wait_for_function("document.querySelectorAll('#popular-row .tile').length > 0")
        if page.locator('html').get_attribute('lang') != lang:
            page.click('#lang-toggle')
        page.click('#view-all-btn')
        page.evaluate('document.fonts.ready')
        tabs = page.locator('#library-tabs button')
        if tabs.count() != 15:
            problems.append(f'{lang}: expected 15 tabs, found {tabs.count()}')
        boxes = tabs.evaluate_all('''buttons => buttons.map(b => {
          const r=b.getBoundingClientRect(), parent=b.parentElement.getBoundingClientRect();
          const range=document.createRange();range.selectNodeContents(b);
          const text=range.getBoundingClientRect();
          return {label:b.textContent,top:r.top,left:r.left,right:r.right,
            fits:b.scrollWidth<=b.clientWidth && b.scrollHeight<=b.clientHeight,
            textFits:text.left>=r.left && text.right<=r.right && text.top>=r.top && text.bottom<=r.bottom,
            inRow:r.left>=parent.left && r.right<=parent.right,
            ellipsis:getComputedStyle(b).textOverflow==='ellipsis'};
        })''')
        expected = page.evaluate('''async lang => {
          const sections=await (await fetch('data/sections.json')).json();
          return [(await import('./strings.js')).STRINGS[lang].libraryAll,
            ...sections.sections.map(section=>section[lang])];
        }''', lang)
        if [box['label'] for box in boxes] != expected:
            problems.append(f'{lang}: tab labels do not match the requested language')
        if len({round(b['top']) for b in boxes}) < 2:
            problems.append(f'{lang}: tabs did not wrap')
        for i, box in enumerate(boxes):
            if not box['fits'] or not box['textFits'] or not box['inRow'] or box['ellipsis'] or box['left'] < 0 or box['right'] > 390:
                problems.append(f'{lang}: clipped label: {box}')
            tabs.nth(i).scroll_into_view_if_needed()
            if not tabs.nth(i).is_visible():
                problems.append(f'{lang}: hidden tab {box["label"]}')
            tabs.nth(i).focus()
            page.keyboard.press('Enter')
            if tabs.nth(i).get_attribute('aria-selected') != 'true':
                problems.append(f'{lang}: unreachable tab {box["label"]}')
        problems = finish(page, errors, problems)
    return problems


def check_F24(browser):
    """Not-food query labels/notes survive both flies, both modes and both languages."""
    # Read the served bundle so this check also works against a staging URL.
    page, errors, _ = open_page(browser, '')
    payload = page.evaluate('''async () => ({
      sections:await (await fetch('data/sections.json')).json(),
      dishes:await (await fetch('data/dishes.json')).json()
    })''')
    keys = {key for section in payload['sections']['sections'] if section.get('not_food') is True
            for key in section['keys']}
    entry = next((dish for dish in payload['dishes'] if dish['key'] == 'nectar' and dish['key'] in keys), None)
    problems = finish(page, errors, [])
    if problems:
        return problems
    if entry is None:
        return ['F24 requires the live batch-3 nectar entry in the not_food section']
    slug = re.sub(r'[^a-z0-9]+', '-', entry['key'].lower()).strip('-')
    for lang in ('zh', 'en'):
        for fly in ('female', 'male', 'both'):
            for mode in ('ask', 'opposite'):
                page, errors, _ = open_page(browser,
                    f'?d={quote(slug)},pizza&lang={lang}&f={fly}&m={mode}', width=390)
                label = f'{lang}/{fly}/{mode}'
                count = 2 if fly == 'both' else 1
                page.wait_for_function('''count => document.querySelectorAll(
                    '.scene-panel:not([hidden]) .plate-label .not-food-badge').length === count''', arg=count)
                page.locator('.scene-panel:visible [data-panel="skip-btn"]').first.click()
                wait_result(page)
                page.locator('#details').evaluate('el => el.open = true')
                expected = page.evaluate("async lang => (await import('./strings.js')).STRINGS[lang].notFood", lang)
                for badge in page.locator('.scene-panel:visible .plate-label .not-food-badge').all():
                    if badge.inner_text() != expected['badge']:
                        problems.append(f'{label}: wrong scene badge')
                    if not badge.evaluate('b => b.scrollWidth <= b.clientWidth'):
                        problems.append(f'{label}: clipped scene badge')
                for selector in ('#result-panel tbody .not-food-note:visible',
                                 '#result-panel .result-hero-notes .not-food-note:visible'):
                    notes = page.locator(selector)
                    if notes.count() != count or any(expected['note'] not in n.inner_text() for n in notes.all()):
                        problems.append(f'{label}: missing result note at {selector}')
                # Language changes must update existing labels and result notes.
                other = 'en' if lang == 'zh' else 'zh'
                page.click('#lang-toggle')
                translated = page.evaluate("async lang => (await import('./strings.js')).STRINGS[lang].notFood", other)
                if any(b.inner_text() != translated['badge'] for b in page.locator('.scene-panel:visible .not-food-badge').all()):
                    problems.append(f'{label}: scene badge did not translate')
                for selector in ('#result-panel tbody .not-food-note:visible',
                                 '#result-panel .result-hero-notes .not-food-note:visible'):
                    notes = page.locator(selector)
                    if notes.count() != count or any(translated['note'] not in n.inner_text() for n in notes.all()):
                        problems.append(f'{label}: result note did not translate at {selector}')
                page.click('#again-btn')
                page.click('#view-all-btn')
                page.fill('#library-search', entry['display'][other])
                tile = page.locator(f'#library-grid .tile[data-key="{entry["key"]}"]')
                if tile.count() != 1 or tile.locator('.not-food-badge').inner_text() != translated['badge']:
                    problems.append(f'{label}: library tile badge absent')
                problems = finish(page, errors, problems)
    return problems


def check_F25(browser):
    """Bilingual menu list parts fit the reference phone viewport with self-attribution."""
    from urllib.parse import urlparse
    problems = []
    for lang in ('zh', 'en'):
        page, errors, requests = open_page(browser, f'menu/?lang={lang}', width=390)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.wait_for_selector('#female-top .menu-row')
        blocks = page.locator('#lists > .menu-block')
        if blocks.count() < 7:
            problems.append(f'{lang}: missing list blocks')
        version = page.evaluate("async () => (await (await fetch('../data/release.json')).json()).version")
        for info in blocks.evaluate_all("""xs => xs.map(x => ({id:x.id,height:x.getBoundingClientRect().height,
          header:x.querySelector('.attribution')?.textContent,title:x.querySelector('h2')?.textContent}))"""):
            if info['height'] > 844:
                problems.append(f"{lang}: {info['id']} height {info['height']}")
            if 'askthefly.app' not in info['header'] or version not in info['header']:
                problems.append(f"{lang}: {info['id']} missing attribution")
        if page.evaluate('document.documentElement.scrollWidth') > 390:
            problems.append(f'{lang}: horizontal scroll')
        icon_errors = page.evaluate("""async () => {
          const data = await (await fetch('../data/menu.json')).json();
          const dishes = new Map(data.dishes.map(d => [d.key, d]));
          const frame = {eats:3,mouth_moves:3,proboscis_only:3,no_response:1};
          const errors = [], seen = new Map();
          for (const icon of document.querySelectorAll('#lists .state-icon')) {
            if (!icon.complete || icon.naturalWidth <= 0) errors.push('unloaded icon: ' + icon.src);
          }
          for (const row of document.querySelectorAll('#lists .menu-row[data-key]')) {
            for (const icon of row.querySelectorAll('.state-icon')) {
              const fly = icon.closest('[data-fly]')?.dataset.fly ||
                (row.closest('[id^="male"], [id^="not-food-male"]') ? 'male' : 'female');
              const state = dishes.get(row.dataset.key)[fly].state;
              const expected = '/assets/' + (fly === 'male' ? 'response_male/' : 'response/') +
                'inset_' + state + '_' + frame[state] + '.png';
              if (!icon.src.endsWith(expected)) errors.push(row.dataset.key + ':' + fly + ': wrong icon');
              if (!icon.complete || icon.naturalWidth <= 0) errors.push(row.dataset.key + ':' + fly + ': unloaded icon');
              seen.set(fly + ':' + state, icon.src);
            }
          }
          for (const [a, srcA] of seen) for (const [b, srcB] of seen) {
            if (a.split(':')[1] !== b.split(':')[1] && srcA === srcB) errors.push(a + '/' + b + ': shared icon');
          }
          return errors;
        }""")
        problems.extend(f'{lang}: {item}' for item in icon_errors)
        for anchor in ('female-top','male-top','divergence','not-food-female','not-food-male','section-tops-female','section-tops-male','all'):
            page.goto(BASE + 'menu/?lang=' + lang + '#' + anchor, wait_until='networkidle')
            top = page.locator('#'+anchor).evaluate('x => x.getBoundingClientRect().top')
            if not -1 <= top <= 2:
                problems.append(f'{lang}: anchor {anchor} at {top}')
        if any(urlparse(url).netloc != urlparse(BASE).netloc for url in requests):
            problems.append(f'{lang}: non-self request')
        problems = finish(page, errors, problems)
    return problems


def check_F26(browser):
    """Numbers, filters, sorting, search and both per-fly row links work."""
    problems = []
    page, errors, requests = open_page(browser, 'menu/?lang=en', width=390)
    page.wait_for_selector('#female-top .menu-row')
    if page.locator('#female-top .numbers:visible').count():
        problems.append('numbers visible by default')
    page.click('#numbers-toggle')
    if not page.locator('#female-top .numbers:visible').count():
        problems.append('numbers toggle did not show values')
    page.click('#numbers-toggle')
    if page.locator('#female-top .numbers:visible').count():
        problems.append('numbers toggle did not hide values')
    if page.locator('#table-rows .table-row').count() != 279:
        problems.append('full table missing rows')
    page.select_option('#section-filter', '0')
    expected = page.evaluate("async () => (await (await fetch('../data/sections.json')).json()).sections[0].keys.length")
    if page.locator('#table-rows .table-row').count() != expected:
        problems.append('section filter count')
    page.select_option('#section-filter', 'all')
    first_female = page.locator('#table-rows .table-row').first.get_attribute('data-key')
    page.select_option('#table-sort', 'male')
    first_male = page.locator('#table-rows .table-row').first.get_attribute('data-key')
    if first_female == first_male:
        problems.append('sort did not change leading dish')
    page.fill('#table-search', 'nectar')
    if page.locator('#table-rows .table-row').count() != 1:
        problems.append('search count')
    page.locator('#table-rows .table-row a[data-fly="male"]').click()
    page.wait_for_selector('#option-list li')
    if 'nectar' not in page.locator('#option-list').inner_text().lower():
        problems.append('link did not prefill dish')
    if not page.locator('input[name="fly"][value="male"]').is_checked():
        problems.append('link did not select male')
    if not page.url.endswith('f=male'):
        problems.append('wrong per-fly link')
    problems = finish(page, errors, problems)
    return problems


def check_F27(browser):
    """Share format changes dimensions and is remembered when the dialog is reopened."""
    problems = []
    page, errors, requests = open_page(browser, '?v=2&d=k.nectar,k.steak&lang=zh', width=390)
    page.wait_for_selector('#scene-panel:not([hidden])')
    page.click('#skip-btn')
    page.wait_for_selector('#result-panel:not([hidden])')
    page.click('#share-btn')
    page.wait_for_selector('#card-dialog[open]')
    if page.locator('#share-card').evaluate('x => [x.width,x.height]') != [900,1200]:
        problems.append('standard card is not default')
    page.check('input[name="card-format"][value="xhs"]')
    page.wait_for_selector('#download-link[href]')
    if page.locator('#share-card').evaluate('x => [x.width,x.height]') != [1080,1440]:
        problems.append('xhs card dimensions')
    page.check('input[name="card-format"][value="standard"]')
    page.wait_for_selector('#download-link[href]')
    if page.locator('#share-card').evaluate('x => [x.width,x.height]') != [900,1200]:
        problems.append('standard card did not return')
    # The chosen format is kept for the rest of the visit.
    page.check('input[name="card-format"][value="xhs"]')
    page.wait_for_selector('#download-link[href]')
    page.click('#close-card-btn')
    page.click('#share-btn')
    page.wait_for_selector('#card-dialog[open]')
    page.wait_for_selector('#download-link[href]')
    if not page.locator('input[name="card-format"][value="xhs"]').is_checked():
        problems.append('reopened dialog forgot the chosen format')
    if page.locator('#share-card').evaluate('x => [x.width,x.height]') != [1080,1440]:
        problems.append('reopened dialog did not draw the chosen format')
    problems = finish(page, errors, problems)
    return problems


def check_F28(browser):
    """First visit on a phone: example set, disabled ask with a hint, no keyboard on View all,
    sticky ask bar while browsing, and the result in view when the run ends."""
    problems = []
    context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, bypass_csp=True)
    page = context.new_page()
    page.add_init_script(INIT)
    errors = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    page.goto(BASE + '?lang=en', wait_until="domcontentloaded")
    page.wait_for_function("window.__askfly && !document.getElementById('example-btn').hidden")
    strings = page.evaluate("import('./strings.js').then(m => ({hint: m.STRINGS.en.hint, one: m.STRINGS.en.hintOneMore}))")
    if not page.locator('#ask-btn').is_disabled() or not page.locator('#opposite-btn').is_disabled():
        problems.append('ask buttons enabled on an empty table')
    if page.locator('#table-empty').inner_text() != strings['hint']:
        problems.append('empty-table hint missing')
    page.fill('#option-input', 'watermelon')
    page.keyboard.press('Enter')
    page.wait_for_function("window.__askfly.snapshot().options.length === 1")
    if not page.locator('#ask-btn').is_disabled() or not page.locator('#opposite-btn').is_disabled():
        problems.append('an ask button is enabled with one dish')
    if page.locator('#table-empty').inner_text() != strings['one'] or not page.locator('#table-empty').is_visible():
        problems.append('one-more hint not shown with one dish')
    if page.locator('#example-btn').is_visible():
        problems.append('example button still visible with a dish on the table')
    # The full list makes the page long enough for the ask button to leave the view.
    page.locator('#view-all-btn').tap()
    page.wait_for_selector('#library-panel:not([hidden])')
    if page.evaluate("document.activeElement && document.activeElement.id") == 'library-search':
        problems.append('View all focused the search box on a touch screen')
    if page.locator('#sticky-bar').is_visible():
        problems.append('sticky bar shown while the ask button is in view')
    page.evaluate("document.getElementById('library-grid').scrollIntoView(); window.scrollBy(0, 600)")
    page.wait_for_selector('#sticky-bar:not([hidden])')
    sticky = page.locator('#sticky-count').inner_text()
    if '1' not in sticky or not page.locator('#sticky-ask').is_disabled():
        problems.append(f'one-entry sticky bar: {sticky!r}, ask disabled = {page.locator("#sticky-ask").is_disabled()}')
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_selector('#sticky-bar', state='hidden')
    page.locator('#option-list button').first.click()
    page.locator('#example-btn').tap()
    page.wait_for_function("window.__askfly.snapshot().options.length >= 2")
    if page.locator('#ask-btn').is_disabled():
        problems.append('ask disabled after the example set')
    if page.locator('#table-empty').is_visible():
        problems.append('hint still shown with two or more dishes')
    page.evaluate("document.getElementById('library-grid').scrollIntoView(); window.scrollBy(0, 600)")
    page.wait_for_selector('#sticky-bar:not([hidden])')
    if page.locator('#sticky-ask').is_disabled():
        problems.append('sticky ask disabled with two or more dishes')
    page.locator('#sticky-ask').tap()
    page.wait_for_function("window.__askfly.snapshot().phase === 'tasting'")
    if page.locator('#sticky-bar').is_visible():
        problems.append('sticky bar still shown during tasting')
    page.click('#skip-btn')
    wait_result(page)
    page.wait_for_timeout(1200)
    box = page.evaluate("(() => { const r = document.getElementById('verdict').getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; })()")
    if not (box[0] >= 0 and box[1] <= box[2]):
        problems.append(f'verdict not in view after the run: {box}')
    problems = finish(page, errors, problems)
    context.close()
    return problems


XHS_BOUNDS = """
(() => {
  const original = CanvasRenderingContext2D.prototype.fillText;
  window.__xhsText = [];
  CanvasRenderingContext2D.prototype.fillText = function(text, x, y, ...rest) {
    if (this.canvas.id === 'share-card') {
      const m = this.measureText(String(text));
      const left = this.textAlign === 'center' ? x - m.width / 2 : this.textAlign === 'right' ? x - m.width : x;
      window.__xhsText.push({text: String(text), left, right: left + m.width, top: y - m.actualBoundingBoxAscent, bottom: y + m.actualBoundingBoxDescent});
    }
    return original.call(this, text, x, y, ...rest);
  };
})();
"""


def check_F29(browser):
    """Xiaohongshu card: no text overlaps other text or comes within 14 px of the footer rule, with the
    longest names in the dictionary, in both languages, for one fly and for both."""
    problems = []
    cases = [
        ('en', 'female', 'latiao,hot-and-sour-noodles,xiaolongbao,pickled-cabbage-fish'),
        ('en', 'both', 'latiao,hot-and-sour-noodles,xiaolongbao'),
        ('en', 'both', 'pickled-cabbage-fish,xiaolongbao'),
        ('zh', 'female', 'injera,goulash,gnocchi,watermelon,honey'),
        ('zh', 'both', 'injera,goulash,gnocchi,pickled-cabbage-fish,xiaolongbao'),
        ('zh', 'male', 'hot-and-sour-noodles,injera,goulash'),
        ('zh', 'female', 'cake,donut,steak'),                                   # two tied winners
        ('en', 'female', 'apple-pie,cake,churros,steak'),                       # three tied winners
        ('en', 'female', 'zz-not-a-dish-one,zz-not-a-dish-two'),                # nothing known: the headline wraps
        ('en', 'female', 'nectar,honey,steak,watermelon,pizza&m=opposite'),     # the fly keeps one, several remain
        ('en', 'both', 'latiao,hot-and-sour-noodles,xiaolongbao,pickled-cabbage-fish,injera,goulash,gnocchi,samgyetang,borscht,clam-chowder&m=opposite'),
    ]
    for lang, fly, dishes in cases:
        page = browser.new_page(viewport={"width": 390, "height": 900}, bypass_csp=True)
        page.add_init_script(INIT)
        page.add_init_script(XHS_BOUNDS)
        errors = []
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        dishes, _, extra = dishes.partition('&')
        query = '?v=2&d=' + ','.join(('t.' if d.startswith('zz-') else 'k.') + d for d in dishes.split(',')) + f'&lang={lang}&seed=0' + ('' if fly == 'female' else f'&f={fly}') + ('&' + extra if extra else '')
        page.goto(BASE + query, wait_until="domcontentloaded")
        page.wait_for_function("window.__askfly && window.__askfly.snapshot().phase !== 'input'")
        for selector in ('#skip-btn', '#skip-btn-male'):
            if page.locator(selector).is_visible():
                page.click(selector)
        wait_result(page)
        page.click('#share-btn')
        page.wait_for_selector('#card-dialog[open]')
        page.wait_for_function("Boolean(document.getElementById('download-link').href) || !document.getElementById('save-btn').hidden")
        page.evaluate("window.__xhsText = []")
        page.check('input[name="card-format"][value="xhs"]')
        page.wait_for_function("document.getElementById('share-card').width === 1080 && window.__xhsText.length > 3")
        page.wait_for_timeout(600)
        # The picture must also have been prepared for saving, not only drawn.
        if not page.evaluate("Boolean(document.getElementById('download-link').href) || !document.getElementById('save-btn').hidden"):
            problems.append(f'{lang}/{fly}/{dishes}: no saved image was prepared')
        boxes = page.evaluate("window.__xhsText")
        label = f'{lang}/{fly}/{dishes}'
        if any(box['text'].endswith('…') for box in boxes) and 'zz-' in dishes:
            problems.append(f'{label}: the headline was cut instead of wrapped')
        for box in boxes:
            if box['left'] < 0 or box['right'] > 1080 or box['top'] < 0 or box['bottom'] > 1440:
                problems.append(f"{label}: text outside the card: {box['text']!r}")
            # Text above the footer rule (y = 1195) keeps a clear margin from it.
            if box['top'] < 1195 and box['bottom'] >= 1195 - 14:
                problems.append(f"{label}: text touches or crosses the footer rule: {box['text']!r} (bottom {box['bottom']:.0f})")
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                if a['left'] < b['right'] - 1 and b['left'] < a['right'] - 1 and a['top'] < b['bottom'] - 1 and b['top'] < a['bottom'] - 1:
                    problems.append(f"{label}: text overlaps: {a['text']!r} / {b['text']!r}")
        if errors:
            problems.append(f"{label}: {errors}")
        page.close()
    return problems



def check_F30(browser):
    """Both flies on a phone play in turn; Skip during the first fly's turn still leaves the
    second fly's stage laid out with its final state, and the result is shown."""
    problems = []
    page, errors, requests = open_page(browser, '?v=2&d=k.pickled-cabbage-fish,k.xiaolongbao&lang=en&seed=0&f=both', width=390)
    page.wait_for_function("window.__askfly && window.__askfly.snapshot().phase === 'tasting'")
    page.wait_for_function("window.__askfly.snapshot().panels.female.sceneRunning")
    if debug(page)['panels']['male']['sceneRunning']:
        problems.append('the male fly started while the female fly was still playing on a stacked layout')
    page.click('#skip-btn')
    wait_result(page)
    page.wait_for_timeout(2500)
    state = page.evaluate("""(() => {
      const male = document.getElementById('scene-panel-male');
      const status = male.querySelector('[data-panel="scene-status"]');
      const detail = male.querySelector('[data-panel="response-detail"]');
      return {phase: window.__askfly.snapshot().phase, status: status ? status.textContent.trim() : null,
              plates: male.querySelectorAll('.plate-label').length,
              detailHidden: detail ? detail.hidden : true, running: window.__askfly.snapshot().panels.male.brainPlaying};
    })()""")
    if state['phase'] != 'result':
        problems.append(f"phase after skip: {state['phase']}")
    if not state['status']:
        problems.append('the male stage has no final status after a skip before its turn')
    if state['plates'] != 2:
        problems.append(f"the male stage has {state['plates']} plate labels after a skip before its turn, expected 2")
    if state['detailHidden']:
        problems.append('the male final response is hidden after a skip before its turn')
    if state['running']:
        problems.append('the male replay is still playing after skip')
    box = page.evaluate("(() => { const r = document.getElementById('verdict').getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; })()")
    if not (box[0] >= 0 and box[1] <= box[2]):
        problems.append(f'verdict not in view after skip: {box}')
    problems = finish(page, errors, problems)
    return problems



def check_F31(browser):
    """Guess before the reveal: the table waits for a tap, only scored plates can be tapped,
    the result says right or wrong, the count stays in the page, the card carries one line,
    Skip and "Just watch" leave no trace of a guess, and a shared link invites a guess."""
    problems = []
    manual = "window.__guess = 'manual'"

    def open_manual(query, width=390):
        page, errors, requests = open_page(browser, query, width=width, init=manual)
        page.wait_for_function("window.__askfly && window.__askfly.snapshot().phase === 'guess'")
        page.wait_for_selector('.plate-guess')
        return page, errors, requests

    def guess_state(page):
        return page.evaluate("""(() => {
          const line = document.getElementById('guess-result'), tally = document.getElementById('guess-tally');
          return {hidden: line.hidden, text: line.textContent, right: line.classList.contains('right'),
                  tallyHidden: tally.hidden, tally: tally.textContent, snap: window.__askfly.snapshot()};
        })()""")

    # A shared link: the recipient is invited to guess; nothing plays until they choose.
    page, errors, requests = open_manual('?v=2&d=k.watermelon,k.mapo-tofu,k.black-coffee,t.zz-not-a-dish&lang=en&seed=0')
    page.wait_for_timeout(1200)
    snap = debug(page)
    if snap['phase'] != 'guess' or snap['brainPlaying']:
        problems.append(f"the run started without a choice: {snap['phase']}, brain playing = {snap['brainPlaying']}")
    if page.locator('.plate-guess').count() != 3:
        problems.append(f"{page.locator('.plate-guess').count()} tap targets for three scored dishes and one unknown entry")
    if not page.locator('#result-panel').is_hidden() or page.locator('#scene-panel .brain-wrap').is_visible():
        problems.append('result or brain shown during the guess step')
    if page.locator('#scene-status').inner_text() != STRINGS_EN_SHARED:
        problems.append(f"shared-link caption: {page.locator('#scene-status').inner_text()!r}")
    boxes = page.evaluate("[...document.querySelectorAll('.plate-guess')].map(b => { const r = b.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })")
    for i, a in enumerate(boxes):
        if a[2] - a[0] < 44 or a[3] - a[1] < 44:
            problems.append(f'tap target {i} smaller than 44 px: {a}')
        for c in boxes[i + 1:]:
            if a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]:
                problems.append(f'tap targets overlap: {a} {c}')
    # A narrower window, then the language switch: the step stays and the targets stay on their plates.
    page.set_viewport_size({'width': 360, 'height': 900})
    page.click('#lang-toggle')
    if debug(page)['phase'] != 'guess' or page.locator('.plate-guess').count() != 3:
        problems.append('the language switch ended the guess step')
    off = page.evaluate("""(() => {
      const buttons = [...document.querySelectorAll('.plate-guess')].map(b => b.getBoundingClientRect());
      const labels = [...document.querySelectorAll('#scene-panel .plate-label')].slice(0, 3).map(b => b.getBoundingClientRect());
      const stage = document.getElementById('scene-canvas').getBoundingClientRect();
      return buttons.map((b, i) => [Math.abs((b.left + b.right) / 2 - (labels[i].left + labels[i].right) / 2), b.left >= stage.left - 1 && b.right <= stage.right + 1]);
    })()""")
    if any(distance > 2 or not inside for distance, inside in off):
        problems.append(f'tap targets off their plates after a resize and a language switch: {off}')
    page.click('#lang-toggle')
    page.set_viewport_size({'width': 390, 'height': 900})
    # A wrong guess (black coffee is the third scored plate; the female fly takes watermelon).
    page.locator('.plate-guess').nth(2).click()
    page.wait_for_function("window.__askfly.snapshot().phase === 'tasting'")
    page.wait_for_selector('.plate-tag')
    if page.locator('.plate-guess').count() or page.locator('[data-panel="guess-watch"]:visible').count():
        problems.append('guess controls still shown while the fly tastes')
    page.click('#skip-btn')
    wait_result(page)
    state = guess_state(page)
    if state['hidden'] or state['right'] or 'black coffee' not in state['text'] or state['snap']['tally'] != {'right': 0, 'total': 1}:
        problems.append(f"wrong guess: {state['text']!r}, right = {state['right']}, tally = {state['snap']['tally']}")
    # The card carries the line at the right of its title row.
    page.evaluate("""(() => {
      window.__cardText = [];
      const fill = CanvasRenderingContext2D.prototype.fillText;
      CanvasRenderingContext2D.prototype.fillText = function (text, x, y, ...rest) {
        if (this.canvas.id === 'share-card') window.__cardText.push({text: String(text), x, y, width: this.measureText(String(text)).width, align: this.textAlign});
        return fill.call(this, text, x, y, ...rest);
      };
    })()""")
    page.click('#share-btn')
    page.wait_for_selector('#card-dialog[open]')
    for card_format, title_y in (('xhs', 84), ('standard', 108)):  # the dialog opens on the standard card
        page.evaluate("window.__cardText = []")
        page.check(f'input[name="card-format"][value="{card_format}"]', force=True)
        page.wait_for_function("window.__cardText.length > 3")
        page.wait_for_timeout(500)
        texts = page.evaluate("window.__cardText")
        line = [t for t in texts if 'black coffee' in t['text'] and t['align'] == 'right']
        title = [t for t in texts if t['y'] == title_y and t['align'] != 'right']
        if len(line) != 1 or not title:
            problems.append(f'{card_format} card: guess line drawn {len(line)} times')
        elif line[0]['x'] - line[0]['width'] < title[0]['x'] + title[0]['width'] + 20:
            problems.append(f'{card_format} card: the guess line runs into the title')
    page.click('#close-card-btn')
    # Play again with a right guess: the count shows by the table title and after the line.
    page.click('#again-btn')
    if guess_state(page)['tallyHidden']:
        problems.append('the count is not shown by the table title after a guess')
    page.click('#ask-btn')
    page.wait_for_selector('.plate-guess')
    if page.locator('#scene-status').inner_text() == STRINGS_EN_SHARED:
        problems.append('the shared-link caption was used for an ordinary run')
    page.locator('.plate-guess').nth(0).click()
    page.wait_for_function("window.__askfly.snapshot().phase === 'tasting'")
    page.click('#skip-btn')
    wait_result(page)
    state = guess_state(page)
    if state['hidden'] or not state['right'] or state['snap']['tally'] != {'right': 1, 'total': 2} or '1 / 2' not in state['text']:
        problems.append(f"right guess: {state['text']!r}, right = {state['right']}, tally = {state['snap']['tally']}")
    # "Just watch" and Skip: no guess, no line, the count unchanged.
    for control in ('[data-panel="guess-watch"]:visible', '#skip-btn'):
        page.click('#again-btn')
        page.click('#ask-btn')
        page.wait_for_selector('.plate-guess')
        page.click(control)
        if control != '#skip-btn':
            page.wait_for_function("window.__askfly.snapshot().phase === 'tasting'")
            page.click('#skip-btn')
        wait_result(page)
        state = guess_state(page)
        if not state['hidden'] or state['snap']['guess'] is not None or state['snap']['tally'] != {'right': 1, 'total': 2}:
            problems.append(f"{control}: a guess was recorded: {state['text']!r}, {state['snap']['guess']}, {state['snap']['tally']}")
        if page.locator('.plate-tag').count():
            problems.append(f'{control}: a plate is tagged without a guess')
        if page.locator('#option-list li').count() and not page.locator('#results-body tr').count():
            problems.append(f'{control}: the result table is empty')
    # "Ask again" during a later run's guess step must not be undone by the earlier one.
    page.click('#again-btn')
    page.click('#ask-btn')
    page.wait_for_selector('.plate-guess')
    snap = debug(page)
    if snap['phase'] != 'guess' or snap['guess'] is not None or page.locator('.plate-tag').count():
        problems.append(f"a new run started with an old guess: {snap['phase']}, {snap['guess']}")
    problems = finish(page, errors, problems)

    # Skip while the plates' pictures are still held back: the result comes at once.
    page = browser.new_page(viewport={"width": 390, "height": 900}, bypass_csp=True)
    page.add_init_script(INIT + manual)
    errors = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    hold = Hold(page, "**/assets/dishes/mapo-tofu.png")
    page.goto(BASE + '?v=2&d=k.watermelon,k.mapo-tofu,k.black-coffee&lang=en&seed=0', wait_until="domcontentloaded")
    page.wait_for_function("window.__askfly && window.__askfly.snapshot().phase === 'guess'")
    for _ in range(100):
        if hold.routes:
            break
        page.wait_for_timeout(50)
    else:
        problems.append('the held plate picture was never requested: the Skip case below proves nothing')
    page.click('#skip-btn')
    try:
        wait_result(page, timeout=5000)
    except Exception:
        problems.append('Skip during the guess step waited for the plate pictures')
    hold.release()
    page.wait_for_timeout(800)
    state = guess_state(page)
    if state['snap']['phase'] != 'result' or not state['hidden'] or page.locator('.plate-guess').count():
        problems.append(f"after Skip with held pictures: {state['snap']['phase']}, tap targets = {page.locator('.plate-guess').count()}")
    problems = finish(page, errors, problems)

    # Both flies on a phone: one table to guess on, both stages tagged, one line for both.
    page, errors, requests = open_manual('?v=2&d=k.latiao,k.hot-and-sour-noodles,k.xiaolongbao,k.injera&lang=zh&seed=0&f=both')
    if page.locator('#scene-panel-male').is_visible():
        problems.append('two tables shown during the guess step with both flies')
    page.locator('.plate-guess').nth(0).click()   # latiao: the female fly's pick, not the male fly's
    page.wait_for_function("window.__askfly.snapshot().phase === 'tasting'")
    page.wait_for_selector('#scene-panel .plate-tag')
    page.click('#skip-btn')
    wait_result(page)
    page.wait_for_timeout(1500)
    stages = page.evaluate("""['scene-panel', 'scene-panel-male'].map(id => {
      const root = document.getElementById(id);
      return [root.querySelectorAll('.plate-label').length, root.querySelectorAll('.plate-tag').length, root.querySelectorAll('.plate-guess').length];
    })""")
    if stages != [[4, 1, 0], [4, 1, 0]]:
        problems.append(f'both flies after a guess and Skip: [labels, tags, tap targets] per stage = {stages}')
    state = guess_state(page)
    expected = page.evaluate("import('./strings.js').then(m => m.STRINGS.zh.guess.resultOneFly.replace('{hit}', m.STRINGS.zh.flyName.female).replace('{miss}', m.STRINGS.zh.flyName.male))")
    if state['text'] != expected or state['right'] or state['snap']['tally'] != {'right': 0, 'total': 1}:
        problems.append(f"both flies, right for one: {state['text']!r} (expected {expected!r}), tally = {state['snap']['tally']}")
    problems = finish(page, errors, problems)

    # Fewer than two scored dishes: no guess step at all.
    page, errors, requests = open_page(browser, '?v=2&d=k.watermelon,t.zz-not-a-dish&lang=en&seed=0', init=manual)
    page.wait_for_function("window.__askfly && window.__askfly.snapshot().phase === 'tasting'")
    if page.locator('.plate-guess').count():
        problems.append('a guess was offered with one scored dish')
    problems = finish(page, errors, problems)
    return problems



def check_F32(browser):
    """Standard share card: the tablecloth patch behind the picture never covers the
    name above it, with the longest names, a tie, the male fly and "Let the fly eat first"."""
    problems = []
    cases = [
        ('en', 'female', 'xiaolongbao,hot-and-sour-noodles'),
        ('en', 'male', 'xiaolongbao,hot-and-sour-noodles'),
        ('en', 'female', 'pickled-cabbage-fish,latiao,injera'),
        ('zh', 'female', 'hot-and-sour-noodles,injera,goulash'),
        ('en', 'female', 'cake,donut,steak'),                              # two tied winners
        ('en', 'female', 'apple-pie,cake,churros,steak'),                  # three tied winners
        ('en', 'female', 'pickled-cabbage-fish,xiaolongbao&m=opposite'),
        ('en', 'female', 'nectar,honey,steak,watermelon,pizza&m=opposite'),
    ]
    for lang, fly, dishes in cases:
        dishes, _, extra = dishes.partition('&')
        query = '?v=2&d=' + ','.join('k.' + d for d in dishes.split(',')) + f'&lang={lang}&seed=0' + ('' if fly == 'female' else f'&f={fly}') + ('&' + extra if extra else '')
        page, errors, requests = open_page(browser, query)
        page.wait_for_function("window.__askfly && ['guess', 'tasting'].includes(window.__askfly.snapshot().phase)")
        page.click('#skip-btn')
        wait_result(page)
        page.evaluate("""(() => {
          window.__card = {text: [], patch: [], order: 0};
          const proto = CanvasRenderingContext2D.prototype, fill = proto.fillText, round = proto.roundRect;
          proto.fillText = function (text, x, y, ...rest) {
            if (this.canvas.id === 'share-card') {
              const m = this.measureText(String(text)), left = this.textAlign === 'right' ? x - m.width : this.textAlign === 'center' ? x - m.width / 2 : x;
              window.__card.text.push({order: window.__card.order++, text: String(text), font: this.font, left, right: left + m.width, top: y - m.actualBoundingBoxAscent, bottom: y + m.actualBoundingBoxDescent});
            }
            return fill.call(this, text, x, y, ...rest);
          };
          proto.roundRect = function (x, y, w, h, ...rest) {
            if (this.canvas.id === 'share-card' && w > 150 && h > 100) window.__card.patch.push({order: window.__card.order++, left: x, top: y, right: x + w, bottom: y + h});
            return round.call(this, x, y, w, h, ...rest);
          };
        })()""")
        page.click('#share-btn')
        page.wait_for_selector('#card-dialog[open]')
        page.wait_for_function("document.getElementById('share-card').width === 900 && window.__card.text.length > 3")
        page.wait_for_timeout(500)
        card = page.evaluate("window.__card")
        label = f'{lang}/{fly}/{dishes}' + (f'/{extra}' if extra else '')
        # A crowded card has no large picture and so no patch; never more than one.
        if len(card['patch']) > 1 or (not card['patch'] and len(dishes.split(',')) < 4):
            problems.append(f"{label}: {len(card['patch'])} tablecloth patches found")
        for patch in card['patch']:
            for text in card['text']:
                if text['order'] > patch['order']:
                    continue  # drawn on the patch on purpose (the fly's own dish in "eat first")
                if text['left'] < patch['right'] and patch['left'] < text['right'] and text['top'] < patch['bottom'] and patch['top'] < text['bottom']:
                    problems.append(f"{label}: the tablecloth covers {text['text']!r} ({text['top']:.0f}-{text['bottom']:.0f} against a patch from {patch['top']:.0f})")
        problems = finish(page, errors, problems)
    return problems


STRINGS_EN_SHARED = "Table's set. Tap to guess"


CHECKS = {
    "F02": check_F02, "F03": check_F03, "F04": check_F04, "F05": check_F05,
    "F06": check_F06, "F08": check_F08, "F15": check_F15,
    "F16": check_F16, "F17": check_F17, "F18": check_F18,
    "F19": check_F19, "F20": check_F20,
    "F21": check_F21,
    "F22": check_F22,
    "F23": check_F23, "F24": check_F24,
    "F25": check_F25, "F26": check_F26, "F27": check_F27,
    "F28": check_F28, "F29": check_F29, "F30": check_F30, "F31": check_F31, "F32": check_F32,
}


def main() -> int:
    from playwright.sync_api import sync_playwright

    global BASE
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="comma-separated ticket ids")
    parser.add_argument("--base", default=BASE)
    args = parser.parse_args()
    BASE = args.base
    wanted = [w.strip() for w in args.only.split(",")] if args.only else list(CHECKS)
    failed = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for ticket in wanted:
            started = time.perf_counter()
            try:
                problems = CHECKS[ticket](browser)
            except Exception as exc:  # noqa: BLE001 - report, do not hide
                problems = [f"check raised: {type(exc).__name__}: {exc}"]
            status = "SKIP" if problems is None else "PASS" if not problems else "FAIL"
            failed += bool(problems)
            print(f"{ticket} {status} ({time.perf_counter() - started:.1f}s)")
            for problem in problems or []:
                print(f"    - {problem}")
        browser.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
