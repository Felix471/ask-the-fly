// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildLookup, slugFor} from '../app.js';
import {speechLine} from '../taste_states.js';
const json = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
const menu = json('../data/menu.json');
const dictionary = json('../data/dishes.json');
const female = json('../data/lookup_table_v1_2.json');
const male = json('../data/lookup_table_male.json');
const base = json('../data/lookup_table.json');
const sections = json('../data/sections.json').sections;
const byKey = new Map(menu.dishes.map(d=>[d.key,d]));

test('menu projects every shipped dish, lookup cell and speech line', () => {
  assert.equal(menu.schema,'menu_v1');
  assert.equal(menu.dishes.length,279);
  assert.deepEqual(menu.dishes.map(d=>d.key),dictionary.map(d=>d.key));
  const lookups={female:buildLookup(female),male:buildLookup(male)};
  const baseLookup=buildLookup(base);
  for(const [i,dish] of menu.dishes.entries()){
    const source=dictionary[i];
    assert.equal(dish.slug,slugFor(dish.key));
    assert.deepEqual(dish.levels,Object.fromEntries(['sugar','bitter','water','ir94e'].map(k=>[k,source[k]??'none'])));
    assert.equal(dish.not_food,Boolean(sections[dish.section].not_food));
    for(const fly of ['female','male']){
      const cell=lookups[fly].get(dish.levels);
      for(const [key,field] of [['mn9','mn9_mean'],['mn11d','mn11d_mean'],['mn11v','mn11v_mean'],['state','state']])
        assert.equal(dish[fly][key],cell[field],dish.key+' '+fly+' '+key);
      for(const lang of ['zh','en']) assert.equal(dish[fly].line[lang],speechLine(cell.state,dish.levels,dish.seed,lang));
    }
    assert.equal(dish.female.mn9,baseLookup.get(dish.levels).mn9_mean);
  }
  for(const cell of female.cells) assert.equal(cell.mn9_mean,baseLookup.get(cell).mn9_mean);
});
test('ranks are competition ranks, with complete cutoff ties',()=>{
  for(const fly of ['female','male']){
    const ordered=[...menu.dishes].sort((a,b)=>b[fly].mn9-a[fly].mn9);
    let rank=0,last=null;
    ordered.forEach((dish,index)=>{if(dish[fly].mn9!==last){rank=index+1;last=dish[fly].mn9;}assert.equal(dish[fly].rank,rank);});
    const tiers=menu.lists[fly+'_top'];
    const keys=tiers.flatMap(t=>t.keys);
    assert.ok(keys.length>=10);
    assert.deepEqual(keys,ordered.slice(0,keys.length).map(d=>d.key));
    assert.ok(!ordered[keys.length] || ordered[keys.length][fly].mn9<ordered[keys.length-1][fly].mn9);
    for(const tier of tiers) for(const key of tier.keys){
      assert.equal(byKey.get(key)[fly].rank,tier.rank);assert.equal(byKey.get(key)[fly].mn9,tier.mn9);
    }
  }
  const diff=d=>Math.abs(d.female.rank-d.male.rank);
  const divergence=menu.lists.divergence.flatMap(t=>t.keys);
  assert.ok(divergence.length>=10);
  assert.ok(divergence.every(key=>diff(byKey.get(key))>0));
  for(const tier of menu.lists.divergence) for(const key of tier.keys) assert.equal(diff(byKey.get(key)),tier.diff);
  assert.ok(!menu.dishes.some(d=>diff(d)>diff(byKey.get(divergence[0]))));
  for(const fly of ['female','male']){
    const keys=menu.lists.not_food[fly].flatMap(t=>t.keys);
    assert.equal(keys.length,23);
    assert.deepEqual(new Set(keys),new Set(menu.dishes.filter(d=>d.not_food).map(d=>d.key)));
    for(const tier of menu.lists.not_food[fly]) for(const key of tier.keys) assert.equal(byKey.get(key)[fly].rank,tier.rank);
  }
  assert.equal(menu.lists.section_tops.length,sections.length);
  menu.lists.section_tops.forEach((top,index)=>{for(const fly of ['female','male']){
    const members=menu.dishes.filter(d=>d.section===index);
    const max=Math.max(...members.map(d=>d[fly].mn9));
    assert.equal(top[fly].mn9,max);
    assert.deepEqual(top[fly].keys,members.filter(d=>d[fly].mn9===max).map(d=>d.key));
  }});
});

