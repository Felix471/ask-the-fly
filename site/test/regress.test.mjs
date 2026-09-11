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
