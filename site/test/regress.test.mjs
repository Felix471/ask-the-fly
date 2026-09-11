// Regression tests for the audit tickets (baseline cfb1864). One block per ticket.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const replayDir = path.join(here, "..", "data", "replay");

function replayBytes(cellId) {
  const buf = readFileSync(path.join(replayDir, `${cellId}.bin`));
  return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
}

// A fetch stub with a scripted response per request, counting requests.
function fetchScript(responses) {
  const calls = [];
  const fetch = async (url) => {
    calls.push(url);
    const next = responses.shift();
    if (typeof next === "function") return next(url);
    return next;
  };
  return { fetch, calls };
}
const ok = (bytes) => ({ ok: true, status: 200, arrayBuffer: async () => bytes });
const fail = (status) => ({ ok: false, status, arrayBuffer: async () => new ArrayBuffer(0) });

// ---- F01: a failed replay request must not be cached; in-flight dedupe stays ----
import { makeReplayLoader } from "../brain.js";

test("F01: first 503 then success -> two requests, second succeeds", async () => {
  const cell = "G_slow_bnone_whigh_inone";
  const { fetch, calls } = fetchScript([fail(503), ok(replayBytes(cell))]);
  const load = makeReplayLoader("data/replay/", fetch);
  await assert.rejects(load(cell), /HTTP 503/);
  const replay = await load(cell);
  assert.equal(replay.header.cell_id, cell);
  assert.equal(calls.length, 2, "the failure was not cached");
  await load(cell);
  assert.equal(calls.length, 2, "success stays cached");
});

test("F01: concurrent identical requests share one fetch; variants are separate keys", async () => {
  const cell = "G_slow_bnone_whigh_inone";
  const { fetch, calls } = fetchScript([ok(replayBytes(cell)), ok(replayBytes(`${cell}_silence_clavicle`))]);
  const load = makeReplayLoader("data/replay/", fetch);
  const [a, b] = await Promise.all([load(cell), load(cell)]);
  assert.equal(a, b);
  assert.equal(calls.length, 1);
  const v = await load(cell, "clavicle");
  assert.notEqual(v, a);
  assert.equal(calls.length, 2);
});

test("F01: a parse failure (bad magic) is retried on the next call", async () => {
  const cell = "G_slow_bnone_whigh_inone";
  const junk = new Uint8Array([1, 2, 3, 4, 0, 0, 0, 0]).buffer;
  const { fetch, calls } = fetchScript([ok(junk), ok(replayBytes(cell))]);
  const load = makeReplayLoader("data/replay/", fetch);
  await assert.rejects(load(cell), /bad magic/);
  const replay = await load(cell);
  assert.equal(replay.header.cell_id, cell);
  assert.equal(calls.length, 2);
});

// ---- F07: fly ties (max set) and selection ties (human rule) are separate ----
import * as appModule from "../app.js";
const { decide, scoreOptions, buildDictionary, buildLookup } = appModule;

const cellOf = (hz) => ({ mn9_mean: hz, mn9_std: 0, hz: {} });
const item = (name, hz) => ({ name, entry: { key: name, display: { en: name, zh: name } }, cell: cellOf(hz), sugarOnly: cellOf(hz) });
const keys = (list) => list.map((i) => i.name);

test("F07: max unique / min tied, opposite: the fly has no tie; the human's dish is tied", () => {
  const d = decide([item("A", 100), item("B", 0), item("C", 0)], "opposite");
  assert.equal(d.flyPick.name, "A");
  assert.deepEqual(keys(d.flyTies), []);
  assert.deepEqual(keys(d.selectionTies), ["B", "C"]);
  assert.deepEqual(keys(d.tie), ["B", "C"], "tie stays the selection tie for the result and the card");
});

test("F07: max tied / min unique, both modes", () => {
  const scored = [item("A", 100), item("B", 100), item("C", 0)];
  const ask = decide(scored, "ask");
  assert.deepEqual(keys(ask.flyTies), ["A", "B"]);
  assert.deepEqual(keys(ask.selectionTies), ["A", "B"]);
  const opp = decide(scored, "opposite");
  assert.deepEqual(keys(opp.flyTies), ["A", "B"], "the fly's tie is expressed even when the human picks the minimum");
  assert.deepEqual(keys(opp.selectionTies), []);
  assert.equal(opp.winner.name, "C");
});

test("F07: ties at both ends, and all tied", () => {
  const both = decide([item("A", 50), item("B", 50), item("C", 1), item("D", 1)], "opposite");
  assert.deepEqual(keys(both.flyTies), ["A", "B"]);
  assert.deepEqual(keys(both.selectionTies), ["C", "D"]);
  const all = decide([item("A", 5), item("B", 5), item("C", 5)], "ask");
  assert.deepEqual(keys(all.flyTies), ["A", "B", "C"]);
  assert.deepEqual(keys(all.selectionTies), ["A", "B", "C"]);
  const allOpp = decide([item("A", 5), item("B", 5), item("C", 5)], "opposite");
  assert.deepEqual(keys(allOpp.flyTies), ["A", "B", "C"]);
  assert.deepEqual(keys(allOpp.selectionTies), ["A", "B", "C"]);
});

test("F07: no random tie-break: flyPick is the first maximum in input order, stable across calls", () => {
  const scored = [item("B", 100), item("A", 100), item("C", 0)];
  for (let i = 0; i < 5; i += 1) assert.equal(decide(scored, "ask").flyPick.name, "B");
  assert.equal(decide([item("A", 100), item("B", 100)], "ask").flyPick.name, "A");
});

test("F07: the animation plan hovers between the fly's ties, never the human's", () => {
  // scenePlan mirrors runScene's plan construction (exported for this test)
  const { scenePlan } = appModule;
  const d = decide([item("A", 100), item("B", 0), item("C", 0)], "opposite");
  const plan = scenePlan(d, [...d.known, ...d.misses]);
  assert.deepEqual(plan.tie, [], "unique fly maximum: no hover");
  assert.equal(plan.winner, 0, "the fly lands on A");
  const d2 = decide([item("A", 100), item("B", 100), item("C", 0)], "opposite");
  const plan2 = scenePlan(d2, [...d2.known, ...d2.misses]);
  assert.deepEqual(plan2.tie, [0, 1], "fly tie between A and B");
});

test("F07: a real dictionary tie behaves the same through scoreOptions", () => {
  const dishes = JSON.parse(readFileSync(path.join(here, "..", "data", "dishes.json"), "utf8"));
  const table = JSON.parse(readFileSync(path.join(here, "..", "data", "lookup_table.json"), "utf8"));
  const d = decide(scoreOptions(["candy", "honey", "lemon"], buildDictionary(dishes), buildLookup(table)), "opposite");
  assert.deepEqual(d.flyTies.map((i) => i.entry.key), ["candy", "honey"]);
  assert.deepEqual(d.selectionTies, []);
  assert.equal(d.winner.entry.key, "lemon");
});

// ---- F09: playback accumulates simulated time per frame; speed changes never rewind ----
import { createPlayback, advancePlayback } from "../brain.js";

test("F09: 1 -> 0.5 -> 2 -> 1 speed changes keep simulated time monotone", () => {
  const replay = { header: { duration_ms: 1000, mn9_left_ms: [100, 250, 250, 600, 999] } };
  const pb = createPlayback(replay);
  const times = [];
  let counted = 0;
  let finishes = 0;
  const step = (now, speed) => {
    const r = advancePlayback(pb, now, speed);
    times.push(r.tMs);
    counted += r.newSpikes;
    if (r.finished) finishes += 1;
    return r;
  };
  step(0, 1);
  step(500, 1);          // 500 ms simulated
  const r = step(510, 0.5); // the old formula gave (510 - 0) * 0.5 = 255: a rewind
  assert.equal(r.tMs, 505);
  step(600, 2);          // + 90 * 2
  assert.equal(pb.t, 685);
  for (let now = 700; now <= 1200; now += 100) step(now, 1);
  assert.ok(times.every((t, i) => i === 0 || t >= times[i - 1]), `monotone: ${times}`);
  assert.equal(pb.t, 1000, "clamped at the duration");
  assert.equal(counted, 5, "each MN9 spike counted exactly once");
  assert.equal(finishes, 1, "finish reported once");
  assert.equal(advancePlayback(pb, 5000, 1).newSpikes, 0, "nothing after the end");
});

test("F09: the counter and the drawn time come from the same simulated clock", () => {
  const replay = { header: { duration_ms: 100, mn9_left_ms: [10, 20, 30] } };
  const pb = createPlayback(replay);
  advancePlayback(pb, 0, 1);
  const r1 = advancePlayback(pb, 15, 1);
  assert.equal(r1.tMs, 15);
  assert.equal(r1.newSpikes, 1);
  const r2 = advancePlayback(pb, 20, 4); // 15 + 5 * 4 = 35
  assert.equal(r2.tMs, 35);
  assert.equal(r2.newSpikes, 2);
});

// ---- F13: transient sprite failures are not cached as missing; one missing frame falls back to another pixel frame ----
import { loadDishSprite, loadSprites, framesFor } from "../fly.js";

function imageLoader(script) {
  // script: url -> "ok" | "fail" | ["fail", "ok", ...] (per call)
  const calls = [];
  return {
    calls,
    load: async (url) => {
      calls.push(url);
      const plan = script[url] ?? script["*"] ?? "ok";
      const outcome = Array.isArray(plan) ? plan.shift() ?? "ok" : plan;
      return outcome === "ok" ? { src: url, width: 1, height: 1 } : null;
    },
  };
}

test("F13: a dish sprite that fails once loads on the next request; successes stay cached; in-flight shared", async () => {
  const loader = imageLoader({ "assets/dishes/hotpot.png": ["fail", "ok"] });
  const sprites = { fly: {}, dishCache: new Map(), base: "assets/" };
  assert.equal(await loadDishSprite(sprites, "hotpot", loader.load), null);
  assert.equal(sprites.dishCache.has("hotpot"), false, "a failure is not cached as missing");
  const img = await loadDishSprite(sprites, "hotpot", loader.load);
  assert.ok(img, "second request succeeds");
  assert.equal(loader.calls.length, 2);
  const [a, b] = await Promise.all([loadDishSprite(sprites, "hotpot", loader.load), loadDishSprite(sprites, "hotpot", loader.load)]);
  assert.equal(a, b);
  assert.equal(loader.calls.length, 2, "cached after success");
  const s2 = { fly: {}, dishCache: new Map(), base: "assets/" };
  await Promise.all([loadDishSprite(s2, "pho", loader.load), loadDishSprite(s2, "pho", loader.load)]);
  assert.equal(loader.calls.filter((u) => u.endsWith("pho.png")).length, 1, "concurrent requests share one load");
});

test("F13: one missing fly frame keeps the other frames; a missing set falls back to another pixel set", async () => {
  const loader = imageLoader({ "assets/fly/fly_3.png": "fail", "assets/fly/proboscis_1.png": "fail", "assets/fly/proboscis_2.png": "fail", "assets/fly/proboscis_3.png": "fail" });
  const sprites = await loadSprites("assets/", loader.load);
  assert.equal(sprites.fly.fly.length, 3, "three of four wing frames survive");
  assert.equal(sprites.fly.proboscis, null, "no proboscis frames at all");
  assert.equal(framesFor(sprites.fly, "fly").length, 3);
  assert.equal(framesFor(sprites.fly, "proboscis"), sprites.fly.idle, "falls back to idle pixel frames, never the drawn fly");
  assert.equal(framesFor(sprites.fly, "hover"), sprites.fly.idle);
  assert.equal(framesFor({}, "idle"), null, "only when nothing loaded does the drawn fallback apply");
});

// ---- F17: versioned, typed share params; unknown text with separators round-trips; old links still parse ----
import { shareParams, parseShareParams, resolveShared, SHARE_LIMITS } from "../app.js";

function fakeDictionary(keys) {
  const entries = keys.map((key) => ({ key, display: { en: key, zh: key }, aliases: [] }));
  return buildDictionary(entries);
}
const known = (key) => ({ name: key, entry: { key, display: { en: key, zh: key } }, cell: { mn9_mean: 1, mn9_std: 0 } });
const unknown = (text) => ({ name: text, entry: null, cell: null });

test("F17: v2 keeps type and order; unknown text with comma, percent, ampersand, emoji and CJK round-trips", () => {
  const texts = ["not, a dish", "50% off", "fish & chips", "🍜 noodles", "凉皮, 加辣", "  padded  "];
  const decision = { mode: "ask", known: [known("hotpot")], misses: texts.map(unknown) };
  const query = shareParams(decision, "zh");
  assert.match(query, /^\?v=2&d=k\.hotpot,t\./);
  const parsed = parseShareParams(query);
  assert.equal(parsed.version, 2);
  assert.deepEqual(parsed.items[0], { kind: "key", value: "hotpot" });
  assert.deepEqual(parsed.items.slice(1).map((i) => i.value), texts.map((t) => t.trim()));
  assert.ok(parsed.items.slice(1).every((i) => i.kind === "text"));
  const dictionary = fakeDictionary(["hotpot"]);
  const options = resolveShared(parsed.items, dictionary);
  assert.deepEqual(options[0], { key: "hotpot" });
  assert.deepEqual(options.slice(1).map((o) => o.text), texts.map((t) => t.trim()));
});

test("F17: unknown text that equals a known slug is never upgraded to a key in v2", () => {
  const dictionary = fakeDictionary(["hotpot"]);
  const query = shareParams({ mode: "ask", known: [], misses: [unknown("hotpot")] }, "en");
  const options = resolveShared(parseShareParams(query).items, dictionary);
  assert.deepEqual(options, [{ text: "hotpot" }]);
});

test("F17: old v1 links (untyped, comma-joined) still parse and resolve", () => {
  const dictionary = fakeDictionary(["hotpot", "black coffee"]);
  const parsed = parseShareParams("?d=hotpot,black-coffee,not%20a%20dish&lang=zh&m=opposite");
  assert.equal(parsed.version, 1);
  assert.deepEqual(parsed.items.map((i) => i.value), ["hotpot", "black-coffee", "not a dish"]);
  assert.deepEqual(resolveShared(parsed.items, dictionary), [{ key: "hotpot" }, { key: "black coffee" }, { text: "not a dish" }]);
  assert.equal(parsed.lang, "zh");
  assert.equal(parsed.mode, "opposite");
});

test("F17: limits and malformed links are controlled", () => {
  const many = { mode: "ask", known: Array.from({ length: 40 }, (_, i) => known(`d${i}`)), misses: [] };
  const parsed = parseShareParams(shareParams(many, "en"));
  assert.equal(parsed.items.length, SHARE_LIMITS.maxItems);
  const long = { mode: "ask", known: [], misses: [unknown("x".repeat(500))] };
  assert.equal(parseShareParams(shareParams(long, "en")).items[0].value.length, SHARE_LIMITS.maxTextLength);
  assert.equal(parseShareParams("?v=2&d=t.%E0%A4%A&lang=en"), null, "bad percent-encoding is rejected, not thrown");
  assert.equal(parseShareParams("?v=2&d=&lang=en"), null);
  assert.equal(parseShareParams("?v=9&d=k.hotpot"), null, "unknown version");
  assert.equal(parseShareParams(""), null);
});

// ---- D08: silencing captions report the measured distribution and its scope; never "no effect" from a zero median ----
import { silenceStats, silenceStatsFrom, STRINGS as S, fmt as fmtStr } from "../app.js";

test("D08: a zero median with large opposite changes is reported as a distribution, not as no effect", () => {
  // deltas [-20, 0, 0, 0, 20]: median 0, 20% up, 20% down, 60% unchanged
  const st = silenceStats({ n_cells_mn9_active: 5, median_delta: 0, frac_up: 0.2, frac_down: 0.2, frac_zero: 0.6 });
  assert.deepEqual(st, { n: 5, median: "0", up: 20, down: 20, same: 60 });
  for (const lang of ["en", "zh"]) {
    const t = S[lang];
    const text = fmtStr(t.silenceCaption, { name: "X", after: 1, before: 1, delta: "+0", ...st });
    assert.ok(!/no effect|does not move|不会改变|没有作用/.test(text), text);
    assert.ok(/20% .*20% .*60%|20%.*20%.*60%/.test(text.replace(/\s+/g, " ")), text);
    assert.ok(/baseline MN9 fired|基线 MN9 有放电/.test(text), "scope named");
    assert.equal(t.silenceCaptionNoEffect, undefined, "the 'no effect' string is gone");
  }
});

test("D08: percentages sum to 100 after rounding", () => {
  const st = silenceStats({ n_cells_mn9_active: 3, median_delta: -1.5, frac_up: 1 / 3, frac_down: 1 / 3, frac_zero: 1 / 3 });
  assert.equal(st.up + st.down + st.same, 100);
  assert.equal(st.median, "-1.5");
});

test("D08: stats recomputed from the manifest over cells where baseline MN9 fired match the stored stats; the all-cells scope is separate", () => {
  const manifest = JSON.parse(readFileSync(path.join(replayDir, "manifest.json"), "utf8"));
  for (const variant of manifest.variants.filter((v) => v !== "baseline")) {
    const active = silenceStatsFrom(manifest, variant, "active");
    const stored = manifest.variant_stats[variant];
    assert.equal(active.n, stored.n_cells_mn9_active, variant);
    assert.equal(active.medianValue, stored.median_delta, variant);
    assert.ok(Math.abs(active.fracUp - stored.frac_up) < 1e-9 && Math.abs(active.fracDown - stored.frac_down) < 1e-9, variant);
    const all = silenceStatsFrom(manifest, variant, "all");
    assert.equal(all.n, manifest.n_cells);
    assert.ok(all.n > active.n, "the all-cells scope includes cells whose baseline MN9 was silent");
  }
});

// ---- opposite mode with 3+ dishes: the fly takes its top pick, every remaining dish is the human's ----
test("opposite, 2 dishes: the single remaining dish is the human's (unchanged)", () => {
  const d = decide([item("A", 100), item("B", 10)], "opposite");
  assert.equal(d.flyPick.name, "A");
  assert.equal(d.winner.name, "B");
  assert.deepEqual(keys(d.humanSet), ["B"]);
  assert.equal(d.many, false);
  assert.deepEqual(keys(d.lowest), ["B"]);
});

test("opposite, 3 dishes: no single winner; the human's set is everything but the fly's pick; lowest reported", () => {
  const d = decide([item("A", 100), item("B", 40), item("C", 10)], "opposite");
  assert.equal(d.flyPick.name, "A");
  assert.equal(d.winner, null, "no lowest-MN9 dish is assigned as the human's single dish");
  assert.deepEqual(keys(d.humanSet), ["B", "C"], "human set in MN9 order");
  assert.equal(d.many, true);
  assert.deepEqual(keys(d.lowest), ["C"]);
  assert.deepEqual(d.tie, []);
  const plan = scenePlan(d, [...d.known, ...d.misses]);
  assert.equal(plan.winner, 0, "the fly still lands on its own pick");
});

test("opposite, 3 dishes with the top tied: both tied dishes are taken, one remains -> two-dish sentence", () => {
  const d = decide([item("A", 100), item("B", 100), item("C", 10)], "opposite");
  assert.deepEqual(keys(d.flyTies), ["A", "B"]);
  assert.deepEqual(keys(d.humanSet), ["C"]);
  assert.equal(d.many, false);
  assert.equal(d.winner.name, "C");
});

test("opposite, 4 dishes with the bottom tied: lowest lists both", () => {
  const d = decide([item("A", 100), item("B", 40), item("C", 5), item("D", 5)], "opposite");
  assert.deepEqual(keys(d.humanSet), ["B", "C", "D"]);
  assert.deepEqual(keys(d.lowest), ["C", "D"]);
  assert.equal(d.many, true);
});

test("opposite, all tied: reported as a tie, nothing is the human's", () => {
  const d = decide([item("A", 5), item("B", 5), item("C", 5)], "opposite");
  assert.deepEqual(keys(d.tie), ["A", "B", "C"]);
  assert.deepEqual(d.humanSet, []);
  assert.equal(d.many, false);
});

test("opposite strings exist for both cases in both languages", () => {
  for (const lang of ["en", "zh"]) {
    for (const key of ["sceneOppositeMany", "verdictOppositeMany", "cardOppositeMany", "oppositeLeast"]) assert.ok(S[lang][key], `${lang}.${key}`);
    assert.match(S[lang].sceneOppositeMany, /\{fly_pick\}/);
    assert.match(S[lang].oppositeLeast, /\{lowest\}/);
  }
});
