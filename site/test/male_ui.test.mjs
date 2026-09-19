// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import {buildDictionary, decide, shareParams, parseShareParams, cardLines, flySelection, fliesDisagree, bothVerdict, STRINGS, fmt} from '../app.js';
import {FlyPanel} from '../panel.js';
import {loadSprites} from '../fly.js';

const item = (name, hz) => ({name, entry:{key:name,display:{en:name,zh:name},sugar:'none',bitter:'none',water:'none'}, cell:{mn9_mean:hz}, sugarOnly:{mn9_mean:hz}});
const decision = (a=10,b=0,mode='ask') => decide([item('bread',a),item('steak',b)],mode);

test('female share query stays byte-identical, including opposite and seed ordering', () => {
  const d = decision(10,0,'opposite'); d.shareSeed=42;
  assert.equal(shareParams(d,'en'), '?v=2&d=k.bread,k.steak&lang=en&m=opposite&seed=42');
  assert.equal(shareParams(d,'en','female'), shareParams(d,'en'));
});
test('male and both share queries round trip; legacy and unknown fly values default to female', () => {
  for (const fly of ['male','both']) {
    const query=shareParams(decision(),'zh',fly);
    assert.ok(query.endsWith('&f='+fly));
    assert.equal(parseShareParams(query).fly,fly);
  }
  for (const q of ['?d=bread,steak','?d=bread,steak&f=unknown']) assert.equal(flySelection(parseShareParams(q).fly),'female');
});
test('selector restores only valid persisted values and accepts explicit changes', () => {
  assert.equal(flySelection(), 'female');
  for(const v of ['female','male','both']) assert.equal(flySelection(v),v);
  for(const v of [null,'',{},'MALE']) assert.equal(flySelection(v),'female');
});
test('disagreement compares outcome sets, distinguishes ties and handles opposite allocations', () => {
  assert.equal(fliesDisagree(decision(),decision(20,1)),false);
  assert.equal(fliesDisagree(decision(),decision(0,10)),true);
  assert.equal(fliesDisagree(decision(),decision(0,0)),true);
  assert.equal(fliesDisagree(decision(1,1),decision(0,0)),false);
  for(const mode of ['ask','opposite']) {
    const a=decide([item('a',10),item('b',1),item('c',0)],mode);
    const b=decide([item('c',0),item('b',2),item('a',20)],mode);
    assert.equal(fliesDisagree(a,b),false);
  }
});
test('both verdict selects agree/disagree/opposite copy and appends tie note', () => {
  for(const lang of ['en','zh']) for(const mode of ['ask','opposite']) {
    const a=decision(10,0,mode), b=decision(0,10,mode), t=STRINGS[lang];
    const suffix=mode==='opposite'?'Opposite':'';
    assert.equal(bothVerdict(a,a,lang),fmt(t.verdictBoth['agree'+suffix],{dish:mode==='opposite'?'steak':'bread'}));
    assert.equal(bothVerdict(a,b,lang),fmt(t.verdictBoth['disagree'+suffix],{female:mode==='opposite'?'steak':'bread',male:mode==='opposite'?'bread':'steak'}));
    assert.ok(bothVerdict(a,decision(0,0,mode),lang).endsWith(t.verdictBoth.tieNote));
  }
});
test('both flies with no known dish retain the existing no-result wording', () => {
  const d=decide([{name:'unknown',entry:null,cell:null}],'ask');
  for(const lang of ['en','zh']) assert.equal(bothVerdict(d,d,lang),STRINGS[lang].verdictNone);
});
test('cardLines adds the named fly without changing female fixed lines', () => {
  const d=decision();
  assert.equal(cardLines(d,'en','male').fly,fmt(STRINGS.en.card.flyLine,{fly:STRINGS.en.flyName.male,dish:'bread'}));
  assert.deepEqual(cardLines(d,'en','female'),cardLines(d,'en'));
});
test('FlyPanel binds its own sources and replay loader; scored flags never cross panels', async () => {
  const calls=[];
  const female=new FlyPanel(null,{flyKey:'female',lookup:{id:1},loadReplay:async id=>{calls.push(['female',id]);return 1;}});
  const male=new FlyPanel(null,{flyKey:'male',lookup:{id:2},loadReplay:async id=>{calls.push(['male',id]);return 2;},neuropils:null});
  assert.equal(await female.loadReplay('a'),1); assert.equal(await male.loadReplay('a'),2);
  assert.deepEqual(calls,[['female','a'],['male','a']]);
  assert.equal(male.neuropils,null);
  const entries=[{...item('bread',1).entry,sugar:'high'},item('steak',2).entry];
  female.bindSources({lookup:{get:levels=>({mn9_mean:levels.sugar==='high'?10:0})}});
  male.bindSources({lookup:{get:levels=>({mn9_mean:levels.sugar==='high'?0:10})}});
  const dictionary=buildDictionary(entries);
  female.score(['bread','steak'],dictionary,'ask',42);
  male.score(['bread','steak'],dictionary,'ask',42);
  assert.equal(female.decision.winner.entry.key,'bread');
  assert.equal(male.decision.winner.entry.key,'steak');
  assert.equal(female.decision.shareSeed,male.decision.shareSeed);
  female.scored[0].loading=true;
  assert.equal(male.scored[0].loading,undefined);
  male.bindSources({flyKey:'male',lookup:{id:3},loadReplay:async()=>3});
  assert.equal(male.lookup.id,3); assert.equal(await male.loadReplay('a'),3);
});

test('fly sprite prefix is independent of shared dish assets; default paths are unchanged', async () => {
  const calls=[];
  const loader=async src=>{calls.push(src);return {src};};
  const sprites=await loadSprites('assets/',loader,'assets/fly_male/');
  assert.equal(sprites.base,'assets/');
  assert.ok(calls.every(src=>src.startsWith('assets/fly_male/')));
  assert.equal(sprites.fly.idle[0].src,'assets/fly_male/fly/idle_1.png');
  calls.length=0;
  await loadSprites('assets/',loader);
  assert.ok(calls.includes('assets/fly/idle_1.png'));
  assert.ok(calls.includes('assets/response/eats_1.png'));
});

test('panel replay loader failures propagate rather than yielding an empty replay', async () => {
  const panel=new FlyPanel(null,{flyKey:'male',loadReplay:async()=>{throw Error('missing male replay');}});
  await assert.rejects(panel.loadReplay('cell'),/missing male replay/);
});
