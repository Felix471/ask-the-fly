// Run with: node --test site/test/app.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import {
  buildDictionary, buildLookup, buildSections, notFoodCopy, cardLines, decide, ir94eLevel, issueUrl, lowInterest, normalizeName, releaseLine, scoreOptions, STRINGS, fmt,
} from "../app.js";

test("footer release line: version · date · summary from site/data/release.json, version linked to the changelog", () => {
  const release = JSON.parse(readFileSync(path.join(here, "..", "data", "release.json"), "utf8"));
  const en = releaseLine(release, "en");
  const zh = releaseLine(release, "zh");
  assert.equal(en.text, `${release.version} · ${release.date} · ${STRINGS.en[release.summary_key]}`);
  assert.equal(zh.summary, STRINGS.zh[release.summary_key]);
  assert.match(en.href, /^https:\/\/github\.com\/.*CHANGELOG\.md$/);
  const changelog = readFileSync(path.join(here, "..", "..", "CHANGELOG.md"), "utf8");
  assert.ok(changelog.includes(`## ${release.version} — ${release.date}`), "release.json names the top changelog entry");
  assert.equal(releaseLine(null, "en"), null);
  assert.equal(releaseLine({ version: "1.1.1", date: "2026-09-12", summary_key: "releaseSummary" }, "en"), null, "version needs a v prefix");
  assert.equal(releaseLine({ version: "v1.1.1", date: "2026-09-12", summary_key: "missingKey" }, "en"), null, "unknown summary key renders nothing");
});

const here = path.dirname(fileURLToPath(import.meta.url));
const dishes = JSON.parse(readFileSync(path.join(here, "..", "data", "dishes.json"), "utf8"));
const table = JSON.parse(readFileSync(path.join(here, "..", "data", "lookup_table.json"), "utf8"));

test('section loader accepts v2 and marks only members of the not_food section', () => {
  const entries = [{...dishes[0], key:'sample', aliases:['synthetic']}, {...dishes[1], key:'food', aliases:[]}];
  const dictionary = buildDictionary(entries);
  const sections = buildSections({schema:'dish_sections_v2', popular:['food'], sections:[
    {zh:'食物', en:'Food', keys:['food']},
    {zh:'不是给人吃的', en:'Not food', keys:['sample'], not_food:true},
  ]});
  assert.equal(sections.sections[1].not_food, true);
  assert.deepEqual(sections.popular, ['food']);
  for (const lang of ['zh','en']) {
    assert.deepEqual(notFoodCopy(dictionary.find('synthetic'), sections, lang), STRINGS[lang].notFood);
    assert.equal(notFoodCopy(dictionary.find('food'), sections, lang), null);
    assert.equal(notFoodCopy(null, sections, lang), null);
  }
  assert.throws(() => buildSections({schema:'dish_sections_v1',sections:[]}), /schema/);
  for (const filename of ['lookup_table_v1_2.json','lookup_table_male.json']) {
    const lookup = buildLookup(JSON.parse(readFileSync(path.join(here,'..','data',filename),'utf8')));
    const scored = scoreOptions(['synthetic','food'],dictionary,lookup);
    for (const mode of ['ask','opposite']) {
      const decision = decide(scored,mode);
      assert.equal(decision.known.filter(item=>notFoodCopy(item.entry,sections,'en')).length,1);
      assert.equal(scored[0].entry,entries[0], 'classification does not mutate the dictionary');
    }
  }
});

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
  // opposite with three dishes: the fly takes its pick, the other two are the human's set
  assert.equal(opposite.winner, null);
  assert.equal(opposite.many, true);
  assert.deepEqual(opposite.humanSet.map((i) => i.entry.key), ask.known.filter((i) => i !== ask.winner).sort((a, b) => b.cell.mn9_mean - a.cell.mn9_mean).map((i) => i.entry.key));
  assert.equal(opposite.lowest[0].cell.mn9_mean, minHz);
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
    assert.doesNotThrow(() => lookup.get({ sugar: entry.sugar, bitter: entry.bitter, water: entry.water, ir94e: ir94eLevel(entry) }), entry.key);
  }
});

test("Ir94e separates dishes and ask mode picks tomato and egg", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const scored = scoreOptions(["kung pao chicken", "tomato and egg stir-fry", "steamed white rice"], dictionary, lookup);
  for (const item of scored) assert.equal(item.cell.hz.ir94e, table.levels.ir94e[item.entry.ir94e], item.entry.key);
  assert.equal(new Set(scored.map((item) => item.cell.mn9_mean)).size, 3);
  const decision = decide(scored, "ask");
  assert.equal(decision.winner.entry.key, "tomato and egg stir-fry");
  assert.deepEqual(decision.tie, []);
});

test("Ir94e changes formerly shared cells and preserves missing-field fallback", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const scored = scoreOptions(["pizza", "hamburger", "bread"], dictionary, lookup);
  const [pizza, hamburger] = scored;
  assert.equal(decide(scored, "ask").winner.entry.key, "bread");
  assert.equal(pizza.cell, hamburger.cell);
  assert.ok(pizza.cell.mn9_mean < 5);

  const real = dictionary.find("pizza");
  const withoutIr94e = { ...real };
  delete withoutIr94e.ir94e;
  const fallbackDictionary = buildDictionary([withoutIr94e]);
  const noneDictionary = buildDictionary([{ ...real, ir94e: "none" }]);
  assert.equal(scoreOptions([real.key], fallbackDictionary, lookup)[0].cell, scoreOptions([real.key], noneDictionary, lookup)[0].cell);
  assert.equal(ir94eLevel({}), "none");
  assert.equal(ir94eLevel(null), "none");
});

test("lowInterest applies only below the designed threshold to the fly's pick", () => {
  assert.equal(lowInterest({ flyPick: { cell: { mn9_mean: 4.9 } } }), true);
  assert.equal(lowInterest({ flyPick: { cell: { mn9_mean: 5 } } }), false);
  assert.equal(lowInterest({ flyPick: null }), false);
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  assert.equal(lowInterest(decide(scoreOptions(["pizza", "hamburger", "bread"], dictionary, lookup), "ask")), false);
  assert.equal(lowInterest(decide(scoreOptions(["pizza", "hamburger", "bacon"], dictionary, lookup), "ask")), true);
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

test("sugar response is the same dish with bitter = none AND ir94e = none; equal when both are already none", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const [coffee, water] = scoreOptions(["black coffee", "water"], dictionary, lookup);
  assert.equal(coffee.entry.bitter !== "none", true);
  assert.equal(coffee.sugarOnly.hz.bitter, 0);
  assert.equal(coffee.sugarOnly.hz.ir94e, 0);
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
  assert.ok(en.fixed[2].includes(STRINGS.en.levelNames[w.entry.ir94e]), "Ir94e level filled");
  assert.equal(en.fixed[3], STRINGS.en.fixedLines[3]);
  assert.equal(en.bottom, STRINGS.en.cardHonesty);
  assert.equal(zh.fixed[0], fmt(STRINGS.zh.fixedLines[0], { dish: w.entry.display.zh }));
  assert.equal(zh.fixed[3], STRINGS.zh.fixedLines[3]);
  assert.equal(zh.bottom, STRINGS.zh.cardHonesty);
  assert.equal(en.fixed.length, 4);
});

test("two options in the same grid cell tie exactly and the card says so", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const a = dishes[0];
  const b = dishes.find((e) => e !== a && lookup.get({ sugar: e.sugar, bitter: e.bitter, water: e.water, ir94e: ir94eLevel(e) }) === lookup.get({ sugar: a.sugar, bitter: a.bitter, water: a.water, ir94e: ir94eLevel(a) }))
    || dishes.find((e) => e !== a && e.sugar === a.sugar && e.bitter === a.bitter && e.water === a.water && ir94eLevel(e) === ir94eLevel(a));
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
    const cell = lookup.get({ sugar: entry.sugar, bitter: entry.bitter, water: entry.water, ir94e: ir94eLevel(entry) });
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
    assert.ok(replay.idx.every(index => index < neurons.n), "indices inside neurons.json");
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

// ---- share links, QR code, provenance ----
import { COMMIT_REWRITE, currentCommit, parseShareParams, resolveShared, shareParams, shareUrl, slugFor, SITE_URL, optionFromText, optionQuery, optionLabel, sameOption, levelsText } from "../app.js";
import { FRAME_SET } from "../fly.js";
import { qrcode } from "../vendor/qrcode-generator/qrcode.mjs";

test("share link round-trips known dishes as slugs and unknown names as typed", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const decision = decide(scoreOptions(["火锅", "black coffee", "not a dish"], dictionary, lookup), "ask");
  const url = shareUrl(decision, "zh");
  assert.equal(url, `${SITE_URL}?v=2&d=k.hotpot,k.black-coffee,t.not%20a%20dish&lang=zh`);
  const parsed = parseShareParams(new URL(url).search);
  assert.deepEqual(parsed, { version: 2, items: [{ kind: "key", value: "hotpot" }, { kind: "key", value: "black-coffee" }, { kind: "text", value: "not a dish" }], lang: "zh", mode: "ask" });
  const options = resolveShared(parsed.items, dictionary);
  assert.deepEqual(options, [{ key: "hotpot" }, { key: "black coffee" }, { text: "not a dish" }]);
  const again = decide(scoreOptions(options.map(optionQuery), dictionary, lookup), "ask");
  assert.deepEqual(again.known.map((i) => i.entry.key), decision.known.map((i) => i.entry.key));
  assert.deepEqual(again.misses.map((i) => i.name), ["not a dish"]);
  assert.equal(again.winner.entry.key, decision.winner.entry.key);
  assert.match(shareParams(decide(scoreOptions(["火锅", "black coffee"], dictionary, lookup), "opposite"), "en"), /&lang=en&m=opposite$/);
  assert.equal(parseShareParams("?lang=zh"), null);
  assert.equal(parseShareParams("?d=&lang=zh"), null);
  assert.equal(parseShareParams("?d=a,b&lang=fr").lang, null);
  assert.equal(parseShareParams("?d=a,b&lang=fr").version, 1);
  assert.equal(slugFor("Black Coffee"), "black-coffee");
});

test("every dictionary key survives the slug round trip", () => {
  const dictionary = buildDictionary(dishes);
  for (const entry of dishes) {
    const [option] = resolveShared([{ kind: "key", value: slugFor(entry.key) }], dictionary);
    assert.deepEqual(option, { key: entry.key }, `${entry.key} -> ${slugFor(entry.key)}`);
  }
});

test("vendored QR generator encodes a share link at error correction M", () => {
  const url = `${SITE_URL}?d=teriyaki-chicken,sour-plum-drink,hot-and-sour-noodles,lemon&lang=zh`;
  const qr = qrcode(0, "M");
  qr.addData(url);
  qr.make();
  const n = qr.getModuleCount();
  assert.ok(n >= 41 && n <= 57, `version fits a ~100-char URL, got ${n} modules`);
  // finder pattern: dark corner module, light ring at (1, 1), dark centre at (3, 3)
  assert.equal(qr.isDark(0, 0), true);
  assert.equal(qr.isDark(1, 1), false);
  assert.equal(qr.isDark(3, 3), true);
});

test("footer shows the post-rewrite hash for the grid commit the table records", () => {
  assert.equal(currentCommit(table.git_commit).slice(0, 7), "01a798e");
  assert.equal(COMMIT_REWRITE[table.git_commit].slice(0, 7), "01a798e");
  assert.equal(currentCommit("deadbeef"), "deadbeef");
  assert.equal(currentCommit(undefined), "");
});

// ---- brain snapshot: the frame with the most MN9 activity ----
import { peakMn9Window, BIN_MS, BINS_IN_WINDOW } from "../brain.js";

test("peak MN9 window is inside the trial and counts every MN9 spike it covers", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const neurons = decodeNeurons(JSON.parse(readFileSync(path.join(here, "..", "data", "neurons.json"), "utf8")));
  const load = (name) => {
    const entry = dictionary.find(name);
    const cell = lookup.get({ ...entry, ir94e: ir94eLevel(entry) });
    const buf = readFileSync(path.join(here, "..", "data", "replay", `${cellIdFor(cell)}.bin`));
    return parseReplay(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
  };
  const active = load("hotpot");
  const peak = peakMn9Window(active, neurons);
  assert.ok(peak.count > 0, "hotpot's run has MN9 spikes");
  assert.ok(peak.tMs > 0 && peak.tMs <= active.header.duration_ms);
  const windowMs = BIN_MS * BINS_IN_WINDOW;
  let inWindow = 0;
  for (let i = 0; i < active.idx.length; i += 1) {
    const f = neurons.flags[active.idx[i]];
    const ms = active.t[i] / 10;
    if (f & (FLAG.mn9_left | FLAG.mn9_right) && ms <= peak.tMs && ms >= peak.tMs - 1 - windowMs) inWindow += 1;
  }
  assert.equal(inWindow, peak.count);
  assert.ok(peak.count <= (active.header.mn9_left_count || 0) + (active.header.mn9_right_count || 0));
  const silent = load("black coffee");
  const quiet = peakMn9Window(silent, neurons);
  assert.equal(quiet.count, 0);
  assert.ok(quiet.tMs > 0 && quiet.tMs <= silent.header.duration_ms);
});

test("fixed line 4 is a label; the snapshot caption carries the numbers", () => {
  assert.equal(STRINGS.en.fixedLines[3], "Brain response:");
  assert.equal(STRINGS.zh.fixedLines[3], "\u8111\u53cd\u5e94\uff1a");
  assert.equal(fmt(STRINGS.en.cardSnapshot, { n: 62, neurons: "138,639" }), "MN9 fired 62\u00d7 \u00b7 138,639 neurons");
  assert.equal(STRINGS.en.issueBody, undefined);
});

test("site/config.json carries the canonical URL the page falls back to", () => {
  const config = JSON.parse(readFileSync(path.join(here, "..", "config.json"), "utf8"));
  assert.equal(config.site_url, SITE_URL);
  assert.equal(SITE_URL, "https://askthefly.app/");
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const decision = decide(scoreOptions(["火锅", "black coffee"], dictionary, lookup), "ask");
  assert.equal(shareUrl(decision, "en", "https://example.test"), "https://example.test/?v=2&d=k.hotpot,k.black-coffee&lang=en");
});

// ---- selections are keys; the language switch only changes labels ----
test("selections are stable keys; typed unknown text stays as typed", () => {
  const dictionary = buildDictionary(dishes);
  assert.deepEqual(optionFromText("  火锅 ", dictionary), { key: "hotpot" });
  assert.deepEqual(optionFromText("Black Coffee", dictionary), { key: "black coffee" });
  assert.deepEqual(optionFromText("moon cheese", dictionary), { text: "moon cheese" });
  assert.equal(optionFromText("   ", dictionary), null);
  const hot = { key: "hotpot" };
  assert.equal(optionLabel(hot, dictionary, "zh"), "火锅");
  assert.equal(optionLabel(hot, dictionary, "en"), "hotpot");
  assert.equal(optionLabel({ text: "moon cheese" }, dictionary, "zh"), "moon cheese");
  assert.ok(sameOption(hot, optionFromText("火锅", dictionary)));
  assert.ok(sameOption({ text: "Liang Pi" }, { text: "liang  pi" }));
  assert.ok(!sameOption(hot, { text: "hotpot" }));
  const lookup = buildLookup(table);
  const options = [hot, { key: "black coffee" }, { text: "moon cheese" }];
  const zh = decide(scoreOptions(options.map(optionQuery), dictionary, lookup), "ask");
  const en = decide(scoreOptions(options.map(optionQuery), dictionary, lookup), "ask");
  assert.equal(zh.winner.entry.key, en.winner.entry.key);
  assert.equal(zh.winner.cell.mn9_mean, en.winner.cell.mn9_mean);
  assert.deepEqual(zh.misses.map((m) => m.name), ["moon cheese"]);
});

test("every fly state draws from the sprite frame sets", () => {
  const sets = new Set(["idle", "fly", "land", "proboscis"]);
  for (const state of ["idle", "fly", "land", "taste", "hover", "proboscis"]) assert.ok(sets.has(FRAME_SET[state]), state);
  assert.equal(FRAME_SET.hover, "idle");
});

test("the card's one honesty sentence names both the LLM estimate and the precomputed connectome runs", () => {
  assert.match(STRINGS.en.cardHonesty, /LLM/);
  assert.match(STRINGS.en.cardHonesty, /precomputed/);
  assert.match(STRINGS.en.cardHonesty, /connectome/);
  assert.match(STRINGS.zh.cardHonesty, /LLM/);
  assert.match(STRINGS.zh.cardHonesty, /预先/);
  assert.match(STRINGS.zh.cardHonesty, /连接组/);
  assert.equal(STRINGS.en.cardBottom, undefined);
});

test("replay caption shows levels in the page language, not the cell id", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const [pho] = scoreOptions(["pho"], dictionary, lookup);
  const en = levelsText(pho.cell, "en");
  const zh = levelsText(pho.cell, "zh");
  assert.match(en, /^sugar \S+ · bitter \S+ · water \S+ · amino acids \S+$/);
  assert.match(zh, /^甜 \S+ · 苦 \S+ · 水 \S+ · 氨基酸 \S+$/);
  assert.ok(!/G_s/.test(en) && !/G_s/.test(zh), "no raw cell id in the caption");
  assert.equal(levelsText({ sugar: "low", bitter: "none", water: "high" }, "en"), `sugar low · bitter none · water high · amino acids ${STRINGS.en.levelNames.none}`);
  assert.equal(levelsText({ sugar: "low", bitter: "none", water: "high" }, "zh"), `甜 低 · 苦 无 · 水 高 · 氨基酸 ${STRINGS.zh.levelNames.none}`);
  assert.equal(levelsText({ sugar: "low", bitter: "none", water: "high", ir94e: "medium" }, "en"), "sugar low · bitter none · water high · amino acids medium");
});

test("opposite mode: the fly's own pick drives the fly; with three dishes the other two are the human's", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const d = decide(scoreOptions(["watermelon", "pho", "black coffee"], dictionary, lookup), "opposite");
  assert.equal(d.flyPick.entry.key, "watermelon");
  assert.equal(d.winner, null);
  assert.deepEqual(d.humanSet.map((i) => i.entry.key), ["pho", "black coffee"]);
  assert.equal(d.lowest[0].entry.key, "black coffee");
  const two = decide(scoreOptions(["watermelon", "black coffee"], dictionary, lookup), "opposite");
  assert.equal(two.winner.entry.key, "black coffee", "two dishes: the remaining dish is the human's");
});
import './taste_states.test.mjs';

// ---- v2.1.1: coherent verdicts for low-response picks; Ir94e raster row ----
import { verdictParts } from "../app.js";

test("a no-response pick is named and the verdict has no dangling 'this one'", () => {
  const text = (key, values = {}) => `${key}${values.fly_pick ? ":" + values.fly_pick : ""}`;
  const name = (item) => item.name;
  const cell = (mn9, state) => ({ mn9_mean: mn9, mn11d_mean: 0, mn11v_mean: 0, state });
  const scored = [{ name: "steak", cell: cell(1.2, "no_response") }, { name: "coffee", cell: cell(0, "no_response") }, { name: "tea", cell: cell(0.3, "no_response") }];
  const ask = verdictParts(decide(scored, "ask"), name, text);
  assert.deepEqual(ask, { lead: "verdictNoResponse", strong: "steak", subs: [] });
  const two = verdictParts(decide(scored.slice(0, 2), "opposite"), name, text);
  assert.equal(two.strong, "verdictOpposite:steak", "opposite mode still says who gets what");
  assert.deepEqual(two.subs, ["lowInterest"]);
  const many = verdictParts(decide(scored, "opposite"), name, text);
  assert.equal(many.strong, "verdictOppositeMany:steak");
  assert.deepEqual(many.subs, ["oppositeLeast", "lowInterest"]);
  const sharedTop = verdictParts(decide([{ name: "a", cell: cell(0.1, "") }, { name: "b", cell: cell(0.1, "") }, scored[1]], "opposite"), name, text);
  assert.deepEqual(sharedTop.subs, ["lowInterestTie"], "a shared top score in opposite mode is not called one pick");
  assert.equal(sharedTop.strong, "verdictOpposite:a / b", "every dish the fly keeps is named");
  const tied = verdictParts(decide([scored[1], { name: "soap", cell: cell(0, "no_response") }], "ask"), name, text);
  assert.deepEqual(tied, { lead: "verdictTie", strong: "coffee / soap", subs: ["lowInterestTie"] }, "a tie never says 'picked this one'");
  const mixed = verdictParts(decide([scored[0], { name: "broth", cell: { mn9_mean: 0.4, mn11d_mean: 6, mn11v_mean: 0 } }], "ask"), name, text);
  assert.deepEqual(mixed, { lead: "verdictAsk", strong: "steak", subs: ["lowInterest"] }, "'nothing got a response' is not claimed when another dish moves the mouth");
  const eats = verdictParts(decide([{ name: "honey", cell: cell(97, "eats") }, scored[0]], "ask"), name, text);
  assert.deepEqual(eats, { lead: "verdictAsk", strong: "honey", subs: [] });
  assert.deepEqual(verdictParts(decide([{ name: "x", cell: null }], "ask"), name, text), { lead: "verdictNone", strong: "", subs: [] });
});

test("verdict copy exists in both languages for single-fly and both-fly wording", () => {
  for (const lang of ["en", "zh"]) for (const key of ["verdictNoResponse", "lowInterestTie", "lowInterest"]) {
    assert.ok(STRINGS[lang][key], `${lang} ${key}`);
    assert.ok(STRINGS[lang].panelVerdict[key].includes("{fly}"), `${lang} panelVerdict.${key}`);
  }
  assert.ok(!/care for much of any/.test(STRINGS.en.panelVerdict.lowInterest));
});

test("the raster has an Ir94e GRN row that fires only when Ir94e is driven", () => {
  const neurons = decodeNeurons(JSON.parse(readFileSync(path.join(here, "..", "data", "neurons.json"), "utf8")));
  const labels = { sugar: "s", bitter: "b", water: "w", ir94e: "i", mn9_left: "L", mn9_right: "R" };
  const on = rasterRows(loadReplay("G_snone_bnone_wnone_ihigh"), neurons, labels);
  assert.deepEqual(on.slice(0, 4).map((r) => r.key), ["sugar", "bitter", "water", "ir94e"]);
  assert.ok(on[3].times.length > 0 && on[3].label === "i");
  const off = rasterRows(loadReplay("G_svery_high_bnone_wnone_inone"), neurons, labels);
  assert.equal(off.find((r) => r.key === "ir94e").times.length, 0);
});

import { cardReadoutLines } from "../app.js";

test("with both flies the card has one labelled readout line per fly, each from its own pick", () => {
  const male = buildLookup(JSON.parse(readFileSync(path.join(here, "..", "data", "lookup_table_male.json"), "utf8")));
  const keys = ["hamburger", "watermelon", "steak"];
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const f = decide(scoreOptions(keys, dictionary, lookup), "ask");
  const m = decide(scoreOptions(keys, dictionary, male), "ask");
  for (const lang of ["en", "zh"]) {
    const single = cardReadoutLines(f, lang);
    assert.deepEqual(single, [{ fly: null, text: cardLines(f, lang).fixed[1] }], "single-fly card line is unchanged");
    const [a, b] = cardReadoutLines(f, lang, m);
    assert.deepEqual([a.fly, b.fly], ["female", "male"]);
    assert.ok(a.text.startsWith(STRINGS[lang].flyName.female) && a.text.includes(f.flyPick.cell.mn9_mean.toFixed(1)));
    assert.ok(b.text.startsWith(STRINGS[lang].flyName.male) && b.text.includes(m.flyPick.cell.mn9_mean.toFixed(1)));
    assert.ok(b.text.includes(m.flyPick.sugarOnly.mn9_mean.toFixed(1)), "the male line uses the male table's sugar-only cell");
  }
  assert.notEqual(f.flyPick.cell.mn9_mean, m.flyPick.cell.mn9_mean);
});

// ---- v2.2.0: first-visit helpers ----
import { EXAMPLE_SETS, tableHintKey, stickyBarState, xhsPassedItems, runPanelsInTurn } from "../app.js";

test("example sets use real entries and give the female fly one clear pick", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  assert.ok(EXAMPLE_SETS.length >= 3);
  for (const set of EXAMPLE_SETS) {
    assert.ok(set.length >= 2 && set.length <= 3, set.join());
    const scored = scoreOptions(set, dictionary, lookup);
    assert.ok(scored.every((item) => item.cell && item.entry.key === item.name), `known keys: ${set.join()}`);
    const d = decide(scored, "ask");
    assert.equal(d.tie.length, 0, `clear pick: ${set.join()}`);
    assert.ok(d.winner.cell.mn9_mean >= 5, `the pick is not a low-interest one: ${set.join()}`);
  }
});

test("the table hint explains what is missing until two dishes are on it", () => {
  assert.equal(tableHintKey(0), "hint");
  assert.equal(tableHintKey(1), "hintOneMore");
  assert.equal(tableHintKey(2), null);
  assert.equal(tableHintKey(5), null);
});

test("the sticky bar shows only while choosing with the ask button out of view", () => {
  assert.deepEqual(stickyBarState({ phase: "input", count: 0, askVisible: false }), { show: false });
  assert.deepEqual(stickyBarState({ phase: "input", count: 1, askVisible: false }), { show: true, key: "stickyNeedMore", n: 1, count: 1, ready: false });
  assert.deepEqual(stickyBarState({ phase: "input", count: 3, askVisible: false }), { show: true, key: "stickyCount", n: 3, ready: true });
  assert.deepEqual(stickyBarState({ phase: "input", count: 3, askVisible: true }), { show: false });
  assert.deepEqual(stickyBarState({ phase: "tasting", count: 3, askVisible: false }), { show: false });
});

test("the Xiaohongshu card lists the dishes the pick was ranked above, highest first", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const keys = ["black coffee", "watermelon", "mapo tofu", "honey"];
  const ask = decide(scoreOptions(keys, dictionary, lookup), "ask");
  assert.deepEqual(xhsPassedItems(ask).map((i) => i.name), ["watermelon", "mapo tofu", "black coffee"]);
  assert.deepEqual(xhsPassedItems(decide(scoreOptions(keys, dictionary, lookup), "opposite")), [], "opposite mode has its own layout");
  assert.deepEqual(xhsPassedItems(decide(scoreOptions(["steak", "black coffee"], dictionary, lookup), "ask")), [], "an all-tied table has nothing below the tie");
  assert.deepEqual(xhsPassedItems(decide(scoreOptions(["no such dish"], dictionary, lookup), "ask")), []);
});

test("both flies play one after the other only when their panels are stacked", () => {
  assert.equal(runPanelsInTurn("both", true), true);
  assert.equal(runPanelsInTurn("both", false), false);
  assert.equal(runPanelsInTurn("female", true), false);
  assert.equal(runPanelsInTurn("male", true), false);
});

import { clipText } from "../app.js";

test("a clipped free-text name never ends on half a surrogate pair", () => {
  const name = "x".repeat(79) + "\u{1f600}";
  assert.equal(clipText(name, 80), "x".repeat(79));
  assert.equal(clipText("abc", 80), "abc");
  assert.equal(clipText("x".repeat(78) + "\u{1f600}", 80), "x".repeat(78) + "\u{1f600}");
  const decision = decide([{ name, cell: null }, { name: "other", cell: null }], "ask");
  assert.doesNotThrow(() => shareParams(decision, "en"));
});

import { guessChoices, guessOutcome, guessSummary, guessText, guessPromptKey, displayName } from "../app.js";

test("the guess is judged against the fly's own pick, ties count, unknown entries cannot be guessed", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const keyOf = (decision, name) => decision.known.find((item) => item.name === name).entry.key;
  const ask = decide(scoreOptions(["black coffee", "watermelon", "mapo tofu", "no such dish"], dictionary, lookup), "ask");
  assert.equal(guessChoices(ask).length, 3, "only scored dishes can be tapped");
  assert.deepEqual(guessChoices(decide(scoreOptions(["watermelon", "no such dish"], dictionary, lookup), "ask")), [], "one scored dish: nothing to guess");
  assert.equal(guessOutcome(ask, keyOf(ask, "watermelon")).hit, true);
  assert.equal(guessOutcome(ask, keyOf(ask, "black coffee")).hit, false);
  assert.equal(guessOutcome(ask, "no such dish"), null);
  assert.deepEqual(guessSummary(ask, null, keyOf(ask, "watermelon")).kind, "right");
  assert.deepEqual(guessSummary(ask, null, keyOf(ask, "mapo tofu")).kind, "wrong");

  // "Let the fly eat first": the guess is still what the fly takes, not what is left.
  const opposite = decide(scoreOptions(["black coffee", "watermelon", "mapo tofu"], dictionary, lookup), "opposite");
  assert.equal(guessOutcome(opposite, keyOf(opposite, "watermelon")).hit, true);
  assert.equal(guessOutcome(opposite, keyOf(opposite, "black coffee")).hit, false);

  // An exact tie at the top: either tied dish counts, and the sentence says it was a tie.
  const tied = decide(scoreOptions(["steak", "black coffee", "watermelon"], dictionary, lookup), "ask");
  const allTied = decide(scoreOptions(["steak", "black coffee"], dictionary, lookup), "ask");
  assert.equal(allTied.flyTies.length, 2, "fixture: steak and black coffee share a cell score");
  const summary = guessSummary(allTied, null, keyOf(allTied, "steak"));
  assert.deepEqual([summary.kind, summary.correct], ["tieRight", true]);
  assert.equal(guessSummary(tied, null, keyOf(tied, "steak")).kind, "wrong", "a tie below the top is not the pick");
  for (const lang of ["en", "zh"]) {
    assert.equal(guessText(summary, lang, "result"), STRINGS[lang].guess.resultTieRight);
    assert.ok(guessText(summary, lang, "card").includes(displayName(summary.item, lang)));
    assert.equal(guessText(null, lang, "card"), "");
  }
});

test("one guess is judged for each fly; the tally counts a round only when both are right", () => {
  const item = (key, hz) => ({ name: key, entry: { key, display: { en: key, zh: key } }, cell: { mn9_mean: hz } });
  const table = (a, b, c) => decide([item("a", a), item("b", b), item("c", c)], "ask");
  const female = table(30, 10, 0);
  assert.deepEqual([guessSummary(female, table(40, 5, 0), "a").kind, guessSummary(female, table(40, 5, 0), "a").correct], ["bothRight", true]);
  assert.deepEqual([guessSummary(female, table(40, 5, 0), "b").kind, guessSummary(female, table(40, 5, 0), "b").correct], ["bothWrong", false]);
  const split = guessSummary(female, table(5, 40, 0), "a");
  assert.deepEqual([split.kind, split.hit, split.miss, split.correct], ["oneFly", "female", "male", false]);
  assert.equal(guessSummary(female, table(5, 40, 0), "b").hit, "male");
  for (const lang of ["en", "zh"]) {
    const t = STRINGS[lang];
    assert.equal(guessText(split, lang, "result"), fmt(t.guess.resultOneFly, { hit: t.flyName.female, miss: t.flyName.male }));
    assert.equal(guessText(split, lang, "card"), fmt(t.guess.cardOneFly, { hit: t.flyName.female }));
    assert.equal(guessText(guessSummary(female, table(40, 5, 0), "b"), lang, "card"), fmt(t.guess.cardWrong, { guess: "b" }), "both wrong uses the short wrong line on the card");
    for (const text of [guessText(split, lang, "result"), guessText(split, lang, "card")]) assert.ok(!/[{}]/.test(text), text);
  }
});

test("the guess caption follows the mode, the flies asked, and a shared link", () => {
  assert.equal(guessPromptKey("ask", "female", false), "promptAsk");
  assert.equal(guessPromptKey("ask", "male", false), "promptAsk");
  assert.equal(guessPromptKey("opposite", "female", false), "promptOpposite");
  assert.equal(guessPromptKey("ask", "both", false), "promptBoth");
  assert.equal(guessPromptKey("opposite", "both", false), "promptBothOpposite");
  assert.equal(guessPromptKey("ask", "both", true), "promptShared");
  assert.equal(guessPromptKey("opposite", "female", true), "promptOpposite", "the shared caption does not say whose dish it is");
  for (const lang of ["en", "zh"]) for (const key of ["promptAsk", "promptOpposite", "promptBoth", "promptBothOpposite", "promptShared"]) assert.ok(STRINGS[lang].guess[key]);
});
