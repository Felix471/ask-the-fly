// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildDictionary, buildLookup, scoreOptions, DIMENSIONS} from '../app.js';
import {readoutState} from '../taste_states.js';
import {cellIdFor, decodeNeurons, parseReplay} from '../brain.js';

const json = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));

test('male lookup has 400 distinct Hz keys and scores all 174 dishes with the recorded state', () => {
  const table = json('../data/lookup_table_male.json');
  const dishes = json('../../data/dishes.json');
  const lookup = buildLookup(table);
  assert.equal(table.cells.length, 400);
  assert.equal(new Set(table.cells.map(c => DIMENSIONS.map(d => c.hz[d]).join('|'))).size, 400);
  assert.equal(dishes.length, 174);
  for (const item of scoreOptions(dishes.map(d => d.key), buildDictionary(dishes), lookup)) {
    assert.ok(item.cell, item.name);
    assert.equal(readoutState(item.cell), item.cell.state, item.name);
  }
});

test('male neurons decode in frozen replay order, with all thirteen named readouts', () => {
  const raw = json('../data/neurons_male.json');
  const index = json('../../data/replay_neurons_male.json');
  const neurons = decodeNeurons(raw);
  assert.equal(neurons.layout, 'malecns_v1_soma');
  assert.equal(neurons.nIndexed, 11271);
  assert.deepEqual(Array.from(neurons.flags.slice(0, neurons.nIndexed)), index.flags);
  const named = neurons.named.flatMap(group => group.cells);
  assert.equal(named.length, 13);
  for (const cell of named) {
    assert.ok(Number.isInteger(cell.index) && cell.index >= 0 && cell.index < neurons.n);
    if (cell.index < neurons.nIndexed) assert.equal(index.root_ids[cell.index], cell.root_id);
  }
});

test('every dish has a male trial-0 replay with exact indexed primary MN9 counts', () => {
  const manifest = json('../data/replay_male/manifest.json');
  const lookup = buildLookup(json('../data/lookup_table_male.json'));
  const index = json('../../data/replay_neurons_male.json');
  const neurons = decodeNeurons(json('../data/neurons_male.json'));
  const primary = neurons.named.find(g => g.key === 'mn9_primary').cells[0];
  assert.equal(index.root_ids[primary.index], '10331');
  const parsed = new Map();
  for (const dish of json('../../data/dishes.json')) {
    const cid = cellIdFor(lookup.get(dish));
    assert.ok(manifest.cells[cid], dish.key);
    if (!parsed.has(cid)) {
      const bytes = readFileSync(new URL(`../data/replay_male/${cid}.bin`, import.meta.url));
      parsed.set(cid, parseReplay(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)));
    }
    const {header, idx} = parsed.get(cid);
    assert.equal(header.fly, 'male');
    assert.equal(header.cell_id, cid);
    assert.equal(header.trial, 0);
    assert.equal(header.n_spikes, idx.length);
    let count = 0;
    for (const i of idx) {
      assert.ok(i < neurons.nIndexed);
      if (i === primary.index) count += 1;
    }
    assert.equal(header.mn9_left_count, count, cid);
  }
  assert.equal(parsed.size, 55);
  assert.equal(manifest.n_cells, parsed.size);
});
