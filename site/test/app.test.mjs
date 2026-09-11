// Run with: node --test site/test/app.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import {
  buildDictionary, buildLookup, decide, issueUrl, normalizeName, scoreOptions, STRINGS, fmt,
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
