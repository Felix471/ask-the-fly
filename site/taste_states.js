// SPDX-License-Identifier: MIT
// Designed presentation only. Ranking and allocation remain in decide().
import { FLY_LINES } from './fly_lines.js';
export const STATE_KEYS = { eats: 'Eats', mouth_moves: 'MouthMoves', proboscis_only: 'ProboscisOnly', no_response: 'NoResponse' };
export const EMOTIONS = { eats: 'happy', mouth_moves: 'sweat', proboscis_only: 'deadpan', no_response: 'deadpan' };
export const RESPONSE_SEQUENCE = {
  eats: [[0,250],[1,180],[2,220],[3,220],[2,220],[3,220],[2,220],[3,220],[0,500]],
  mouth_moves: [[0,250],[1,220],[2,250],[1,220],[0,380],[1,220],[2,250],[3,600]],
  proboscis_only: [[0,200],[1,120],[2,80],[3,160],[0,600]],
  no_response: [[0,250],[1,180],[2,180],[1,180],[2,180],[1,180],[3,250]],
};
export function readoutState(cell) {
  if (!cell || !Number.isFinite(cell.mn9_mean) || !Number.isFinite(cell.mn11d_mean)) return null;
  return cell.mn9_mean >= 5 ? (cell.mn11d_mean >= 5 ? 'eats' : 'proboscis_only') : (cell.mn11d_mean >= 5 ? 'mouth_moves' : 'no_response');
}
export function stateLabel(cell, strings) {
  const key = STATE_KEYS[readoutState(cell)];
  return key ? strings.stateV12[key + 'Label'] : '—';
}
export function stateExplanation(cell, strings) {
  const key = STATE_KEYS[readoutState(cell)];
  return key ? strings.stateV12[key + 'Explanation'] : '';
}
export function validSeed(seed) { return Number.isSafeInteger(seed) && seed >= 0; }
export function speechBucket(state, levels) {
  const canonical = { ...levels, water: levels.water === 'medium' ? 'low' : levels.water };
  const bucket = FLY_LINES.buckets.find(b => b.state === state && Object.entries(b.when).every(([axis, allowed]) => allowed.includes(canonical[axis])));
  if (!bucket) throw new Error(`No speech bucket: ${state}`);
  return bucket;
}
export function speechLine(state, levels, seed, lang) {
  if (!validSeed(seed) || !['en','zh'].includes(lang)) throw new Error('Invalid speech seed/language');
  return speechBucket(state, levels)[lang][seed % 3];
}
export function finalSpeechContext(decision) {
  if (!decision.flyPick) return null;
  if (decision.flyTies.length > 1 || decision.tie.length) return 'tie';
  const state = readoutState(decision.flyPick.cell);
  if (state === 'no_response') return null; // Owner: leave without an ownership line.
  return decision.mode === 'opposite' ? 'eats_first' : state;
}
