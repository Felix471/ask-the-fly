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
