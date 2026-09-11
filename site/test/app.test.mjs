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
  assert.match(url, /\/issues\/new\?title=New%20dish/);
  assert.match(url, /body=/);
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
  assert.equal(en.fixed[0], `Today's pick: ${w.entry.display.en}`);
  assert.equal(en.fixed[1], `MN9: ${w.cell.mn9_mean.toFixed(1)} Hz (sugar response ${w.sugarOnly.mn9_mean.toFixed(1)} · after bitter suppression ${w.cell.mn9_mean.toFixed(1)})`);
  assert.match(en.fixed[2], /^Taste input: sugar .+ · bitter .+ · water .+ \(estimated by LLM\)$/);
  assert.equal(en.fixed[3], "Simulation: precomputed from the whole-brain connectome, not run live");
  assert.equal(en.bottom, "The model turns the dish into taste signals. The connectome predicts whether the fly would extend its proboscis. We use that response to choose the winner.");
  assert.equal(zh.fixed[0], `今日选择：${w.entry.display.zh}`);
  assert.equal(zh.fixed[3], "仿真：基于全脑连接组预先计算，并非现场实时运行");
  assert.equal(zh.bottom, "模型先把菜品转换成味觉信号，连接组再预测果蝇会不会伸出口器。最后我们根据这个反应决定选哪一道。");
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
    assert.equal(en.fixed[0], `Today's pick: ${a.display.en} / ${b.display.en}`);
  }
  assert.equal(STRINGS.en.cardTie, "The fly can't tell these apart");
  assert.equal(STRINGS.zh.cardTie, "果蝇分不出这几个");
});

test("all-miss decision fills the card with dashes", () => {
  const dictionary = buildDictionary(dishes);
  const lookup = buildLookup(table);
  const decision = decide(scoreOptions(["zzz"], dictionary, lookup), "ask");
  const en = cardLines(decision, "en");
  assert.equal(en.fixed[0], "Today's pick: —");
});
