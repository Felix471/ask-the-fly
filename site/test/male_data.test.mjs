// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {buildDictionary, buildLookup, scoreOptions, DIMENSIONS} from '../app.js';
import {readoutState} from '../taste_states.js';
import {cellIdFor, decodeNeurons, parseReplay} from '../brain.js';

const json = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));

test('batch 3: all 279 entries resolve to both flies and an intact shipped male replay', () => {
  const dishes = json('../../data/dishes.json');
  assert.equal(dishes.length, 279);
  assert.deepEqual(json('../data/dishes.json'), dishes);
  const dictionary = buildDictionary(dishes);
  const manifest = json('../data/replay_male/manifest.json');
  const verified = new Set();
  for (const filename of ['lookup_table_v1_2.json', 'lookup_table_male.json']) {
    const scored = scoreOptions(dishes.map(d => d.key), dictionary, buildLookup(json(`../data/${filename}`)));
    assert.equal(scored.length, 279);
    for (const [i, item] of scored.entries()) {
      assert.equal(item.entry.key, dishes[i].key);
      assert.ok(item.cell, `${filename}: ${dishes[i].key}`);
      assert.ok(Number.isFinite(item.cell.mn9_mean), item.entry.key);
      assert.equal(readoutState(item.cell), item.cell.state);
      if (filename === 'lookup_table_male.json') {
        const cid = cellIdFor(item.cell);
        const record = manifest.cells[cid];
        assert.ok(record, item.entry.key);
        if (!verified.has(cid)) {
          const bytes = readFileSync(new URL(`../data/replay_male/${cid}.bin`, import.meta.url));
          assert.equal(createHash('sha256').update(bytes).digest('hex'), record.sha256, cid);
          verified.add(cid);
        }
      }
    }
  }
  assert.equal(verified.size, 70);
  assert.deepEqual(verified, new Set(Object.keys(manifest.cells)));
});

test('male v2.0.0: immutable scores and states for the 174 reference dishes', () => {
  const bytes = readFileSync(new URL('./fixtures/male_v2_0_0_scores.json', import.meta.url));
  assert.equal(createHash('sha256').update(bytes).digest('hex'),
    'b3da79e6b3bdab1ef4fcb4f5c7c3bc663600c44c43346ba9ac1a71594506cc03');
  const fixture = JSON.parse(bytes);
  const female = json('./fixtures/female_v1_2_1_decisions.json');
  assert.equal(fixture.dishes.length, 174);
  assert.deepEqual(fixture.dishes.map(d => d[0]), female.dishes.map(d => d[0]));
  const dictionary = buildDictionary(json('../data/dishes.json'));
  const table = json('../data/lookup_table_male.json');
  assert.equal(table.cells_sha256, fixture.lookup_cells_sha256);
  const scored = scoreOptions(fixture.dishes.map(d => d[0]), dictionary, buildLookup(table));
  assert.deepEqual(scored.map(d => [d.entry.key, cellIdFor(d.cell), d.cell.mn9_mean, readoutState(d.cell)]), fixture.dishes);
});

test('male lookup has 400 distinct Hz keys and scores every current dish with the recorded state', () => {
  const table = json('../data/lookup_table_male.json');
  const dishes = json('../../data/dishes.json');
  const lookup = buildLookup(table);
  assert.equal(table.cells.length, 400);
  assert.equal(new Set(table.cells.map(c => DIMENSIONS.map(d => c.hz[d]).join('|'))).size, 400);
  const scored = scoreOptions(dishes.map(d => d.key), buildDictionary(dishes), lookup);
  assert.equal(scored.length, dishes.length);
  for (const item of scored) {
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
  assert.deepEqual(neurons.named.map(g=>[g.key,g.label,g.code]),
    [['mn9','MN9',null],['mn11d','MN11D',null],['mn11v','MN11V',null],['cem','CEM',null]]);
  assert.equal(neurons.named[0].cells.length,2);
  assert.equal(named.length, 13);
  for (const cell of named) {
    assert.ok(Number.isInteger(cell.index) && cell.index >= 0 && cell.index < neurons.n);
    if (cell.index < neurons.nIndexed) assert.equal(index.root_ids[cell.index], cell.root_id);
  }
});

test('tracked centroid cache agrees with the shipped positions without the large synapse source', () => {
  const raw=json('../data/neurons_male.json'), neurons=decodeNeurons(raw);
  const index=json('../../data/replay_neurons_male.json');
  const cache=json('../../data/malecns/derived/male_synapse_centroids.json');
  assert.equal(cache.schema_version,'male_synapse_centroids_v1');
  assert.equal(cache.source.bytes,6777179098);
  assert.equal(cache.source.sha256,'959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07');
  assert.equal(cache.counts.rows_scanned,311833243);
  assert.equal(Object.keys(cache.bodies).length,229);
  assert.equal(cache.coordinate_check.samples.length,50);
  assert.deepEqual(raw.position_sources,{soma:11011,tosoma:32,synapse_centroid:228});
  const ids=[...index.root_ids,...raw.non_replay_readouts];
  const {frame}=raw;
  let vnc=0;
  for(const [body,point] of Object.entries(cache.bodies)) {
    assert.ok(point.n_all>=point.n_post && point.n_all>0);
    assert.equal(point.used,point.n_post>0?'post':'all');
    const i=ids.indexOf(body);
    assert.ok(i>=0,body);
    const expected=['x','y'].map((axis,k)=>Math.min(1,Math.max(0,
      (point[axis]*(frame.flip[k]?-1:1)-frame.lo[k])*frame.scale+frame.offset[k])));
    const actual=[neurons.xy[2*i]/65535,neurons.xy[2*i+1]/65535];
    assert.ok(Math.abs(actual[0]-expected[0])<=1/65535,body);
    if(actual[1]>=.96-1/65535) vnc++;
    else assert.ok(Math.abs(actual[1]-expected[1])<=1/65535,body);
  }
  assert.equal(vnc,7);
  assert.equal(raw.position_sources_all.synapse_centroid,229);
  assert.ok(!('placeholder_y' in frame));
});

test('every dish has a male trial-0 replay with exact indexed primary MN9 counts', () => {
  const manifest = json('../data/replay_male/manifest.json');
  const lookup = buildLookup(json('../data/lookup_table_male.json'));
  const index = json('../../data/replay_neurons_male.json');
  const neurons = decodeNeurons(json('../data/neurons_male.json'));
  const primary = neurons.named.find(g => g.key === 'mn9').cells.find(c=>c.root_id==='10331');
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
  const occupied = new Set(json('../../data/dishes.json').map(d => cellIdFor(lookup.get(d))));
  assert.deepEqual(new Set(parsed.keys()), occupied);
  assert.equal(manifest.n_cells, parsed.size);
});
