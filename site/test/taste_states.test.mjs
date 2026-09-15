import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {readoutState,speechBucket,speechLine,finalSpeechContext} from '../taste_states.js';
import {FLY_LINES} from '../fly_lines.js';
import {parseShareParams,shareParams,decide,buildLookup,buildDictionary,scoreOptions} from '../app.js';
import {parseReplay,rasterRows,decodeNeurons,cellIdFor} from '../brain.js';
const json=path=>JSON.parse(readFileSync(new URL(path,import.meta.url),'utf8'));
const table=json('../../data/lookup_table_v1_2.json');
const old=json('../../data/lookup_table.json');
const lines=json('../../copy/fly_lines.json');
test('generated speech copy matches the owner copy source',()=>assert.deepEqual(FLY_LINES,lines));
test('all 400 v1.2 packs preserve original MN9 header bytes and event bytes; four MN11 raster rows are exact',()=>{
  const neurons=decodeNeurons(json('../data/neurons.json'));
  for(const cell of table.cells){
    const name=cellIdFor(cell)+'.bin';
    const before=readFileSync(new URL('../data/replay/'+name,import.meta.url));
    const after=readFileSync(new URL('../data/replay_v1_2/'+name,import.meta.url));
    const source=readFileSync(new URL('../../data/replay_v1_2/'+name,import.meta.url));
    assert.deepEqual(after,source);
    const ah=after.subarray(8,8+after.readUInt32LE(4)).toString();
    const bh=before.subarray(8,8+before.readUInt32LE(4)).toString();
    const mn9Tokens=h=>h.match(/"mn9_[^"]+"\s*:\s*(?:\[[^\]]*\]|[^,}]+)/g);
    assert.deepEqual(mn9Tokens(ah),mn9Tokens(bh),name);
    assert.deepEqual(after.subarray(8+after.readUInt32LE(4)),before.subarray(8+before.readUInt32LE(4)),name);
    const replay=parseReplay(after.buffer.slice(after.byteOffset,after.byteOffset+after.byteLength));
    const rows=rasterRows(replay,neurons,{}).filter(r=>r.key.startsWith('MN11'));
    assert.equal(rows.length,4);
    for(const type of ['MN11D','MN11V'])for(const c of replay.header.readout_rows[type].cells){
      const row=rows.find(r=>r.key===`${type}:${c.root_id}`);
      assert.deepEqual(row.times,Float32Array.from(c.spike_ms));
    }
  }
});

test('v1.2 all 400 states and first-match speech buckets, three deterministic bilingual lines',()=>{
  assert.equal(table.cells.length,400);
  for(const cell of table.cells){
    assert.equal(readoutState(cell),cell.state);
    const canonical={...cell,water:cell.water==='medium'?'low':cell.water};
    const expected=lines.buckets.filter(b=>b.state===cell.state).find(b=>Object.entries(b.when).every(([k,v])=>v.includes(canonical[k])));
    assert.equal(speechBucket(cell.state,cell).id,expected.id);
    for(const lang of ['zh','en'])for(let seed=0;seed<6;seed++)assert.equal(speechLine(cell.state,cell,seed,lang),expected[lang][seed%3]);
  }
});
test('v1.2 threshold is inclusive and MN11V/right MN9 cannot decide state',()=>{
  assert.equal(readoutState({mn9_mean:5,mn11d_mean:5}),'eats');
  assert.equal(readoutState({mn9_mean:4.99,mn11d_mean:5,mn11v_mean:999,mn9_r_mean:999}),'mouth_moves');
  assert.equal(readoutState({mn9_mean:5,mn11d_mean:4.99}),'proboscis_only');
  assert.equal(readoutState({mn9_mean:0,mn11d_mean:0}),'no_response');
});
test('v1.2 all 174 dish scores and pairwise decisions match frozen product',()=>{
  const dictionary=buildDictionary(json('../../data/dishes.json'));
  const names=dictionary.entries.map(d=>d.key);
  const a=scoreOptions(names,dictionary,buildLookup(old)),b=scoreOptions(names,dictionary,buildLookup(table));
  assert.equal(a.length,174);
  for(let i=0;i<a.length;i++)for(let j=i+1;j<a.length;j++)for(const mode of ['ask','opposite']){
    const before=decide([a[i],a[j]],mode),after=decide([b[i],b[j]],mode);
    for(const key of ['winner','flyPick'])assert.equal(before[key]?.name,after[key]?.name);
    for(const key of ['tie','flyTies','humanSet'])assert.deepEqual(before[key].map(d=>d.name),after[key].map(d=>d.name));
  }
});
test('v1.2 no-response final UI never claims ownership; tie remains tie',()=>{
  const pick={name:'a',cell:{mn9_mean:1,mn11d_mean:0}};
  const other={name:'b',cell:{mn9_mean:0,mn11d_mean:0}};
  assert.equal(finalSpeechContext(decide([pick,other],'opposite')),null);
  assert.equal(finalSpeechContext(decide([other,{...other,name:'c'}],'ask')),'tie');
});
test('share seed round trips without affecting legacy links',()=>{
  const d=decide([{name:'one',entry:{key:'one'},cell:{mn9_mean:10}}],'ask');
  d.shareSeed=4294967295;
  assert.equal(parseShareParams(shareParams(d,'zh')).seed,d.shareSeed);
  for(const query of ['?d=one','?d=one&seed=-1','?d=one&seed=NaN','?d=one&seed=9007199254740992'])assert.equal(parseShareParams(query).seed,undefined);
});
