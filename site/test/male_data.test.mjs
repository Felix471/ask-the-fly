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
  assert.equal(parsed.size, 55);
  assert.equal(manifest.n_cells, parsed.size);
});
