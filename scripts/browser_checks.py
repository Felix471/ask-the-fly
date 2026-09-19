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

BASE = "http://127.0.0.1:8765/"
INIT = """
window.__rejections = [];
window.addEventListener('unhandledrejection', (e) => window.__rejections.push(String(e.reason)));
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


def open_page(browser, query, width=390):
    # bypass_csp: the page's CSP (verified separately) would block Playwright's evaluated predicates
    page = browser.new_page(viewport={"width": width, "height": 900}, bypass_csp=True)
    page.add_init_script(INIT)
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


CHECKS = {
    "F02": check_F02, "F03": check_F03, "F04": check_F04, "F05": check_F05,
    "F06": check_F06, "F08": check_F08, "F15": check_F15,
    "F16": check_F16, "F17": check_F17, "F18": check_F18,
    "F19": check_F19, "F20": check_F20,
    "F21": check_F21,
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
            status = "PASS" if not problems else "FAIL"
            failed += bool(problems)
            print(f"{ticket} {status} ({time.perf_counter() - started:.1f}s)")
            for problem in problems:
                print(f"    - {problem}")
        browser.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
