// Run with: node --test site/test/app.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import {
  buildDictionary, buildLookup, cardLines, decide, issueUrl, normalizeName, scoreOptions, STRINGS, fmt,
} from "../app.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const dishes = JSON.parse(readFileSync(path.join(here, "..", "data", "dishes.json"), "utf8"));
const table = JSON.parse(readFileSync(path.join(here, "..", "data", "lookup_table.json"), "utf8"));

test("normalizeName mirrors encoder/normalize.py", () => {
  assert.equal(normalizeName("  Mapo   Tofu "), "mapo tofu");
  assert.equal(normalizeName("ＭＡＰＯ"), "mapo");
});

test("dictionary finds keys and aliases, misses unknown names", () => {
  const dictionary = buildDictionary(dishes);
  assert.ok(dictionary.find("water"));
  assert.equal(dictionary.find("水"), dictionary.find("water"));
  assert.equal(dictionary.find("definitely not a dish"), null);
});

test("lookup resolves water low and medium to the same cell", () => {
  const lookup = buildLookup(table);
  const low = lookup.get({ sugar: "high", bitter: "none", water: "low", ir94e: "none" });
  const medium = lookup.get({ sugar: "high", bitter: "none", water: "medium", ir94e: "none" });
  assert.equal(low, medium);
  assert.equal(low.hz.water, 60);
  assert.equal(table.cells.length, 400);
});

test("lookup rejects unknown levels", () => {
  const lookup = buildLookup(table);
  assert.throws(() => lookup.get({ sugar: "huge", bitter: "none", water: "none", ir94e: "none" }));
});

test("ask picks the highest MN9, opposite picks the lowest and reports the fly's pick", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const scored = scoreOptions(["water", "cola", "black coffee", "not a dish"], dictionary, lookup);
  const ask = decide(scored, "ask");
  const opposite = decide(scored, "opposite");
  assert.equal(ask.misses.length, 1);
  assert.equal(ask.known.length, 3);
  const maxHz = Math.max(...ask.known.map((i) => i.cell.mn9_mean));
  const minHz = Math.min(...ask.known.map((i) => i.cell.mn9_mean));
  assert.equal(ask.winner.cell.mn9_mean, maxHz);
  assert.equal(opposite.winner.cell.mn9_mean, minHz);
  assert.equal(opposite.flyPick, ask.winner);
});

test("all-miss input yields no winner", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const decision = decide(scoreOptions(["zzz", "yyy"], dictionary, lookup), "ask");
  assert.equal(decision.winner, null);
  assert.equal(decision.misses.length, 2);
});

test("every dictionary entry resolves to a lookup cell", () => {
  const lookup = buildLookup(table);
  for (const entry of dishes) {
    assert.doesNotThrow(() => lookup.get({ sugar: entry.sugar, bitter: entry.bitter, water: entry.water, ir94e: "none" }), entry.key);
  }
});

test("issue URL is prefilled and encoded", () => {
  const url = issueUrl("凉皮 liangpi", "zh");
  assert.match(url, /\/issues\/new\?template=dish-request\.yml&title=New\+dish/);
  assert.match(url, /&name_typed=%E5%87%89%E7%9A%AE\+liangpi&language=zh$/);
});

test("both languages define the same string keys and four fixed lines", () => {
  assert.deepEqual(Object.keys(STRINGS.en).sort(), Object.keys(STRINGS.zh).sort());
  assert.equal(STRINGS.en.fixedLines.length, 4);
  assert.equal(STRINGS.zh.fixedLines.length, 4);
  assert.equal(fmt("{a}-{b}", { a: 1, b: 2 }), "1-2");
});

test("sugar response is the same dish with bitter = none; equal when bitter is already none", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const [coffee, water] = scoreOptions(["black coffee", "water"], dictionary, lookup);
  assert.equal(coffee.entry.bitter !== "none", true);
  assert.equal(coffee.sugarOnly.hz.bitter, 0);
  assert.equal(coffee.sugarOnly.hz.sugar, coffee.cell.hz.sugar);
  assert.equal(coffee.sugarOnly.hz.water, coffee.cell.hz.water);
  assert.equal(water.entry.bitter, "none");
  assert.equal(water.sugarOnly, water.cell);
});

test("card lines are filled exactly from the spec templates", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const decision = decide(scoreOptions(["black coffee", "water"], dictionary, lookup), "ask");
  const en = cardLines(decision, "en");
  const zh = cardLines(decision, "zh");
  const w = decision.winner;
  assert.equal(en.fixed[0], fmt(STRINGS.en.fixedLines[0], { dish: w.entry.display.en }));
  assert.equal(en.fixed[1], fmt(STRINGS.en.fixedLines[1], { hz: w.cell.mn9_mean.toFixed(1), hz_sugar_only: w.sugarOnly.mn9_mean.toFixed(1) }));
  assert.ok(en.fixed[1].includes(w.sugarOnly.mn9_mean.toFixed(1)) && !/\{\w+\}/.test(en.fixed[1]), "both numbers filled");
  assert.ok(!/\{\w+\}/.test(en.fixed[2]) && en.fixed[2].includes(STRINGS.en.levelNames[w.entry.sugar]), "levels filled");
  assert.equal(en.fixed[3], STRINGS.en.fixedLines[3]);
  assert.equal(en.bottom, STRINGS.en.cardBottom);
  assert.equal(zh.fixed[0], fmt(STRINGS.zh.fixedLines[0], { dish: w.entry.display.zh }));
  assert.equal(zh.fixed[3], STRINGS.zh.fixedLines[3]);
  assert.equal(zh.bottom, STRINGS.zh.cardBottom);
  assert.equal(en.fixed.length, 4);
});

test("two options in the same grid cell tie exactly and the card says so", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const a = dishes[0];
  const b = dishes.find((e) => e !== a && lookup.get({ sugar: e.sugar, bitter: e.bitter, water: e.water, ir94e: "none" }) === lookup.get({ sugar: a.sugar, bitter: a.bitter, water: a.water, ir94e: "none" }))
    || dishes.find((e) => e !== a && e.sugar === a.sugar && e.bitter === a.bitter && e.water === a.water);
  const pair = b ? [a.key, b.key] : ["water", "water"];
  const decision = decide(scoreOptions(pair, dictionary, lookup), "ask");
  if (b) {
    assert.equal(decision.tie.length, 2);
    const en = cardLines(decision, "en");
    assert.equal(en.fixed[0], fmt(STRINGS.en.fixedLines[0], { dish: `${a.display.en} / ${b.display.en}` }));
  }
  assert.ok(STRINGS.en.cardTie && STRINGS.zh.cardTie, "tie wording present in both languages");
});

test("all-miss decision fills the card with dashes", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const decision = decide(scoreOptions(["zzz"], dictionary, lookup), "ask");
  const en = cardLines(decision, "en");
  assert.equal(en.fixed[0], fmt(STRINGS.en.fixedLines[0], { dish: STRINGS.en.cardEmptyValue }));
});

// ---- brain view and fly scene (pure parts) ----
import { cellIdFor, decodeNeurons, parseReplay, spikeColor, COLORS, FLAG } from "../brain.js";
import { layoutPlates, makeToken } from "../fly.js";

test("every dictionary entry maps to a replay file that parses and matches the manifest", () => {
  const lookup = buildLookup(table);
  const manifest = JSON.parse(readFileSync(path.join(here, "..", "data", "replay", "manifest.json"), "utf8"));
  const neurons = decodeNeurons(JSON.parse(readFileSync(path.join(here, "..", "data", "neurons.json"), "utf8")));
  assert.equal(manifest.n_cells, 400);
  for (const entry of dishes) {
    const cell = lookup.get({ sugar: entry.sugar, bitter: entry.bitter, water: entry.water, ir94e: "none" });
    const id = cellIdFor(cell);
    assert.ok(manifest.cells[id], `${entry.key}: ${id} missing from manifest`);
    const buf = readFileSync(path.join(here, "..", "data", "replay", `${id}.bin`));
    const replay = parseReplay(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
    assert.equal(replay.header.cell_id, id);
    assert.equal(replay.idx.length, manifest.cells[id].n_spikes);
    assert.equal(replay.header.mn9_left_count, manifest.cells[id].mn9_left_count);
    assert.equal(replay.header.hz.sugar, cell.hz.sugar);
    assert.equal(replay.header.hz.water, cell.hz.water);
    for (let i = 1; i < replay.t.length; i += 1) assert.ok(replay.t[i] >= replay.t[i - 1], "times sorted");
    if (replay.idx.length) assert.ok(Math.max(...replay.idx) < neurons.n, "indices inside neurons.json");
    assert.ok(typeof replay.header.seed === "number" && replay.header.git_commit.length >= 7, "provenance present");
  }
});

test("neurons.json decodes with flags for every GRN class and MN9", () => {
  const neurons = decodeNeurons(JSON.parse(readFileSync(path.join(here, "..", "data", "neurons.json"), "utf8")));
  assert.equal(neurons.xy.length, neurons.n * 2);
  const has = (bit) => Array.from(neurons.flags).some((f) => (f & bit) !== 0);
  for (const name of ["sugar", "bitter", "water", "ir94e", "mn9_left", "mn9_right"]) assert.ok(has(FLAG[name]), name);
  assert.equal(spikeColor(FLAG.mn9_left | FLAG.sugar), COLORS.mn9);
  assert.equal(spikeColor(0), COLORS.spike);
});

test("plate layout wraps to rows on narrow screens and centres a single row", () => {
  const wide = layoutPlates(4, 640);
  assert.equal(wide.positions.length, 4);
  assert.ok(wide.positions.every((p) => p.y === wide.positions[0].y), "one row on a wide screen");
  const narrow = layoutPlates(4, 360);
  assert.ok(new Set(narrow.positions.map((p) => p.y)).size > 1, "wraps on a narrow screen");
  assert.ok(narrow.height > wide.height);
  const one = layoutPlates(1, 400);
  assert.equal(Math.round(one.positions[0].x), 200);
});

test("cancel token fires and clears its callbacks once", () => {
  const token = makeToken();
  let fired = 0;
  token.onCancel.push(() => { fired += 1; });
  token.cancel();
  token.cancel();
  assert.equal(token.cancelled, true);
  assert.equal(fired, 1);
});

// ---- autocomplete ----
import { suggest, closest, editDistance, entryNames } from "../app.js";

test("edit distance with cutoff", () => {
  assert.equal(editDistance("cola", "cola"), 0);
  assert.equal(editDistance("colla", "cola"), 1);
  assert.equal(editDistance("kola", "cola"), 1);
  assert.equal(editDistance("xxxxx", "cola"), 3, "over the cutoff returns cutoff + 1");
  assert.equal(editDistance("可乐", "可口可乐", 4), 2);
});

test("suggest ranks prefix, then substring, then edit distance, max 6, both languages", () => {
  const dictionary = buildDictionary(dishes);
  const en = suggest("co", dictionary, "en");
  assert.ok(en.length > 0 && en.length <= 6);
  assert.equal(en[0].rank, 0, "prefix matches come first");
  assert.ok(en.every((s, i) => i === 0 || s.rank >= en[i - 1].rank), "ranks are non-decreasing");
  assert.ok(en.some((s) => s.entry.key === "cola") && en.some((s) => s.entry.key === "cookies"));
  const sub = suggest("tofu", dictionary, "en");
  assert.equal(sub[0].entry.key, "tofu", "exact name first");
  assert.ok(sub.some((s) => s.entry.key === "mapo tofu" && s.rank === 1), "substring / word match follows");
  const typo = suggest("watermelom", dictionary, "en");
  assert.equal(typo[0].entry.key, "watermelon", "edit distance 1");
  assert.equal(typo[0].rank, 3);
  const zh = suggest("麻婆", dictionary, "zh");
  assert.equal(zh[0].label, "麻婆豆腐");
  const alias = suggest("chinese broc", dictionary, "en");
  assert.equal(alias[0].entry.key, "gai lan", "alias prefix");
  assert.equal(suggest("", dictionary, "en").length, 0);
  assert.equal(suggest("zzzzzzzz", dictionary, "en").length, 0);
});

test("closest offers near misses when nothing matches", () => {
  const dictionary = buildDictionary(dishes);
  const near = closest("watermelonsss", dictionary, "en");
  assert.ok(near.length >= 1 && near[0].entry.key === "watermelon");
  assert.equal(closest("qqqqqqqqqqqq", dictionary, "en").length, 0);
  assert.ok(entryNames(dishes[0]).includes(dishes[0].key));
});

// ---- neuroscience layers: raster rows, HUD stats, silencing variants, neuropils ----
import { rasterRows, replayStats, FLAG as BFLAG } from "../brain.js";

function loadReplay(name) {
  const buf = readFileSync(path.join(here, "..", "data", "replay", `${name}.bin`));
  return parseReplay(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
}

test("raster rows and HUD stats come from the replay file", () => {
  const neurons = decodeNeurons(JSON.parse(readFileSync(path.join(here, "..", "data", "neurons.json"), "utf8")));
  const replay = loadReplay("G_svery_high_bnone_wnone_inone");
  const rows = rasterRows(replay, neurons, { sugar: "sugar", bitter: "bitter", water: "water", mn9_left: "L", mn9_right: "R" });
  const byKey = Object.fromEntries(rows.map((r) => [r.key, r]));
  assert.equal(byKey.mn9_left.times.length, replay.header.mn9_left_count, "MN9 L row = recorded count");
  assert.ok(byKey.sugar.times.length > 0 && byKey.bitter.times.length === 0, "sugar drives, bitter silent at 0 Hz");
  assert.ok(neurons.named.length >= 5, "named neurons present");
  for (const entry of neurons.named) assert.ok(byKey[`named:${entry.key}`], `row for ${entry.label}`);
  for (const row of rows) for (let i = 1; i < row.times.length; i += 1) assert.ok(row.times[i] >= row.times[i - 1]);
  const st = replayStats(replay);
  assert.equal(st.totalNeurons, 138639, "neurons in the v783 completeness list the model is built from");
  assert.equal(st.mn9Left, replay.header.mn9_left_count);
  assert.equal(st.mn9FirstMs, replay.header.mn9_left_ms[0]);
  assert.equal(st.hz.sugar, 200);
  assert.equal(st.variant, "baseline");
});

test("silenced replay exists for every cell, same seed, Clavicle recorded as silenced", () => {
  const manifest = JSON.parse(readFileSync(path.join(here, "..", "data", "replay", "manifest.json"), "utf8"));
  assert.ok(manifest.variants.includes("silence_clavicle"));
  const base = loadReplay("G_svery_high_bnone_wnone_inone");
  const sil = loadReplay("G_svery_high_bnone_wnone_inone_silence_clavicle");
  assert.equal(sil.header.seed, base.header.seed);
  assert.equal(sil.header.silenced, "clavicle");
  assert.equal(sil.header.silenced_root_ids.length, 2);
  assert.equal(sil.header.mn9_left_count, manifest.cells.G_svery_high_bnone_wnone_inone.mn9_left_count_silence_clavicle);
  const named = JSON.parse(readFileSync(path.join(here, "..", "data", "named_neurons.json"), "utf8"));
  const quasimodo = named.neurons.find((n) => n.key === "quasimodo");
  assert.equal(quasimodo.root_ids.length, 0, "Quasimodo has no v783 match and is recorded as such");
});

test("neuropil outlines share the neuron frame and stay inside it", () => {
  const np = JSON.parse(readFileSync(path.join(here, "..", "data", "neuropils.json"), "utf8"));
  assert.equal(np.groups.length, 8);
  for (const g of np.groups) {
    assert.ok(g.polygon.length >= 3, g.key);
    for (const [x, y] of g.polygon) assert.ok(x >= -0.05 && x <= 1.05 && y >= -0.05 && y <= 1.05, `${g.key} inside frame`);
    assert.ok(g.label_en && g.label_zh);
  }
  const left = np.groups.find((g) => g.key === "ol_l").label_at[0];
  const right = np.groups.find((g) => g.key === "ol_r").label_at[0];
  assert.ok(left < 0.4 && right > 0.6, "optic lobes sit on opposite sides");
  assert.ok(BFLAG.named === 64);
});
