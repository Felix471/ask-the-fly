// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {buildDictionary, buildLookup, scoreOptions, decide, shareParams, flySelection} from '../app.js';
import {readoutState} from '../taste_states.js';
import {cellIdFor} from '../brain.js';

// Generated once from tag-verified v1.2.1 inputs by freeze_female_decisions.py.
const FIXTURE_SHA256 = '518f4e7739995b39ba398d9adfdfc0410ae3a9e43341484953a02b085ee12baa';
const json = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));

test('female v1.2.1: immutable fixture covers every dish and both modes of every pair', () => {
  const bytes = readFileSync(new URL('./fixtures/female_v1_2_1_decisions.json', import.meta.url));
  assert.ok(bytes.length < 1_000_000);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), FIXTURE_SHA256);
  const fixture = JSON.parse(bytes);
  const female = flySelection('female');
  assert.equal(female, 'female');
  const dictionary = buildDictionary(json('../data/dishes.json'));
  const lookup = buildLookup(json('../data/lookup_table_v1_2.json'));
  assert.equal(fixture.dishes.length, 174); // Frozen reference set, not the live dictionary size.
  const scored = scoreOptions(fixture.dishes.map(d => d[0]), dictionary, lookup);
  assert.equal(scored.length, fixture.dishes.length);
  assert.deepEqual(scored.map(d => [d.entry.key, cellIdFor(d.cell), d.cell.mn9_mean, readoutState(d.cell)]), fixture.dishes);
  const pairs = [];
  for (let i = 0; i < scored.length; i++) for (let j = i + 1; j < scored.length; j++) {
    const input = [scored[i], scored[j]];
    const mask = items => items.reduce((bits, item) => bits | (1 << input.indexOf(item)), 0);
    pairs.push(['ask', 'opposite'].map(mode => {
      const d = decide(input, mode);
      return [input.indexOf(d.winner), input.indexOf(d.flyPick), mask(d.tie), mask(d.flyTies), mask(d.humanSet)];
    }));
  }
  assert.equal(pairs.length, 15051);
  assert.deepEqual(pairs, fixture.pairs);
});

test('female v1.2.1: real-dish share query stays byte-identical', () => {
  const dictionary = buildDictionary(json('../data/dishes.json'));
  const lookup = buildLookup(json('../data/lookup_table_v1_2.json'));
  const d = decide(scoreOptions(['bread', 'steak'], dictionary, lookup), 'opposite');
  d.shareSeed = 42;
  assert.equal(shareParams(d, 'en', 'female'), '?v=2&d=k.bread,k.steak&lang=en&m=opposite&seed=42');
});
