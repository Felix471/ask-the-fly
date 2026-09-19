// SPDX-License-Identifier: MIT
// Ask the Fly — static front end. No LLM calls: dictionary lookup + lookup-table read.
// Pure functions are exported so they can be unit-tested with node (see test/).

import { cellIdFor, decodeNeurons, makeReplayLoader } from "./brain.js";
import { IdleFly, loadDishSprite, loadSprites } from "./fly.js";
import { FlyPanel } from './panel.js';
import { qrcode } from "./vendor/qrcode-generator/qrcode.mjs";
import { readoutState, stateLabel, stateExplanation, validSeed } from './taste_states.js';

export const LEVELS = ["none", "low", "medium", "high", "very_high"];
export const DIMENSIONS = ["sugar", "bitter", "water", "ir94e"];

// Set this to the public repository once it exists; the report button opens a prefilled issue there.
export const REPO_URL = "https://github.com/Felix471/ask-the-fly";

import { STRINGS } from "./strings.js";
export { STRINGS };

export function fmt(template, values) {
  return template.replace(/\{(\w+)\}/g, (_, key) => (key in values ? String(values[key]) : `{${key}}`));
}

// Mirrors encoder/normalize.py: NFKC, lowercase, trim, collapse internal whitespace.
export function normalizeName(name) {
  return String(name).normalize("NFKC").trim().toLowerCase().replace(/\s+/g, " ");
}

export function buildDictionary(entries) {
  const index = new Map();
  const slugs = new Map(); // sprite slug (share links, file names) -> entry
  for (const entry of entries) {
    const names = [entry.key, ...(entry.aliases || [])];
    for (const name of names) {
      const key = normalizeName(name);
      if (key && !index.has(key)) index.set(key, entry);
    }
    if (!slugs.has(slugFor(entry.key))) slugs.set(slugFor(entry.key), entry);
  }
  return {
    entries,
    find(name) {
      return index.get(normalizeName(name)) || null;
    },
    findSlug(slug) {
      return slugs.get(String(slug).toLowerCase()) || null;
    },
  };
}

export function hzKey(levels, hz) {
  return DIMENSIONS.map((dimension) => Number(hz[dimension])).join("|");
}

// Mirrors sim/lookup.py: cells are indexed by their Hz vector, so level names
// that share a rate (water low and medium, both 60 Hz) resolve to one cell.
export function buildLookup(table) {
  const byHz = new Map();
  for (const cell of table.cells) byHz.set(hzKey(table.levels, cell.hz), cell);
  if (byHz.size !== table.cells.length) throw new Error("Lookup table contains duplicate cells");
  return {
    table,
    get(selected) {
      const hz = {};
      for (const dimension of DIMENSIONS) {
        const name = selected[dimension] ?? "none";
        if (!(name in table.levels[dimension])) {
          throw new Error(`Unknown ${dimension} level ${name}`);
        }
        hz[dimension] = table.levels[dimension][name];
      }
      const cell = byHz.get(hzKey(table.levels, hz));
      if (!cell) throw new Error(`Lookup cell is absent: ${JSON.stringify(selected)}`);
      return cell;
    },
  };
}

export function ir94eLevel(entry) {
  return entry && entry.ir94e ? entry.ir94e : "none";
}

export function scoreOptions(names, dictionary, lookup) {
  return names.map((name) => {
    const entry = dictionary.find(name);
    if (!entry) return { name, entry: null, cell: null };
    const cell = lookup.get({ sugar: entry.sugar, bitter: entry.bitter, water: entry.water, ir94e: ir94eLevel(entry) });
    // "Sugar response" = the same dish with bitter = none AND ir94e = none.
    const sugarOnly = lookup.get({ sugar: entry.sugar, bitter: "none", water: entry.water, ir94e: "none" });
    return { name, entry, cell, sugarOnly };
  });
}

// mode: "ask" picks the highest MN9; "opposite" picks the lowest, and also
// reports what the fly itself would have picked. Ties are reported as ties.
// flyTies: every option sharing the maximum MN9 (what the fly cannot tell
// apart; the animation hovers between them). selectionTies: the options tied
// under the human rule (ask: the maximum set; opposite: the minimum set); the
// result view and the card report them. `tie` is an alias of selectionTies.
// Sorting is stable and ties are never broken at random: flyPick is the first
// maximum in input order (F07).
export function decide(scored, mode) {
  const known = scored.filter((item) => item.cell);
  const misses = scored.filter((item) => !item.cell);
  if (known.length === 0) return { mode, winner: null, flyPick: null, tie: [], flyTies: [], selectionTies: [], known, misses };
  const by = (sign) => [...known].sort((a, b) => sign * (b.cell.mn9_mean - a.cell.mn9_mean));
  const highest = by(1);
  const lowest = by(-1);
  const flyPick = highest[0];
  const chosen = mode === "opposite" ? lowest[0] : flyPick;
  const sameAs = (ref) => known.filter((item) => Math.abs(item.cell.mn9_mean - ref.cell.mn9_mean) < 1e-9);
  const flyTies = sameAs(flyPick);
  const lowestSet = sameAs(lowest[0]);
  if (mode === "opposite") {
    // The fly takes its top pick (every dish tied at the maximum); everything
    // else is the human's. One remaining dish: the classic two-dish outcome.
    // Two or more remaining: no single winner among them (`many`). None
    // remaining: everything was tied, reported as a tie.
    const humanSet = highest.filter((item) => !flyTies.includes(item));
    const many = humanSet.length >= 2;
    const single = humanSet.length === 1 ? humanSet[0] : null;
    const allTied = humanSet.length === 0;
    return {
      mode,
      winner: single,
      flyPick,
      flyTies: flyTies.length > 1 ? flyTies : [],
      selectionTies: allTied ? flyTies : [],
      tie: allTied ? flyTies : [],
      humanSet,
      many,
      lowest: lowestSet,
      known,
      misses,
    };
  }
  const selectionTies = sameAs(chosen);
  return {
    mode,
    winner: chosen,
    flyPick,
    flyTies: flyTies.length > 1 ? flyTies : [],
    selectionTies: selectionTies.length > 1 ? selectionTies : [],
    tie: selectionTies.length > 1 ? selectionTies : [],
    humanSet: [],
    many: false,
    lowest: lowestSet,
    known,
    misses,
  };
}

// Designed threshold (ours, not the model's): below 5 Hz MN9 the fly's own pick
// is called "least uninteresting". Copy only; decisions and ties are unchanged.
export const LOW_INTEREST_HZ = 5;
export function lowInterest(decision, threshold = LOW_INTEREST_HZ) {
  const pick = decision && decision.flyPick;
  return Boolean(pick && pick.cell && pick.cell.mn9_mean < threshold);
}

// The fly's animation plan for a decision: taste every known dish in order,
// then land on the fly's own pick, or hover between the fly's ties.
export function scenePlan(decision, scored) {
  const indexOf = (item) => scored.indexOf(item);
  return {
    order: decision.known.map(indexOf),
    winner: decision.flyPick ? indexOf(decision.flyPick) : null, // the fly lands on its own pick in every mode
    tie: decision.flyTies.map(indexOf),
  };
}

// The recorded run the brain shows when the fly makes its final landing: the
// plate it lands on (plan.winner, the fly's own pick in every mode), unless the
// brain already shows that cell because it was the last plate tasted. Null for
// ties (the fly hovers; the brain keeps the last tasted run) and for no pick.
export function finalLanding(plan, scored, currentCellId) {
  if (plan.winner == null || (plan.tie && plan.tie.length > 1)) return null;
  const item = scored[plan.winner];
  if (!item || !item.cell) return null;
  const cellId = cellIdFor(item.cell);
  return cellId === currentCellId ? null : { index: plan.winner, cellId };
}

// Levenshtein distance with an early cutoff (characters, so CJK works too).
export function editDistance(a, b, cutoff = 2) {
  if (Math.abs(a.length - b.length) > cutoff) return cutoff + 1;
  const prev = new Array(b.length + 1);
  const cur = new Array(b.length + 1);
  for (let j = 0; j <= b.length; j += 1) prev[j] = j;
  for (let i = 1; i <= a.length; i += 1) {
    cur[0] = i;
    let rowMin = cur[0];
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      if (cur[j] < rowMin) rowMin = cur[j];
    }
    if (rowMin > cutoff) return cutoff + 1;
    for (let j = 0; j <= b.length; j += 1) prev[j] = cur[j];
  }
  return prev[b.length];
}

// Names a dictionary entry can be found under: key, both display names, aliases.
export function entryNames(entry) {
  return [...new Set([entry.key, entry.display?.zh, entry.display?.en, ...(entry.aliases || [])].filter(Boolean).map(normalizeName))];
}

// Fuzzy suggestions: prefix matches first, then substring, then edit distance <= 2
// (on the whole name or on any word of it). Returns at most `max` entries, each with
// the label to show in `lang` and the matched name.
export function suggest(query, dictionary, lang, max = 6) {
  const q = normalizeName(query);
  if (!q) return [];
  // Typo tolerance grows with the query: for Latin text none under 3 characters,
  // 1 up to 5, then 2; CJK names are short, so one edit is allowed from 2 characters.
  const cjk = /[㐀-鿿]/.test(q);
  const tolerance = Math.min(2, Math.floor(q.length / (cjk ? 2 : 3)));
  const scored = [];
  for (const entry of dictionary.entries) {
    let best = null;
    for (const name of entryNames(entry)) {
      let rank = null;
      if (name.startsWith(q)) rank = 0;
      else if (name.includes(q)) rank = 1;
      else if (tolerance > 0) {
        const d = Math.min(editDistance(q, name, tolerance), ...name.split(" ").map((w) => editDistance(q, w, tolerance)));
        if (d <= tolerance) rank = 2 + d;
      }
      if (rank !== null && (best === null || rank < best.rank || (rank === best.rank && name.length < best.name.length))) {
        best = { rank, name };
      }
    }
    if (best) scored.push({ entry, rank: best.rank, name: best.name, label: entry.display?.[lang] || entry.key });
  }
  scored.sort((a, b) => a.rank - b.rank || a.name.length - b.name.length || a.label.localeCompare(b.label));
  return scored.slice(0, max);
}

// Closest entries when nothing matches within the fuzzy rules (edit distance <= 4).
export function closest(query, dictionary, lang, max = 3) {
  const q = normalizeName(query);
  if (!q) return [];
  const cutoff = Math.min(3, Math.floor(q.length / 2));
  if (cutoff === 0) return [];
  const scored = [];
  for (const entry of dictionary.entries) {
    let d = Infinity;
    for (const name of entryNames(entry)) d = Math.min(d, editDistance(q, name, cutoff), ...name.split(" ").map((w) => editDistance(q, w, cutoff)));
    if (d <= cutoff) scored.push({ entry, d, label: entry.display?.[lang] || entry.key });
  }
  scored.sort((a, b) => a.d - b.d || a.label.localeCompare(b.label));
  return scored.slice(0, max);
}

// Opens the "New dish request" issue form (.github/ISSUE_TEMPLATE/dish-request.yml);
// query keys are the form's field ids, so the issue arrives structured.
export function issueUrl(name, lang) {
  const t = STRINGS[lang] || STRINGS.en;
  const params = new URLSearchParams({
    template: "dish-request.yml",
    title: fmt(t.issueTitle, { name }),
    name_typed: name,
    language: lang === "zh" ? "zh" : "en",
  });
  return `${REPO_URL}/issues/new?${params.toString()}`;
}

export function displayName(item, lang) {
  if (item.entry && item.entry.display && item.entry.display[lang]) return item.entry.display[lang];
  return item.name;
}

// The four fixed lines and the front-bottom line, filled for a decision.
// Ties are exact (same grid cell): the pick shows every tied name and the
// shared cell's numbers. With no known option every placeholder is "—".
export function cardLines(decision, lang, fly = decision.fly || 'female') {
  const t = STRINGS[lang];
  const names = t.levelNames;
  const picked = decision.tie.length ? decision.tie : decision.many ? [decision.flyPick] : decision.winner ? [decision.winner] : [];
  const lead = picked[0];
  const values = lead
    ? {
        dish: picked.map((item) => displayName(item, lang)).join(" / "),
        hz: lead.cell.mn9_mean.toFixed(1),
        hz_sugar_only: lead.sugarOnly.mn9_mean.toFixed(1),
        sugar: names[lead.entry.sugar] ?? lead.entry.sugar,
        bitter: names[lead.entry.bitter] ?? lead.entry.bitter,
        water: names[lead.entry.water] ?? lead.entry.water,
        ir94e: names[ir94eLevel(lead.entry)] ?? ir94eLevel(lead.entry),
      }
    : Object.fromEntries(["dish", "hz", "hz_sugar_only", "sugar", "bitter", "water", "ir94e"].map((k) => [k, t.cardEmptyValue]));
  return { fixed: t.fixedLines.map((line) => fmt(line, values)), bottom: t.cardHonesty,
    ...(fly === 'male' ? {fly: fmt(t.card.flyLine, {fly:t.flyName.male,dish:values.dish})} : {}) };
}

export function flySelection(value) {
  return ['female', 'male', 'both'].includes(value) ? value : 'female';
}

function outcomeItems(decision) {
  if (decision.tie.length) return decision.tie;
  if (decision.mode === 'opposite') return decision.humanSet || [];
  return decision.winner ? [decision.winner] : [];
}

export function fliesDisagree(female, male) {
  const signature = d => JSON.stringify([Boolean(d.tie.length), outcomeItems(d).map(i => i.entry?.key || i.name).sort()]);
  return signature(female) !== signature(male);
}

export function bothVerdict(female, male, lang) {
  const t = STRINGS[lang];
  if (!female.flyPick && !male.flyPick) return t.verdictNone;
  const label = d => outcomeItems(d).map(i => displayName(i, lang)).join(' / ') || t.cardEmptyValue;
  const key = (fliesDisagree(female, male) ? 'disagree' : 'agree') + (female.mode === 'opposite' ? 'Opposite' : '');
  const text = fmt(t.verdictBoth[key], {dish:label(female),female:label(female),male:label(male)});
  return text + ((female.tie.length || male.tie.length || female.flyTies.length || male.flyTies.length) ? ' ' + t.verdictBoth.tieNote : '');
}

// Footer "what's new" line from site/data/release.json: `v1.1.1 · 2026-09-12 · summary`,
// the version linking to CHANGELOG.md on GitHub. Null when the file is missing or malformed.
export function releaseLine(release, lang, strings = STRINGS) {
  if (!release || typeof release.version !== "string" || !/^v\d+\.\d+\.\d+$/.test(release.version)) return null;
  if (typeof release.date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(release.date)) return null;
  const t = strings[lang] || strings.en;
  const summary = typeof release.summary_key === "string" ? t[release.summary_key] : null;
  if (!summary) return null;
  const href = typeof release.changelog_url === "string" && /^https:\/\//.test(release.changelog_url)
    ? release.changelog_url : `${REPO_URL}/blob/main/CHANGELOG.md`;
  return { version: release.version, date: release.date, summary, href, text: `${release.version} · ${release.date} · ${summary}` };
}

// ---------- share links ----------

// Canonical public URL; the page overrides it from site/config.json at load.
export const SITE_URL = "https://askthefly.app/";

// Commits recorded by data files before the 2026-09-11 history rewrite (commit
// trailers stripped), mapped to the same commits' current hashes. The lookup
// table keeps the hash its run wrote; the footer shows the current one.
// Mapping documented in docs/site.md and docs/grid_provenance.md.
export const COMMIT_REWRITE = {
  "4d66cfcc6d080da46e316bf57dabe30132e0d5eb": "01a798e042a412edcb44f482ec6c9706c585d767",
};

export function currentCommit(hash) {
  return COMMIT_REWRITE[hash] || hash || "";
}

// One neutral plate for every dish without a sprite (typed, unknown dishes).
export const PLACEHOLDER_PLATE = "data:image/svg+xml," + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><ellipse cx="16" cy="19" rx="13" ry="6" fill="#ebe4d8" stroke="#cfc5b6"/><ellipse cx="16" cy="18" rx="8" ry="3.4" fill="#f6f1e8" stroke="#ded5c6"/></svg>'
);

export function slugFor(key) {
  return String(key).normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "dish";
}

// Share links, format v2: `?v=2&d=<item>,<item>,…&lang=zh|en[&m=opposite]`.
// Each item is typed: `k.<slug>` for a dictionary dish, `t.<encodeURIComponent(text)>`
// for typed unknown text. Items are joined with "," after encoding, so commas,
// "&", "%" and non-ASCII inside a text survive; the `d` value is read from
// the raw query string, not through URLSearchParams (which would decode
// before splitting). Old v1 links (`?d=slug,slug` without `v`) still parse.
// A link re-runs the choice against the current data; it is not a snapshot.
export const SHARE_LIMITS = { maxItems: 20, maxTextLength: 80 };

function shareItemsFor(decision) {
  return [...decision.known, ...decision.misses].slice(0, SHARE_LIMITS.maxItems).map((item) => (
    item.entry ? { kind: "key", value: slugFor(item.entry.key) } : { kind: "text", value: String(item.name).trim().slice(0, SHARE_LIMITS.maxTextLength) }
  ));
}

export function shareParams(decision, lang, fly = decision.fly || 'female') {
  const parts = shareItemsFor(decision).map((item) => (item.kind === "key" ? `k.${item.value}` : `t.${encodeURIComponent(item.value)}`));
  let query = `?v=2&d=${parts.join(",")}&lang=${lang === "zh" ? "zh" : "en"}`;
  if (decision.mode === "opposite") query += "&m=opposite";
  if (validSeed(decision.shareSeed)) query += `&seed=${decision.shareSeed}`;
  if (flySelection(fly) !== 'female') query += `&f=${flySelection(fly)}`;
  return query;
}

export function shareUrl(decision, lang, base = SITE_URL) {
  return (base.endsWith("/") ? base : base + "/") + shareParams(decision, lang);
}

function safeDecode(text) {
  try { return decodeURIComponent(text); } catch (_) { return null; }
}

// Returns { version, items: [{kind: "key"|"text", value}], lang, mode } or null
// for a link that carries no usable list (missing, empty, unknown version,
// undecodable). Items beyond the limits are dropped or truncated.
export function parseShareParams(search) {
  const raw = String(search || "").replace(/^\?/, "");
  if (!raw) return null;
  const fields = {};
  for (const pair of raw.split("&")) {
    const eq = pair.indexOf("=");
    const name = eq < 0 ? pair : pair.slice(0, eq);
    if (!(name in fields)) fields[name] = eq < 0 ? "" : pair.slice(eq + 1);
  }
  if (!fields.d) return null;
  const version = fields.v === undefined ? 1 : Number(fields.v);
  if (version !== 1 && version !== 2) return null;
  const items = [];
  for (const part of fields.d.split(",")) {
    if (!part) continue;
    if (version === 2) {
      const kind = part.startsWith("k.") ? "key" : part.startsWith("t.") ? "text" : null;
      if (!kind) return null;
      const value = safeDecode(part.slice(2));
      if (value === null) return null;
      const trimmed = value.trim().slice(0, SHARE_LIMITS.maxTextLength);
      if (trimmed) items.push({ kind, value: trimmed });
    } else {
      const value = safeDecode(part.replace(/\+/g, " "));
      if (value === null) return null;
      const trimmed = value.trim().slice(0, SHARE_LIMITS.maxTextLength);
      if (trimmed) items.push({ kind: "any", value: trimmed });
    }
    if (items.length >= SHARE_LIMITS.maxItems) break;
  }
  if (!items.length) return null;
  const lang = safeDecode(fields.lang || "");
  return {
    version,
    items,
    lang: lang === "zh" || lang === "en" ? lang : null,
    mode: fields.m === "opposite" ? "opposite" : "ask",
    ...(fields.f === 'male' || fields.f === 'both' ? {fly:fields.f} : {}),
    ...(fields.seed !== undefined && /^\d+$/.test(fields.seed) && validSeed(Number(fields.seed)) ? { seed: Number(fields.seed) } : {}),
  };
}

// Turns shared items back into selections. v2: a `key` item resolves through
// the slug index (an unknown slug stays as typed text), a `text` item is always
// text, never upgraded to a dish. v1 (`any`): slug, then name, then hyphens as
// spaces, else text.
export function resolveShared(items, dictionary) {
  return items.map((item) => {
    if (item.kind === "text") return { text: item.value };
    const name = item.value;
    const entry = item.kind === "key"
      ? (dictionary.findSlug(name) || dictionary.find(name))
      : (dictionary.find(name) || dictionary.findSlug(name) || dictionary.find(name.replace(/-/g, " ")));
    return entry ? { key: entry.key } : { text: name };
  });
}

// "sugar low · bitter none · water high · amino acids medium" for a lookup cell or dictionary entry,
// in the page's language; the raw cell id stays in the details HUD.
export function levelsText(levels, lang) {
  const t = STRINGS[lang] || STRINGS.en;
  const name = (level) => t.levelNames[level] ?? level;
  return fmt(t.levelsLine, { sugar: name(levels.sugar), bitter: name(levels.bitter), water: name(levels.water), ir94e: name(levels.ir94e ?? "none") });
}

// ---------- silencing statistics (D08) ----------
// Percentages that sum to 100 after rounding (largest remainder), median as
// text with the sign kept. Input: a manifest variant_stats entry.
export function silenceStats(st) {
  const fracs = [st.frac_up || 0, st.frac_down || 0, st.frac_zero || 0];
  const raw = fracs.map((f) => f * 100);
  const floors = raw.map(Math.floor);
  let rest = 100 - floors.reduce((a, b) => a + b, 0);
  const order = raw.map((v, i) => [v - floors[i], i]).sort((a, b) => b[0] - a[0]);
  for (const [, i] of order) { if (rest <= 0) break; floors[i] += 1; rest -= 1; }
  const median = st.median_delta == null ? "–" : (st.median_delta > 0 ? "+" : "") + String(st.median_delta);
  return { n: st.n_cells_mn9_active ?? 0, median, up: floors[0], down: floors[1], same: floors[2] };
}

// Recomputes a variant's MN9 delta distribution from the manifest cells:
// scope "active" = cells where the baseline MN9 fired (the stored stats'
// scope), "all" = every recorded cell.
export function silenceStatsFrom(manifest, variant, scope = "active") {
  const deltas = [];
  for (const cell of Object.values(manifest.cells)) {
    const before = cell.mn9_left_count;
    const after = cell[`mn9_left_count_${variant}`];
    if (typeof after !== "number") continue;
    if (scope === "active" && !(before > 0)) continue;
    deltas.push(after - before);
  }
  const sorted = [...deltas].sort((a, b) => a - b);
  const n = sorted.length;
  const medianValue = n ? (n % 2 ? sorted[(n - 1) / 2] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2) : null;
  const fracUp = n ? deltas.filter((d) => d > 0).length / n : 0;
  const fracDown = n ? deltas.filter((d) => d < 0).length / n : 0;
  const fracZero = n ? deltas.filter((d) => d === 0).length / n : 0;
  return { n, medianValue, fracUp, fracDown, fracZero, ...silenceStats({ n_cells_mn9_active: n, median_delta: medianValue, frac_up: fracUp, frac_down: fracDown, frac_zero: fracZero }) };
}

// ---------- selected options ----------
// A selection is { key } for a dictionary dish (stable across languages) or
// { text } for something the user typed that the fly does not know.

export function optionFromText(raw, dictionary) {
  const text = String(raw).trim();
  if (!text) return null;
  const entry = dictionary ? dictionary.find(text) : null;
  return entry ? { key: entry.key } : { text };
}

// The string handed to scoreOptions (a key resolves through the dictionary).
export function optionQuery(option) {
  return option.key ?? option.text;
}

export function optionLabel(option, dictionary, lang) {
  if (!option.key) return option.text;
  const entry = dictionary ? dictionary.find(option.key) : null;
  return entry ? (entry.display?.[lang] || entry.key) : option.key;
}

export function sameOption(a, b) {
  if (a.key || b.key) return a.key === b.key;
  return normalizeName(a.text) === normalizeName(b.text);
}

// ---------- share card (3:4, canvas) ----------

// Breaks CJK text per character (closing punctuation stays with its character) but
// keeps Latin/number runs (LLM, 70.6, Hz) whole.
function wrapLines(ctx, text, maxWidth) {
  const cjk = /[㐀-鿿]/.test(text);
  const tokens = cjk ? (text.match(/[㐀-鿿][、。，）：；！？]*|[^\s㐀-鿿]+|\s+/g) || []) : text.split(" ").map((w, i) => (i ? " " + w : w));
  const lines = [];
  let current = "";
  for (const token of tokens) {
    const candidate = current + token;
    if (ctx.measureText(candidate).width > maxWidth && current.trim()) {
      lines.push(current.trimEnd());
      current = token.trimStart();
    } else {
      current = candidate;
    }
  }
  if (current.trim()) lines.push(current.trimEnd());
  return lines;
}

// Monospace URL wrapped by character count (the card has no word breaks to use).
function wrapChars(text, perLine) {
  const lines = [];
  for (let i = 0; i < text.length; i += perLine) lines.push(text.slice(i, i + perLine));
  return lines;
}

// Greyscale copy of a sprite, done per pixel so it also works where canvas
// filters are unsupported.
function greyscaleSprite(img, size) {
  const off = document.createElement("canvas");
  off.width = size;
  off.height = size;
  const c = off.getContext("2d");
  c.imageSmoothingEnabled = false;
  c.drawImage(img, 0, 0, size, size);
  const data = c.getImageData(0, 0, size, size);
  const p = data.data;
  for (let i = 0; i < p.length; i += 4) {
    const l = Math.round(0.299 * p[i] + 0.587 * p[i + 1] + 0.114 * p[i + 2]);
    p[i] = p[i + 1] = p[i + 2] = l;
  }
  c.putImageData(data, 0, 0);
  return off;
}

// A dish sprite (drawn with its own plate) at x, y with a soft shadow; `struck`
// draws it greyscale at 40% with a thin line through the plate.
function drawDish(ctx, img, x, y, size, struck) {
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(x + size / 2, y + size * 0.82, size * 0.5, size * 0.13, 0, 0, Math.PI * 2);
  ctx.fillStyle = struck ? "rgba(0, 0, 0, 0.05)" : "rgba(0, 0, 0, 0.10)";
  ctx.fill();
  ctx.imageSmoothingEnabled = false;
  if (img) {
    if (struck) {
      ctx.globalAlpha = 0.4;
      ctx.drawImage(greyscaleSprite(img, size), x, y, size, size);
      ctx.globalAlpha = 1;
    } else {
      ctx.drawImage(img, x, y, size, size);
    }
  } else {
    // No sprite: plate and a neutral circle, like the scene's placeholder.
    ctx.globalAlpha = struck ? 0.4 : 1;
    ctx.beginPath();
    ctx.ellipse(x + size / 2, y + size * 0.7, size * 0.48, size * 0.2, 0, 0, Math.PI * 2);
    ctx.fillStyle = "#f4efe7";
    ctx.strokeStyle = "#d8cfc2";
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x + size / 2, y + size * 0.55, size * 0.26, 0, Math.PI * 2);
    ctx.fillStyle = struck ? "#9a928a" : "#c9a86a";
    ctx.fill();
    ctx.globalAlpha = 1;
  }
  if (struck) {
    ctx.strokeStyle = "rgba(31, 26, 23, 0.75)";
    ctx.lineWidth = Math.max(2, Math.round(size / 40));
    ctx.beginPath();
    ctx.moveTo(x + size * 0.04, y + size * 0.66);
    ctx.lineTo(x + size * 0.96, y + size * 0.66);
    ctx.stroke();
  }
  ctx.restore();
}

// The fly sprite, proboscis fully out, sitting on a dish drawn at x, y, size.
function drawFlyOn(ctx, frames, x, y, size, proboscis) {
  const list = frames && (proboscis ? frames.proboscis : frames.idle);
  const frame = list && list[list.length - 1];
  const fs = Math.round(size * 0.52);
  const fx = x + size * 0.5 - fs * 0.42;
  const fy = y + size * 0.18 - fs * 0.35;
  ctx.save();
  ctx.imageSmoothingEnabled = false;
  if (frame) {
    ctx.drawImage(frame, fx, fy, fs, fs);
  } else {
    ctx.fillStyle = "#2a2420";
    ctx.beginPath();
    ctx.ellipse(fx + fs / 2, fy + fs / 2, fs * 0.22, fs * 0.12, 0, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawResponseFly(ctx, sprites, item, x, y, size) {
  const response = readoutState(item?.cell);
  if (response === 'no_response') return;
  const list = sprites?.responses?.[response];
  if (!list) return drawFlyOn(ctx, sprites?.fly, x, y, size, response !== 'mouth_moves');
  const fs = Math.round(size * 0.65);
  ctx.save();ctx.imageSmoothingEnabled=false;
  ctx.drawImage(list[response === 'proboscis_only' ? 2 : response === 'mouth_moves' ? 1 : 2], x+size*0.5-fs*0.65,y-fs*0.12,fs,fs);
  ctx.restore();
}

function drawQr(ctx, text, x, y, size) {
  const qr = qrcode(0, "M");
  qr.addData(text);
  qr.make();
  const n = qr.getModuleCount();
  const quiet = 4; // modules of quiet zone, per the QR spec
  const cell = Math.max(1, Math.floor(size / (n + quiet * 2)));
  const total = cell * (n + quiet * 2);
  const ox = x + Math.floor((size - total) / 2);
  const oy = y + Math.floor((size - total) / 2);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(ox, oy, total, total);
  ctx.fillStyle = "#1f1a17";
  for (let r = 0; r < n; r += 1) {
    for (let c = 0; c < n; c += 1) {
      if (qr.isDark(r, c)) ctx.fillRect(ox + (c + quiet) * cell, oy + (r + quiet) * cell, cell, cell);
    }
  }
  return { x: ox, y: oy, size: total, modules: n };
}

// The result view's main image: the chosen dish with the fly on it, the other
// dishes small, greyed and struck beside it (same treatment as the card). Ties
// draw every tied dish in colour; in "opposite" the fly's own pick keeps the
// fly. Sizes are CSS px; the canvas is scaled by options.pixelRatio.
export function drawResultHero(canvas, decision, lang, options = {}) {
  const pr = options.pixelRatio || 1;
  const width = options.width || 360;
  const spriteFor = options.spriteFor || (() => null);
  const flyFrames = options.sprites ? options.sprites.fly : null;
  const many = Boolean(decision.many);
  const chosen = many ? decision.humanSet : decision.winner ? (decision.tie.length ? decision.tie : [decision.winner]) : [];
  const ranked = [...decision.known].sort((a, b) => b.cell.mn9_mean - a.cell.mn9_mean);
  const others = ranked.filter((item) => !chosen.includes(item));
  const big = chosen.length > 1 ? Math.min(120, Math.floor((width - 16 * (chosen.length + 1)) / chosen.length)) : 150;
  const small = 64;
  const gap = 16;
  const top = chosen.length > 1 && !many ? Math.round(big * 0.2) : 0; // room for the hovering fly in a tie
  const height = top + (chosen.length ? big + 12 : 0) + (others.length ? small + 34 : 0) + 8;
  canvas.width = Math.round(width * pr);
  canvas.height = Math.round(height * pr);
  canvas.style.height = `${height}px`;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(pr, 0, 0, pr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const font = (size, weight = 400) =>
    `${weight} ${size}px system-ui, -apple-system, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif`;
  let y = top;
  if (chosen.length) {
    const rowWidth = chosen.length * big + (chosen.length - 1) * gap;
    const x0 = (width - rowWidth) / 2;
    if (chosen.length > 1 && !many) drawFlyOn(ctx, flyFrames, width / 2 - big / 2, y - big * 0.16, big, false);
    chosen.forEach((item, i) => {
      const x = x0 + i * (big + gap);
      drawDish(ctx, spriteFor(item), x, y, big, false);
      if (chosen.length === 1 && decision.mode !== "opposite") drawResponseFly(ctx, options.sprites, item, x, y, big);
    });
    y += big + 12;
  }
  if (others.length) {
    const maxCols = Math.max(1, Math.floor((width + 12) / (small + 12)));
    const shown = others.slice(0, maxCols);
    const rowWidth = shown.length * small + (shown.length - 1) * 12;
    let x = (width - rowWidth) / 2;
    ctx.textAlign = "center";
    for (const item of shown) {
      const flyPick = decision.mode === "opposite" && (item === decision.flyPick || decision.flyTies.includes(item));
      // Two dishes: the fly's pick keeps its colour. Three or more: it is taken (greyed, struck) with the fly on it.
      drawDish(ctx, spriteFor(item), x, y, small, !flyPick || many);
      if (flyPick) drawResponseFly(ctx, options.sprites, item, x, y, small);
      ctx.font = font(12, flyPick ? 600 : 400);
      ctx.fillStyle = flyPick ? "#1f1a17" : "#9a928a";
      const label = displayName(item, lang);
      const short = ctx.measureText(label).width > small + 10 ? wrapLines(ctx, label, small + 10)[0] : label;
      ctx.fillText(short, x + small / 2, y + small + 16);
      x += small + 12;
    }
    if (others.length > shown.length) {
      ctx.font = font(12);
      ctx.fillStyle = "#9a928a";
      ctx.fillText(fmt(STRINGS[lang].cardMore, { n: others.length - shown.length }), width / 2, y + small + 32);
    }
    ctx.textAlign = "left";
  }
  return canvas;
}

// options: stub, sprites ({ fly, dishCache }), spriteFor(item) -> image | null,
// snapshot ({ canvas, mn9, neurons }) -> a brain frame drawn left of the QR code,
// siteUrl -> base of the QR link (default SITE_URL).
// Card content: title, headline, the chosen name, the chosen sprite with the
// fly, the MN9 bar comparison, the MN9 line, one honesty sentence, then the
// brain snapshot and the QR code with its short URL. The taste levels and the
// other fixed lines live in the page's details, not on the card.
export function drawShareCard(canvas, decision, lang, options = {}) {
  const t = STRINGS[lang];
  const both = Boolean(options.maleDecision);
  if (both && options.contentScale === undefined) {
    // Measure the two blocks before painting. Long names and opposite-mode
    // allocations need variable space; the QR keeps its full size and quiet zone.
    const measure = document.createElement('canvas');
    measure.width=canvas.width; measure.height=canvas.height;
    const bottom = drawShareCard(measure,decision,lang,{...options,contentScale:1,measureOnly:true});
    const contentScale = Math.min(1,(canvas.height-374-120)/Math.max(1,bottom-120));
    return drawShareCard(canvas,decision,lang,{...options,contentScale});
  }
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  const pad = 64;
  const spriteFor = options.spriteFor || (() => null);
  const flyFrames = options.sprites ? options.sprites.fly : null;
  ctx.fillStyle = options.stub ? "#fff3c4" : "#fbf8f2";
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = "#b5471f";
  ctx.fillRect(0, 0, W, 18);

  const font = (size, weight = 400) =>
    `${weight} ${size}px system-ui, -apple-system, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif`;
  // Display tier on the card: the title and the chosen dish name (pixel fonts,
  // self-hosted; the caller waits for document.fonts before drawing).
  const display = (size, weight = 400) =>
    `${weight} ${size}px "Pixelify Sans", "Fusion Pixel", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", system-ui, sans-serif`;
  const mono = (size) => `${size}px ui-monospace, Menlo, Consolas, "Courier New", monospace`;

  // Header: title, headline, the chosen name(s).
  ctx.fillStyle = "#1f1a17";
  ctx.font = display(50, 700);
  ctx.textAlign = "left";
  ctx.fillText(t.cardTitle, pad, 108);
  if (both) {
    ctx.save();
    ctx.translate(W/2,120);
    ctx.scale(options.contentScale,options.contentScale);
    ctx.translate(-W/2,-120);
  }
  let y = both ? 142 : 172;
  if (both) {
    ctx.font = font(22, 600);
    ctx.fillText(t.flyName.female, pad, y);
    y += 30;
  }
  ctx.font = font(27);
  ctx.fillStyle = "#6b625b";
  let headline;
  const many = Boolean(decision.many);
  if (!decision.flyPick) headline = t.verdictNone;
  else if (decision.tie.length) headline = t.cardTie;
  else if (readoutState(decision.flyPick.cell) === 'no_response') headline = t.sceneNoResponse;
  else if (many) headline = "";
  else if (decision.mode === "opposite") headline = fmt(t.cardOppositePicked, { fly_pick: displayName(decision.flyPick, lang), human_pick: displayName(decision.winner, lang) });
  else headline = t.cardPicked;
  if (decision.fly === 'male') headline = cardLines(decision, lang, 'male').fly;
  for (const line of wrapLines(ctx, headline, W - 2 * pad - (both ? 108 : 0))) {
    ctx.fillText(line, pad, y);
    y += 36;
  }
  const chosen = many ? decision.humanSet : decision.winner ? (decision.tie.length ? decision.tie : [decision.winner]) : [];
  if (many) {
    // The sentence is the title; a small second line names the fly's least favourite.
    ctx.fillStyle = "#1f1a17";
    ctx.font = display(40, 700);
    for (const line of wrapLines(ctx, readoutState(decision.flyPick.cell) === 'no_response' ? stateLabel(decision.flyPick.cell, t) : fmt(t.cardOppositeMany, { fly_pick: displayName(decision.flyPick, lang) }), W - 2 * pad - (both ? 108 : 0))) {
      y += 48;
      ctx.fillText(line, pad, y);
    }
    ctx.font = font(24);
    ctx.fillStyle = "#6b625b";
    y += 34;
    ctx.fillText(fmt(t.oppositeLeast, { lowest: decision.lowest.map((i) => displayName(i, lang)).join(" / ") }), pad, y);
  } else if (chosen.length) {
    ctx.fillStyle = "#1f1a17";
    ctx.font = display(both ? 38 : chosen.length > 1 ? 44 : 56, 700);
    const names = chosen.map((i) => displayName(i, lang)).join(" / ");
    for (const line of wrapLines(ctx, names, W - 2 * pad - (both ? 108 : 0))) {
      y += both ? 44 : chosen.length > 1 ? 50 : 62;
      ctx.fillText(line, pad, y);
    }
  }
  y += 24;

  // Bottom block is fixed: brain snapshot left, QR code right. Everything above
  // shares the rest: sprite, bars, MN9 line, honesty sentence.
  const qrSize = 220;
  const qrX = W - pad - qrSize;
  const bottomEstimate = H - 330; // reserve QR + four URL lines inside the canvas

  // The chosen dish with the fly on it (ties: every tied dish, fly hovering above).
  const ranked = [...decision.known].sort((a, b) => b.cell.mn9_mean - a.cell.mn9_mean);
  const barRows = Math.min(ranked.length, 4);
  const rowHeight = 66;
  const barsHeight = ranked.length ? 16 + barRows * rowHeight + (ranked.length > barRows ? 28 : 0) : 0;
  const lines = cardLines(decision, lang);
  ctx.font = font(21);
  const mn9TextHeight = wrapLines(ctx, lines.fixed[1], W - 2 * pad).length * 28;
  ctx.font = font(19, 600);
  const textBlock = 12 + mn9TextHeight + wrapLines(ctx, lines.bottom, W - 2 * pad).slice(0,3).length * 26;
  const opposite = decision.mode === "opposite" && decision.flyPick && !chosen.includes(decision.flyPick);
  const spriteTop = chosen.length > 1 && !many ? 30 : 0; // only ties need hover room
  const spriteTail = opposite ? (options.tablecloth ? 78 : 44) : (options.tablecloth ? 30 : 16);
  const maleHeight = both ? 68 + Math.min(options.maleDecision.known.length, 4) * 38 + (options.maleDecision.known.length > 4 ? 24 : 0) + (fliesDisagree(decision, options.maleDecision) ? 30 : 0) : 0;
  const spriteRoom = Math.max(0, bottomEstimate - 44 - textBlock - barsHeight - y - spriteTop - spriteTail - maleHeight);
  if (both && chosen.length && spriteRoom < 64) {
    // A small header sprite retains the female depiction when both tables use
    // the vertical space normally available for its large dish illustration.
    const size = 78;
    const x = W - pad - size;
    drawDish(ctx, spriteFor(opposite ? decision.flyPick : chosen[0]), x, 174, size, false);
    drawResponseFly(ctx, options.sprites, decision.flyPick, x, 174, size);
  }
  if (chosen.length && spriteRoom >= 64) {
    const gap = 24;
    // Everything on one row: the human's dishes, plus the fly's pick at 0.56x when
    // it stands beside them; the row (and the tablecloth patch around it) fits
    // inside the margins.
    const slots = chosen.length + (opposite ? 0.56 : 0);
    const fitWidth = Math.floor((W - 2 * pad - 72 - (opposite ? 28 : 0) - gap * (chosen.length - 1)) / Math.max(1, slots));
    const bigSize = Math.min(chosen.length > 1 ? Math.min(180, fitWidth) : Math.min(250, fitWidth), spriteRoom);
    const flyExtra = opposite ? Math.round(bigSize * 0.56) + 28 : 0;
    const rowWidth = chosen.length * bigSize + (chosen.length - 1) * gap;
    const x0 = (W - rowWidth - flyExtra) / 2;
    const sy = y + spriteTop;
    const shift = 0;
    // Tablecloth only behind the sprites; every line of text stays on solid cream.
    if (options.tablecloth) {
      const padX = 36;
      const padY = 22;
      const bx = x0 - padX;
      const bw = rowWidth + flyExtra + 2 * padX;
      const by = sy - padY - (chosen.length > 1 ? bigSize * 0.16 : bigSize * 0.1);
      const bh = bigSize + 2 * padY + (chosen.length > 1 ? bigSize * 0.16 : bigSize * 0.1) + (opposite ? 30 : 0);
      ctx.save();
      ctx.beginPath();
      if (typeof ctx.roundRect === "function") ctx.roundRect(bx, by, bw, bh, 18); else ctx.rect(bx, by, bw, bh);
      ctx.fillStyle = options.tablecloth;
      ctx.fill();
      ctx.strokeStyle = "#d9c6a8";
      ctx.lineWidth = 3;
      ctx.stroke();
      ctx.restore();
    }
    if (chosen.length > 1 && !many) drawFlyOn(ctx, flyFrames, W / 2 - bigSize / 2, sy - bigSize * 0.16, bigSize, false);
    chosen.forEach((item, i) => {
      const x = x0 + shift + i * (bigSize + gap);
      drawDish(ctx, spriteFor(item), x, sy, bigSize, false);
      if (chosen.length === 1 && !opposite) drawResponseFly(ctx, options.sprites, item, x, sy, bigSize);
    });
    if (opposite) {
      // The human's dishes stay large; the fly sits on its own pick beside them
      // (taken: greyed and struck when the human keeps several dishes).
      const small = Math.round(bigSize * 0.56);
      const x = x0 + shift + rowWidth + 28;
      const yy = sy + bigSize - small;
      drawDish(ctx, spriteFor(decision.flyPick), x, yy, small, many);
      drawResponseFly(ctx, options.sprites, decision.flyPick, x, yy, small);
      ctx.font = font(20, 600);
      ctx.fillStyle = "#1f1a17";
      ctx.textAlign = "center";
      ctx.fillText(displayName(decision.flyPick, lang), x + small / 2, yy + small + 24);
      ctx.textAlign = "left";
    }
    y = sy + bigSize + (opposite ? (options.tablecloth ? 78 : 44) : (options.tablecloth ? 30 : 16));
  }

  // Bars carry the numbers: one shared scale, the chosen dish in the accent.
  const scale = Math.max(100, ...ranked.map((item) => item.cell.mn9_mean));
  const trackWidth = W - 2 * pad;
  const shown = ranked.slice(0, barRows);
  y += 16;
  for (const item of shown) {
    const isChosen = chosen.includes(item);
    ctx.font = font(22, isChosen ? 700 : 400);
    ctx.fillStyle = isChosen ? "#b5471f" : "#1f1a17";
    ctx.textAlign = "left";
    ctx.fillText(displayName(item, lang), pad, y);
    ctx.textAlign = "right";
    ctx.fillText(fmt(t.hzValue, { hz: item.cell.mn9_mean.toFixed(1) }), W - pad, y);
    ctx.textAlign = "left";
    const barY = y + 10;
    ctx.fillStyle = "#e2dbd0";
    ctx.fillRect(pad, barY, trackWidth, 10);
    const width = Math.max(0, Math.round((item.cell.mn9_mean / scale) * trackWidth));
    ctx.fillStyle = isChosen ? "#b5471f" : "#1f1a17";
    if (width > 0) ctx.fillRect(pad, barY, width, 10);
    if (readoutState(item.cell)) {
      ctx.font = font(16);
      ctx.fillStyle = '#51463e';
      ctx.fillText(fmt(t.cardReadouts, {state:stateLabel(item.cell,t),d:item.cell.mn11d_mean.toFixed(1),v:item.cell.mn11v_mean.toFixed(1)}),pad,y+40);
    }
    y += rowHeight;
  }
  if (ranked.length > shown.length) {
    ctx.font = font(20);
    ctx.fillStyle = "#6b625b";
    ctx.fillText(fmt(t.cardMore, { n: ranked.length - shown.length }), pad, y);
    y += 28;
  }

  if (both) {
    const male = options.maleDecision;
    const items = [...male.known].sort((a,b)=>b.cell.mn9_mean-a.cell.mn9_mean);
    const maleChosen = outcomeItems(male);
    const pick = maleChosen.map(i=>displayName(i,lang)).join(' / ') || t.cardEmptyValue;
    y += 16;
    ctx.font = font(22, 700);
    ctx.fillStyle = '#1f1a17';
    const title = fmt(t.card.flyLine,{fly:t.flyName.male,dish:pick});
    for (const line of wrapLines(ctx,title,W-2*pad-80)) {ctx.fillText(line,pad,y);y+=28;}
    if(male.flyPick) drawResponseFly(ctx,options.maleSprites,male.flyPick,W-pad-65,y-40,60);
    y += 8;
    const maleScale = Math.max(100,...items.map(i=>i.cell.mn9_mean));
    for(const item of items.slice(0,4)) {
      ctx.font=font(18,maleChosen.includes(item)?700:400);
      ctx.fillStyle=maleChosen.includes(item)?'#b5471f':'#1f1a17';
      ctx.fillText(displayName(item,lang),pad,y);
      ctx.textAlign='right';ctx.fillText(fmt(t.hzValue,{hz:item.cell.mn9_mean.toFixed(1)}),W-pad,y);ctx.textAlign='left';
      ctx.fillStyle='#e2dbd0';ctx.fillRect(pad,y+7,trackWidth,6);
      ctx.fillStyle=maleChosen.includes(item)?'#b5471f':'#1f1a17';
      ctx.fillRect(pad,y+7,item.cell.mn9_mean/maleScale*trackWidth,6);
      y+=38;
    }
    if(items.length>4){ctx.font=font(18);ctx.fillText(fmt(t.cardMore,{n:items.length-4}),pad,y);y+=24;}
    y+=8;
  }

  // The MN9 line and the one honesty sentence.
  y += 6;
  ctx.font = font(21);
  ctx.fillStyle = "#1f1a17";
  for (const part of wrapLines(ctx, lines.fixed[1], W - 2 * pad)) {
    ctx.fillText(part, pad, y);
    y += 28;
  }
  y += 6;
  if (both && fliesDisagree(decision,options.maleDecision)) {
    ctx.font=font(17,600);ctx.fillStyle='#b5471f';
    // The approved short disagreement copy fits on one line in both languages.
    ctx.fillText(t.card.disagree,pad,y,W-2*pad);
    y+=30;
  }
  ctx.font = font(19, 600);
  ctx.fillStyle = "#b5471f";
  for (const part of wrapLines(ctx, lines.bottom, W - 2 * pad).slice(0, 3)) {
    ctx.fillText(part, pad, y);
    y += 26;
  }
  if (both) {
    ctx.restore();
    if (options.measureOnly) return y;
    y = 120 + (y-120)*options.contentScale;
  }

  // Bottom block: brain snapshot with its caption, QR code with its URL. It
  // starts right under the text and the snapshot grows into whatever is left,
  // so it stays readable.
  const bottomTop = Math.max(y + 44, Math.min(bottomEstimate, H - 330));
  ctx.fillStyle = "#e2dbd0";
  ctx.fillRect(pad, bottomTop - 34, W - 2 * pad, 2);
  if (options.snapshot) {
    const snap = options.snapshot;
    const aspect = snap.canvas.height / snap.canvas.width;
    const maxW = qrX - 28 - pad;
    const maxH = H - 64 - 46 - bottomTop; // caption line under it, margin below
    const snapW = Math.max(200, Math.min(maxW, Math.floor(maxH / aspect)));
    const snapH = Math.round(snapW * aspect);
    const snapX = pad;
    const snapY = bottomTop;
    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(snap.canvas, snapX, snapY, snapW, snapH);
    ctx.restore();
    ctx.strokeStyle = "#e2dbd0";
    ctx.lineWidth = 1;
    ctx.strokeRect(snapX - 0.5, snapY - 0.5, snapW + 1, snapH + 1);
    ctx.font = font(16);
    ctx.fillStyle = "#6b625b";
    ctx.textAlign = "left";
    const neurons = typeof snap.neurons === "number" ? snap.neurons.toLocaleString(lang === "zh" ? "zh-CN" : "en-US") : "\u2014";
    const caption = fmt(t.cardSnapshot, { n: snap.mn9, neurons });
    let cy = snapY + snapH + 26;
    for (const part of wrapLines(ctx, caption, snapW).slice(0, 2)) {
      ctx.fillText(part, snapX, cy);
      cy += 21;
    }
  }

  const url = shareUrl(decision, lang, options.siteUrl || SITE_URL);
  const qr = drawQr(ctx, url, qrX, bottomTop, qrSize);
  ctx.font = font(15);
  ctx.fillStyle = "#6b625b";
  ctx.textAlign = "center";
  ctx.fillText(t.cardScan, qr.x + qr.size / 2, qr.y - 8);
  ctx.font = mono(13);
  ctx.fillStyle = "#1f1a17";
  const shortUrl = url.replace(/^https?:\/\//, "");
  let uy = qr.y + qr.size + 22;
  for (const part of wrapChars(shortUrl, 27).slice(0, 4)) {
    ctx.fillText(part, qr.x + qr.size / 2, uy);
    uy += 17;
  }
  ctx.textAlign = "left";

  if (options.stub) {
    ctx.font = font(20, 700);
    ctx.fillStyle = "#4a3a00";
    ctx.fillText(t.stubStamp, pad, H - 14);
  }
  return canvas;
}

// ---------- DOM wiring (skipped under node) ----------

const isBrowser = typeof document !== "undefined";

if (isBrowser) {
  const state = {
    lang: (() => {
      try {
        const saved = localStorage.getItem("askfly.lang");
        if (saved === "zh" || saved === "en") return saved;
      } catch (_) { /* ignore */ }
      return /^zh/i.test(navigator.language || "") ? "zh" : "en";
    })(),
    options: [], // [{ key } | { text }], see optionFromText
    dictionary: null,
    panels: {female:null,male:null},
    fly: (() => {try {return flySelection(localStorage.getItem('askfly.fly'));} catch (_) {return 'female';}})(),
    spriteFallbacks: {}, sections:null, siteUrl:SITE_URL,
    session:0, shareRequest:0, phase:'input', selectionRequest:0,
    idleFly: null,
  };

  const $ = (id) => document.getElementById(id);
  const primaryRoot = $('scene-panel');
  let secondaryRoot = null;
  const primaryPanel = () => state.fly === 'male' ? state.panels.male : state.panels.female;
  const activePanels = () => (state.fly === 'both' ? [state.panels.female,state.panels.male] : [primaryPanel()]).filter(Boolean);
  const panelHost = {lang:()=>state.lang,selection:()=>state.fly,notice, spriteSlug,skip:skipAll,
    get scrollBehavior(){return scrollBehavior;}};
  state.panels.female = new FlyPanel(primaryRoot, {flyKey:'female', loadReplay:(()=>{
    const baseline=makeReplayLoader('data/replay_v1_2/'),variants=makeReplayLoader('data/replay/');
    return (id,variant)=>variant && variant!=='baseline'?variants(id,variant):baseline(id);
  })()}, panelHost);
  const stringAt = (strings,key) => key.split('.').reduce((value,part)=>value?.[part],strings);
  const reducedMotion = typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const scrollBehavior = reducedMotion ? "auto" : "smooth";
  const tr = (key, values) => fmt(STRINGS[state.lang][key], values || {});
  function notice(key, values) {
    const el = $("notice");
    if (!key) { el.hidden = true; el.textContent = ""; return; }
    el.textContent = tr(key, values);
    el.hidden = false;
  }

  let maleLoading = null;
  async function loadMale() {
    if (state.panels.male?.lookup) return state.panels.male;
    if (maleLoading) return maleLoading;
    maleLoading = (async () => {
      const json = async path => {
        const response = await fetch(path);
        if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
        return response.json();
      };
      const [table, raw, manifest] = await Promise.all([
        json('data/lookup_table_male.json'), json('data/neurons_male.json'), json('data/replay_male/manifest.json'),
      ]);
      // P3-3's approved asset set is pending. The parameterised prefix currently
      // points at the existing female art; dish assets always retain their base.
      const sprites = await loadSprites('assets/', undefined, 'assets/');
      if (!secondaryRoot) {
        secondaryRoot = $('fly-panel-template').content.firstElementChild.cloneNode(true);
        $('fly-panels').append(secondaryRoot);
      }
      const panel = new FlyPanel(secondaryRoot, {
        flyKey:'male', lookup:buildLookup(table), loadReplay:makeReplayLoader('data/replay_male/'),
        neurons:decodeNeurons(raw), placeholderIndexed:raw.placeholder_indexed,
        neuropils:null, manifest, sprites,
      }, panelHost);
      panel.mount();
      state.panels.male = panel;
      const results = $('male-results');
      for (const id of ['table-fly','verdict','result-hero','results-table','card-lines','misses']) {
        const clone = $(id).cloneNode(true);
        clone.id = id+'-male';
        for (const el of clone.querySelectorAll('[id]')) el.id += '-male';
        results.append(clone);
      }
      return panel;
    })();
    try { return await maleLoading; }
    finally { maleLoading = null; }
  }

  function renderFlySelection() {
    for (const radio of document.querySelectorAll('input[name="fly"]')) radio.checked=radio.value===state.fly;
    document.body.classList.toggle('with-both',state.fly==='both');
    $('fly-panels').classList.toggle('panels-both',state.fly==='both');
    for (const el of document.querySelectorAll('.male-how')) el.hidden=state.fly==='female';
    // These existing descriptions explicitly describe the frozen female setup.
    for (const key of ['howP1','howP2','howExtra','ir94eExplain','honesty','provenance']) {
      for (const el of document.querySelectorAll(`[data-i18n="${key}"]`)) el.hidden=state.fly==='male';
    }
    for (const key of ['honesty','provenance']) document.querySelector(`.foot [data-i18n="${key}"]`).hidden=state.fly!=='female';
    for (const key of ['howExtra','ir94eExplain']) document.querySelector(`[data-i18n="${key}"]`).hidden=state.fly!=='female';
    if (primaryPanel()?.lookup) {
      const meta=panel=>{
        const table=panel.lookup.table;
        return fmt(STRINGS[state.lang].tableMeta,{version:table.stub?'stub':currentCommit(table.git_commit).slice(0,7),cells:table.cells.length,trials:table.n_trials_per_cell});
      };
      $('table-meta').textContent=state.fly==='female'?meta(primaryPanel()):activePanels().filter(p=>p.lookup).map(p=>STRINGS[state.lang].flyName[p.flyKey]+' · '+meta(p)).join(' / ');
    }
  }

  async function selectFly(value, persist = true) {
    const request=++state.selectionRequest;
    state.fly=flySelection(value);
    if(persist) {try {localStorage.setItem('askfly.fly',state.fly);} catch (_) { /* storage may be unavailable */ }}
    renderFlySelection();
    if(state.fly!=='female') {
      try {await loadMale();}
      catch(error) {
        console.warn('scene disabled:',error);
        if(request===state.selectionRequest) notice('stateDataFailed');
        return false;
      }
    }
    if(request!==state.selectionRequest) return false;
    // Male-only uses the original DOM block. Switching back restores its female
    // sources; the secondary block is used only for the second fly in both mode.
    const femaleRoot=state.fly==='male'?secondaryRoot:primaryRoot;
    const maleRoot=state.fly==='male'?primaryRoot:secondaryRoot;
    for(const [key,root] of [['female',femaleRoot],['male',maleRoot]]) {
      const panel=state.panels[key];
      if(panel && root && panel.root!==root) {panel.reset();panel.mount(root);}
    }
    for(const panel of Object.values(state.panels).filter(Boolean)) if(panel.neurons) panel.renderStrings();
    renderFlySelection();
    setPhase(state.phase);
    return true;
  }

  for (const radio of document.querySelectorAll('input[name="fly"]')) {
    radio.addEventListener('change',()=>{selectFly(radio.value).catch(error=>{console.warn('fly selection failed:',error);notice('stateDataFailed');});});
  }

  function applyStrings() {
    const t = STRINGS[state.lang];
    document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
    document.title = t.pageTitle;
    for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = stringAt(t,el.dataset.i18n) ?? "";
    for (const el of document.querySelectorAll("[data-i18n-placeholder]")) el.placeholder = t[el.dataset.i18nPlaceholder] ?? "";
    for (const el of document.querySelectorAll("[data-i18n-aria]")) el.setAttribute("aria-label", t[el.dataset.i18nAria] ?? "");
    $("lang-toggle").textContent = state.lang === "zh" ? "EN" : "中文";
    if (primaryPanel()?.lookup) {
      const table = primaryPanel().lookup.table;
      $("table-meta").textContent = fmt(t.tableMeta, {
        version: table.stub ? "stub" : currentCommit(table.git_commit).slice(0, 7),
        cells: table.cells.length,
        trials: table.n_trials_per_cell,
      });
    }
    renderReleaseLine();
    renderOptions();
    renderTasted();
    for (const panel of Object.values(state.panels).filter(Boolean)) if(panel.root && panel.neurons) panel.renderStrings();
    renderFlySelection();
    if (primaryPanel()?.decision) renderDecision(); // text only; the phase is untouched
    if (primaryPanel()?.decision && $('card-dialog').open) showCard().catch(error=>console.warn('share card redraw failed:',error));
  }

  // Footer: latest release only (site/data/release.json), version linked to the changelog.
  function renderReleaseLine() {
    const box = $("release-line");
    box.textContent = "";
    const line = releaseLine(state.release, state.lang);
    if (!line) { box.hidden = true; return; }
    box.hidden = false;
    const link = document.createElement("a");
    link.href = line.href;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = line.version;
    const t = STRINGS[state.lang];
    box.append(link, ` · ${line.date} · ${line.summary} · `);
    const more = document.createElement("a");
    more.href = line.href;
    more.target = "_blank";
    more.rel = "noopener";
    more.textContent = t.releaseLink;
    box.append(more);
  }

  // ---- dish library: a picture menu ----
  // Collapsed: one scrolling row of popular dishes. "View all": search, section
  // tabs and a tile grid. Tiles toggle the selection; a selected tile shows a check.
  const library = { open: false, tab: "all", query: "" };

  function isSelected(key) {
    return state.options.some((o) => o.key === key);
  }

  function toggleSelection(key) {
    const index = state.options.findIndex((o) => o.key === key);
    if (index >= 0) state.options.splice(index, 1);
    else state.options.push({ key });
    renderOptions();
  }

  function makeTile(entry) {
    const tile = document.createElement("button");
    tile.type = "button";
    tile.className = "tile";
    tile.dataset.key = entry.key;
    tile.setAttribute("aria-pressed", isSelected(entry.key) ? "true" : "false");
    tile.append(spriteImg(entry.key, "sprite"));
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = entry.display?.[state.lang] || entry.key;
    tile.title = name.textContent;
    const check = document.createElement("span");
    check.className = "check";
    check.textContent = "✓";
    tile.append(name, check);
    tile.addEventListener("click", () => { toggleSelection(entry.key); closeSuggest(); });
    return tile;
  }

  function renderLibrarySelection() {
    for (const tile of document.querySelectorAll(".tile[data-key]")) {
      tile.setAttribute("aria-pressed", isSelected(tile.dataset.key) ? "true" : "false");
    }
  }

  function librarySections() {
    return state.sections ? state.sections.sections : [];
  }

  function renderTasted() {
    if (!state.dictionary) return;
    const t = STRINGS[state.lang];
    const popularKeys = (state.sections && state.sections.popular) || [];
    const row = $("popular-row");
    row.innerHTML = "";
    for (const key of popularKeys) {
      const entry = state.dictionary.find(key);
      if (entry) row.append(makeTile(entry));
    }
    $("view-all-btn").textContent = library.open ? t.viewLess : t.viewAll;
    $("view-all-btn").setAttribute("aria-expanded", library.open ? "true" : "false");
    $("library-panel").hidden = !library.open;
    $("library-search").placeholder = t.librarySearch;
    if (!library.open) return;
    const tabs = $("library-tabs");
    tabs.innerHTML = "";
    const mkTab = (id, label) => {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", library.tab === id ? "true" : "false");
      b.textContent = label;
      b.addEventListener("click", () => { library.tab = id; renderTasted(); });
      tabs.append(b);
    };
    mkTab("all", t.libraryAll);
    librarySections().forEach((section, i) => mkTab(String(i), state.lang === "zh" ? section.zh : section.en));
    const grid = $("library-grid");
    grid.innerHTML = "";
    const byKey = new Map(state.dictionary.entries.map((e) => [e.key, e]));
    let entries;
    if (library.tab === "all") entries = [...state.dictionary.entries];
    else entries = (librarySections()[Number(library.tab)] || { keys: [] }).keys.map((k) => byKey.get(k)).filter(Boolean);
    if (normalizeName(library.query)) {
      const matched = new Set(suggest(library.query, state.dictionary, state.lang, 1000).map((s) => s.entry.key));
      entries = entries.filter((e) => matched.has(e.key));
    } else {
      const label = (entry) => entry.display?.[state.lang] || entry.key;
      entries.sort((a, b) => label(a).localeCompare(label(b), state.lang === "zh" ? "zh-Hans-CN" : "en"));
    }
    for (const entry of entries) grid.append(makeTile(entry));
    $("library-empty").hidden = entries.length > 0;
  }

  // ---- autocomplete ----
  const suggestState = { items: [], index: -1 };

  function closeSuggest() {
    suggestState.items = [];
    suggestState.index = -1;
    $("suggest").hidden = true;
    $("suggest").innerHTML = "";
    $("option-input").setAttribute("aria-expanded", "false");
  }

  function renderSuggest() {
    const input = $("option-input");
    const box = $("suggest");
    const query = input.value;
    if (!state.dictionary || !normalizeName(query)) { closeSuggest(); return; }
    const items = suggest(query, state.dictionary, state.lang, 6);
    suggestState.items = items;
    suggestState.index = items.length ? 0 : -1;
    box.innerHTML = "";
    if (items.length === 0) {
      const near = closest(query, state.dictionary, state.lang, 3);
      const p = document.createElement("div");
      p.className = "suggest-none";
      if (near.length) {
        p.textContent = "";
        const text = tr("suggestNone", { names: "" });
        p.append(document.createTextNode(text));
        near.forEach((item, i) => {
          const b = document.createElement("b");
          b.textContent = item.label;
          b.style.cursor = "pointer";
          b.addEventListener("mousedown", (event) => { event.preventDefault(); addSelection({ key: item.entry.key }); input.value = ""; closeSuggest(); });
          if (i) p.append(document.createTextNode(" · "));
          p.append(b);
        });
      } else {
        p.textContent = tr("suggestNoneNoClosest");
      }
      box.append(p);
    } else {
      items.forEach((item, i) => {
        const row = document.createElement("div");
        row.className = "suggest-item";
        row.setAttribute("role", "option");
        row.setAttribute("aria-selected", i === suggestState.index ? "true" : "false");
        const main = document.createElement("span");
        main.textContent = item.label;
        const alt = document.createElement("span");
        alt.className = "alt";
        const other = item.entry.display?.[state.lang === "zh" ? "en" : "zh"];
        alt.textContent = other && other !== item.label ? other : (item.name !== normalizeName(item.label) ? item.name : "");
        row.append(main, alt);
        row.addEventListener("mousedown", (event) => { event.preventDefault(); pickSuggest(i); });
        box.append(row);
      });
    }
    box.hidden = false;
    input.setAttribute("aria-expanded", "true");
  }

  function highlightSuggest(index) {
    const rows = $("suggest").querySelectorAll(".suggest-item");
    if (!rows.length) return;
    suggestState.index = (index + rows.length) % rows.length;
    rows.forEach((row, i) => row.setAttribute("aria-selected", i === suggestState.index ? "true" : "false"));
  }

  function pickSuggest(index) {
    const item = suggestState.items[index];
    if (!item) return;
    addSelection({ key: item.entry.key });
    $("option-input").value = "";
    closeSuggest();
    $("option-input").focus();
  }

  function spriteUrlFor(key) {
    if (!key) return PLACEHOLDER_PLATE;
    const slug = slugFor(key);
    return `assets/dishes/${state.spriteFallbacks[slug] || slug}.png`;
  }

  function spriteImg(key, className) {
    const img = document.createElement("img");
    img.className = className;
    img.alt = "";
    img.decoding = "async";
    img.src = spriteUrlFor(key);
    img.addEventListener("error", () => { img.src = PLACEHOLDER_PLATE; }, { once: true });
    return img;
  }

  function renderOptions() {
    const list = $("option-list");
    list.innerHTML = "";
    state.options.forEach((option, index) => {
      const name = optionLabel(option, state.dictionary, state.lang);
      const li = document.createElement("li");
      li.append(spriteImg(option.key, "thumb"));
      const span = document.createElement("span");
      span.textContent = name;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "×";
      remove.setAttribute("aria-label", tr("removeOption", { name }));
      remove.addEventListener("click", () => {
        state.options.splice(index, 1);
        renderOptions();
      });
      li.append(span, remove);
      list.append(li);
    });
    renderLibrarySelection();
    const ready = Boolean(state.panels.female.lookup && state.dictionary);
    $("ask-btn").disabled = !ready;
    $("opposite-btn").disabled = !ready;
    if (state.options.length >= 2) notice(null);
    // Empty table: the one-line hint shows until a dish arrives; the fly rests
    // on the table's edge throughout.
    $("table-empty").hidden = state.options.length > 0;
    if (state.idleFly) { if (reducedMotion) { state.idleFly.stop(); state.idleFly.draw(); } else state.idleFly.start(); }
  }

  function levelText(level) {
    return STRINGS[state.lang].levelNames[level] ?? level;
  }

  function renderDecision() {
    const primary=primaryPanel();
    if(!primary?.decision) return;
    renderPanelDecision(primary);
    $('result-fly').hidden=state.fly==='female';
    $('result-fly').textContent=STRINGS[state.lang].flyName[primary.flyKey]+' · '+STRINGS[state.lang].flySource[primary.flyKey];
    $('disagreement').hidden=true;
    $('male-results').hidden=state.fly!=='both' || !state.panels.male?.decision;
    if(state.fly==='both' && state.panels.male?.decision) {
      renderPanelDecision(state.panels.male, true);
      $('verdict').textContent=bothVerdict(primary.decision,state.panels.male.decision,state.lang);
      $('disagreement').hidden=!fliesDisagree(primary.decision,state.panels.male.decision);
    }
  }

  function renderPanelDecision(panel, secondary = false) {
    const $ = id => document.getElementById(secondary && ['verdict','result-hero','results-body','card-lines','misses','table-fly','results-table'].includes(id) ? id+'-male' : id);
    const t = STRINGS[state.lang];
    const d = panel.decision;
    const verdict = $("verdict");
    verdict.innerHTML = "";
    const lead = document.createElement("span");
    const strong = document.createElement("strong");
    if (!d.flyPick) {
      lead.textContent = t.verdictNone;
    } else if (d.tie.length) {
      lead.textContent = t.verdictTie;
      strong.textContent = d.tie.map((i) => displayName(i, state.lang)).join(" / ");
    } else if (readoutState(d.flyPick.cell) === 'no_response') {
      lead.textContent = t.sceneNoResponse;
      strong.textContent = '';
    } else if (d.mode === "opposite" && d.many) {
      lead.textContent = "";
      strong.textContent = fmt(t.verdictOppositeMany, { fly_pick: displayName(d.flyPick, state.lang) });
      const sub = document.createElement("span");
      sub.className = "verdict-sub";
      sub.textContent = fmt(t.oppositeLeast, { lowest: d.lowest.map((i) => displayName(i, state.lang)).join(" / ") });
      verdict.append(lead, strong, sub);
    } else if (d.mode === "opposite") {
      lead.textContent = "";
      strong.textContent = fmt(t.verdictOpposite, { fly_pick: displayName(d.flyPick, state.lang), human_pick: displayName(d.winner, state.lang) });
    } else {
      lead.textContent = t.verdictAsk;
      strong.textContent = displayName(d.winner, state.lang);
    }
    if (!verdict.contains(strong)) verdict.append(lead, strong);
    if (lowInterest(d)) {
      const sub = document.createElement("span");
      sub.className = "verdict-sub";
      sub.textContent = t.lowInterest;
      verdict.append(sub);
    }
    $("table-fly").hidden = state.fly === 'female';
    $("table-fly").textContent = t.tableFly[panel.flyKey];
    $("results-table").querySelector('[data-i18n="colMn11D"]').textContent = panel.flyKey === 'male' ? t.maleNote.colMn11D : t.colMn11D;
    renderHero(panel, $("result-hero")).catch((error) => console.warn("hero failed:", error));

    const body = $("results-body");
    body.innerHTML = "";
    const ordered = [...d.known].sort((a, b) => b.cell.mn9_mean - a.cell.mn9_mean).concat(d.misses);
    for (const item of ordered) {
      const tr = document.createElement("tr");
      if (item.cell && ((d.winner && (item === d.winner || d.tie.includes(item))) || (d.many && d.humanSet.includes(item)))) tr.className = "win";
      else if (item.cell && d.mode === "opposite" && (item === d.flyPick || d.flyTies.includes(item))) tr.className = "lose";
      else if (!item.cell) tr.className = "miss";
      const name = document.createElement("td");
      name.textContent = displayName(item, state.lang);
      if (item.entry) {
        const sub = document.createElement("span");
        sub.className = "sub";
        sub.textContent = item.entry.display[state.lang === "zh" ? "en" : "zh"] || "";
        name.append(sub);
      }
      tr.append(name);
      if (item.cell) {
        for (const dimension of ["sugar", "bitter", "water", "ir94e"]) {
          const td = document.createElement("td");
          td.textContent = levelText(item.entry[dimension] ?? "none");
          tr.append(td);
        }
        const mn9 = document.createElement("td");
        mn9.className = "mn9";
        mn9.textContent = fmt(t.mn9MeanStd, { mean: item.cell.mn9_mean.toFixed(1), std: item.cell.mn9_std.toFixed(1) }); // `tr` is the table row here
        tr.append(mn9);
        for (const [mean, sd] of [['mn9_r_mean','mn9_r_sd'],['mn11d_mean','mn11d_sd'],['mn11v_mean','mn11v_sd']]) {
          const td = document.createElement('td');
          td.textContent = fmt(t.mn9MeanStd, {mean:item.cell[mean].toFixed(1),std:item.cell[sd].toFixed(1)});
          tr.append(td);
        }
        const response = document.createElement('td');
        response.textContent = stateLabel(item.cell, t);
        response.title = stateExplanation(item.cell, t);
        tr.append(response);
      } else {
        const td = document.createElement("td");
        td.colSpan = 9;
        td.textContent = t.missTitle;
        tr.append(td);
      }
      body.append(tr);
    }

    const cardLinesBox = $("card-lines");
    cardLinesBox.innerHTML = "";
    if (d.flyPick) {
      // Lines 1-3 only: the fourth ("Brain response:") was the label above the
      // card's brain snapshot, which now carries its own caption.
      for (const line of cardLines(d, state.lang).fixed.slice(0, 3)) {
        const li = document.createElement("li");
        li.textContent = line;
        cardLinesBox.append(li);
      }
    }

    const misses = $("misses");
    misses.innerHTML = "";
    for (const item of d.misses) {
      const box = document.createElement("div");
      box.className = "miss-item";
      const text = document.createElement("span");
      text.textContent = `${item.name} — ${t.missTitle}`;
      const link = document.createElement("a");
      link.className = "btn btn-secondary";
      link.href = issueUrl(item.name, state.lang);
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = t.missReport;
      box.append(text, link);
      misses.append(box);
    }

  }

  // The only place that shows or hides the three views. Text re-renders
  // (language switch) never call it (F06).
  function setPhase(phase) {
    state.phase = phase;
    $("input-panel").hidden = phase !== "input";
    for(const panel of Object.values(state.panels).filter(Boolean)) panel.root.hidden=phase==='input' || !activePanels().includes(panel);
    $('fly-panels').hidden=phase==='input';
    $("result-panel").hidden = phase !== "result";
  }

  function showResult() {
    for (const panel of activePanels()) panel.showFinalResponse();
    renderDecision();
    setPhase("result");
  }

  // The winner sprite with the fly is the result's main image, drawn as soon
  // as the sprites are in the cache (the scene loaded them; the card reuses them).
  async function renderHero(panel, canvas) {
    const decision = panel.decision;
    const sprites = panel.sprites;
    if (!decision || !decision.flyPick || !sprites) { canvas.hidden = true; return; }
    await Promise.all(decision.known.map((item) => loadDishSprite(sprites, spriteSlug(item)).catch(() => null)));
    if (panel.decision !== decision) return;
    canvas.hidden = false;
    const width = Math.min(420, canvas.parentElement.clientWidth || 360);
    canvas.style.width = `${width}px`;
    drawResultHero(canvas, decision, state.lang, {
      pixelRatio: Math.min(2, window.devicePixelRatio || 1),
      width,
      sprites,
      spriteFor: (item) => (spriteSlug(item) ? sprites.dishCache.get(spriteSlug(item)) || null : null),
    });
  }

  // Score each experiment separately, then run the active panels concurrently.
  async function run(mode, shareSeed = null) {
    if (!state.panels.female.lookup || !state.dictionary) {notice('stateDataFailed');return;}
    if(state.options.length<2){notice('stateNoOptions');return;}
    notice(null);
    state.session+=1;
    const session=state.session;
    cancelShare();
    const ready=await selectFly(state.fly,false);
    if(session!==state.session || !ready) return;
    const seed=validSeed(shareSeed)?shareSeed:crypto.getRandomValues(new Uint32Array(1))[0];
    for(const panel of activePanels()) {
      panel.reset();
      panel.score(state.options.map(optionQuery),state.dictionary,mode,seed,state.fly);
    }
    if(!primaryPanel().decision.known.length){notice('stateAllUnknown');showResult();return;}
    setPhase('tasting');
    await Promise.all(activePanels().map(async panel=>{
      if(!panel.brain || !panel.scene) return;
      const panelSession=panel.session;
      try {await panel.runScene(panel.decision,panelSession);}
      catch(error){
        console.warn('scene error:',error);
        if(state.session!==session) return;
        panel.el('scene-status').textContent=tr('stateSceneError');
        notice('stateSceneError');
      }
    }));
    if(state.session!==session) return;
    showResult();
  }

  function skipAll() {
    for(const panel of activePanels()) panel.skip();
    if(primaryPanel()?.decision) showResult();
  }

  function spriteSlug(item) {
    return item.entry ? (state.spriteFallbacks[slugFor(item.entry.key)] || slugFor(item.entry.key)) : null;
  }

  // One share request = one immutable (decision, lang, siteUrl) captured up front
  // and an id; only the latest request may draw, set the download link or open
  // the dialog. Close, reset and a newer request cancel older ones. Failures are
  // shown with a retry hint instead of being logged away (F08).
  // The card is drawn only once the display fonts are loaded (preloaded in
  // index.html); a font that never loads falls through after document.fonts
  // settles, so the card still renders with the system fallback.
  async function displayFontsReady(lang) {
    if (!document.fonts) return;
    try {
      const wanted = ['700 56px "Pixelify Sans"', '400 56px "Pixelify Sans"'];
      if (lang === "zh") wanted.push('400 56px "Fusion Pixel"');
      await Promise.all(wanted.map((spec) => document.fonts.load(spec)));
      await document.fonts.ready;
    } catch (error) {
      console.warn("display fonts:", error);
    }
  }

  let tableclothPattern = null;
  async function tableclothFor(ctx) {
    if (tableclothPattern !== null) return tableclothPattern || null;
    const img = await new Promise((resolve) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => resolve(null);
      image.src = "assets/bg/tablecloth.png";
    });
    if (!img) { tableclothPattern = false; return null; }
    const tile = document.createElement("canvas");
    tile.width = img.width * 2;
    tile.height = img.height * 2;
    const tctx = tile.getContext("2d");
    tctx.imageSmoothingEnabled = false;
    tctx.drawImage(img, 0, 0, tile.width, tile.height);
    tableclothPattern = ctx.createPattern(tile, "repeat");
    return tableclothPattern;
  }

  async function showCard() {
    const request = { id: ++state.shareRequest, session: state.session, decision: primaryPanel()?.decision, panel: primaryPanel(), maleDecision: state.fly === 'both' ? state.panels.male?.decision : null, lang: state.lang, siteUrl: state.siteUrl };
    const current = () => request.id === state.shareRequest && request.session === state.session && primaryPanel()?.decision === request.decision;
    if (!request.decision) return;
    const canvas = $("share-card");
    $("download-link").removeAttribute("href"); // no stale PNG while this request runs
    const sprites = request.panel.sprites;
    let snapshot = null;
    try {
      const [snap] = await Promise.all([
        request.panel.snapshotFor(request.decision),
        sprites ? Promise.all(request.decision.known.map((item) => loadDishSprite(sprites, spriteSlug(item)).catch(() => null))) : null,
      ]);
      snapshot = snap;
    } catch (error) {
      console.warn("snapshot failed:", error);
      snapshot = null; // the card is still valid without the brain snapshot
    }
    if (!current()) return;
    const tablecloth = await tableclothFor(canvas.getContext("2d")).catch(() => null);
    await displayFontsReady(request.lang);
    if (!current()) return;
    try {
      drawShareCard(canvas, request.decision, request.lang, {
        stub: Boolean(request.panel.lookup.table.stub),
        maleDecision: request.maleDecision,
        maleSprites: state.panels.male?.sprites,
        sprites,
        snapshot,
        tablecloth,
        siteUrl: request.siteUrl,
        spriteFor: (item) => (sprites && spriteSlug(item) ? sprites.dishCache.get(spriteSlug(item)) || null : null),
      });
    } catch (error) {
      console.warn("share card failed:", error);
      notice("stateShareFailed");
      return;
    }
    if (!current()) return;
    await prepareSave(canvas, request);
    if (!current()) return;
    const dialog = $("card-dialog");
    if (!dialog.open && request.id === state.shareRequest) dialog.showModal();
  }

  const isIOS = () => /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

  // The PNG as a File. Where the browser can share files (iOS Safari, Android
  // Chrome), "Save image" opens the share sheet, whose "Save Image" writes to
  // Photos. Otherwise the download link is used, and on iOS Safari (no file
  // sharing) the PNG is shown as an image with a long-press hint, because a
  // canvas cannot be long-pressed into Photos.
  let saveFile = null;
  async function prepareSave(canvas, request) {
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
    if (!blob || !(request.id === state.shareRequest)) return;
    saveFile = new File([blob], "ask-the-fly.png", { type: "image/png" });
    const canShareFiles = typeof navigator.canShare === "function" && navigator.canShare({ files: [saveFile] });
    const link = $("download-link");
    const button = $("save-btn");
    const image = $("share-image");
    const hint = $("save-hint");
    if (link.dataset.url) { URL.revokeObjectURL(link.dataset.url); delete link.dataset.url; }
    if (canShareFiles) {
      button.hidden = false;
      link.hidden = true;
      link.removeAttribute("href");
    } else {
      button.hidden = true;
      link.hidden = false;
      const url = URL.createObjectURL(blob);
      link.href = url;
      link.dataset.url = url;
    }
    const showImage = !canShareFiles && isIOS();
    if (showImage) {
      image.src = canvas.toDataURL("image/png");
      image.alt = STRINGS[state.lang].ariaShareCard;
    } else {
      image.removeAttribute("src");
    }
    image.hidden = !showImage;
    canvas.hidden = showImage;
    hint.hidden = !showImage;
  }

  async function shareSave() {
    if (!saveFile) return;
    try {
      await navigator.share({ files: [saveFile], title: STRINGS[state.lang].cardTitle });
    } catch (error) {
      if (error && error.name === "AbortError") return; // the user dismissed the sheet
      console.warn("share sheet failed:", error);
      notice("stateShareFailed");
    }
  }

  function cancelShare() {
    state.shareRequest += 1;
    const link = $("download-link");
    if (link.dataset.url) { URL.revokeObjectURL(link.dataset.url); delete link.dataset.url; }
    link.removeAttribute("href");
    saveFile = null;
  }

  function addSelection(option) {
    if (!option) return;
    if (!state.options.some((existing) => sameOption(existing, option))) state.options.push(option);
    renderOptions();
  }

  // Typed or pasted text: split on list separators; known names become keys.
  function addOption(raw) {
    for (const part of String(raw).split(/[\n,，、;；]+/)) addSelection(optionFromText(part, state.dictionary));
    renderOptions();
  }

  async function loadData() {
    const [dishes, table] = await Promise.all([
      fetch("data/dishes.json").then((r) => r.json()),
      fetch("data/lookup_table_v1_2.json").then((r) => { if (!r.ok) throw new Error('v1.2 table missing'); return r.json(); }),
    ]);
    state.dictionary = buildDictionary(dishes);
    state.panels.female.bindSources({lookup:buildLookup(table)});
    $("stub-banner").hidden = !table.stub;
    const [fallbacks, sections, config, release] = await Promise.all([
      fetch("assets/dishes/fallbacks.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("data/sections.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("config.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("data/release.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]);
    state.spriteFallbacks = (fallbacks && fallbacks.fallbacks) || {};
    state.sections = sections;
    state.release = release;
    if (config && typeof config.site_url === "string" && /^https?:\/\//.test(config.site_url)) state.siteUrl = config.site_url;
    applyStrings();
    // Scene data loads after the dictionary so the buttons enable early; the
    // scene is used only once both the neuron layout and the sprites are ready.
    try {
      const [neuronsJson, sprites, neuropils, manifest] = await Promise.all([
        fetch("data/neurons.json").then((r) => r.json()),
        loadSprites("assets/"),
        fetch("data/neuropils.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
        fetch("data/replay/manifest.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      ]);
      const panel=state.panels.female;
      panel.bindSources({neurons:decodeNeurons(neuronsJson),sprites,neuropils,manifest});
      if(manifest) {
        try {
          const named=await fetch('data/named_neurons.json').then(r=>r.ok?r.json():null);
          manifest.unmatched=named?named.neurons.filter(n=>!n.root_ids.length).map(n=>({key:n.key,label:n.label})):[];
        } catch (_) {manifest.unmatched=[];}
      }
      panel.mount();
      state.idleFly=new IdleFly($('idle-fly'),sprites);
      renderOptions();
    } catch (error) {
      console.warn("scene disabled:", error);
    }
  }

  // Reset discards the current run: a new session id makes every pending await
  // of the old run a no-op, and the run-time fields are cleared (F05). Skip is
  // different: it keeps the session and shows this run's result.
  function reset() {
    state.session+=1;
    for(const panel of Object.values(state.panels).filter(Boolean)) panel.reset();
    cancelShare();
    if($('card-dialog').open) $('card-dialog').close();
    setPhase('input');
  }

  $("lang-toggle").addEventListener("click", () => {
    state.lang = state.lang === "zh" ? "en" : "zh";
    try { localStorage.setItem("askfly.lang", state.lang); } catch (_) { /* ignore */ }
    applyStrings();
  });
  // IME: while a composition is open, Enter confirms the candidate and must not
  // submit the form (F15). Chrome reports keyCode 229 / isComposing on that key.
  const ime = { composing: false };
  $("option-input").addEventListener("compositionstart", () => { ime.composing = true; });
  $("option-input").addEventListener("compositionend", () => { ime.composing = false; });
  $("option-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (ime.composing) return;
    const input = $("option-input");
    if (suggestState.index >= 0 && suggestState.items[suggestState.index]) {
      pickSuggest(suggestState.index); // Enter selects the highlighted match
      return;
    }
    addOption(input.value); // no match: raw text is added and takes the miss path
    input.value = "";
    closeSuggest();
    input.focus();
  });
  $("option-input").addEventListener("input", renderSuggest);
  $("option-input").addEventListener("focus", renderSuggest);
  $("option-input").addEventListener("blur", () => setTimeout(closeSuggest, 120));
  $("option-input").addEventListener("keydown", (event) => {
    if (event.isComposing || event.keyCode === 229 || ime.composing) {
      if (event.key === "Enter") event.preventDefault();
      return;
    }
    if ($("suggest").hidden) return;
    if (event.key === "ArrowDown") { event.preventDefault(); highlightSuggest(suggestState.index + 1); }
    else if (event.key === "ArrowUp") { event.preventDefault(); highlightSuggest(suggestState.index - 1); }
    else if (event.key === "Escape") { closeSuggest(); }
  });
  $("option-input").addEventListener("paste", (event) => {
    const text = event.clipboardData && event.clipboardData.getData("text");
    if (text && /[\n,，、;；]/.test(text)) {
      event.preventDefault();
      addOption(text);
    }
  });
  $("view-all-btn").addEventListener("click", () => {
    library.open = !library.open;
    renderTasted();
    if (library.open) $("library-search").focus({ preventScroll: true });
  });
  $("library-search").addEventListener("input", (event) => { library.query = event.target.value; renderTasted(); });
  $("ask-btn").addEventListener("click", () => run("ask"));
  $("opposite-btn").addEventListener("click", () => run("opposite"));
  $("share-btn").addEventListener("click", () => {
    showCard().catch((error) => { console.warn("share card failed:", error); notice("stateShareFailed"); });
  });
  $("save-btn").addEventListener("click", () => { shareSave(); });
  $("close-card-btn").addEventListener("click", () => $("card-dialog").close());
  $("card-dialog").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });
  $("card-dialog").addEventListener("close", cancelShare); // covers Close, backdrop and Escape
  $("again-btn").addEventListener("click", () => {
    reset();
    $("option-input").focus();
  });
  window.addEventListener('resize',()=>{
    for(const panel of activePanels()) if(panel.brain && !panel.root.hidden) panel.brain.resize();
  });

  // Read-only view of the run state for browser regression checks (scripts/browser_checks.py).
  window.__askfly = {
    snapshot:()=>{
      const common={phase:state.phase,options:state.options.map(o=>o.key||o.text),idleRunning:Boolean(state.idleFly?.raf),dialogOpen:$('card-dialog').open};
      return {...state.panels.female.snapshot(common),fly:state.fly,
        panels:Object.fromEntries(Object.entries(state.panels).filter(([,p])=>p).map(([key,p])=>[key,p.snapshot(common)]))};
    },
  };

  applyStrings();
  loadData().then(async () => {
    // A shared link (?d=…&lang=…) fills the options and runs the sequence.
    const shared = parseShareParams(window.location.search);
    if (!shared || !state.dictionary) {await selectFly(state.fly,false);return;}
    state.fly=flySelection(shared.fly); // Old shared links always select the female.
    if (shared.lang && shared.lang !== state.lang) {
      state.lang = shared.lang; // for this view only; the saved preference is untouched
      applyStrings();
    }
    for (const option of resolveShared(shared.items, state.dictionary)) addSelection(option);
    if (state.options.length >= 2) await run(shared.mode, shared.seed ?? 0);
  }).catch((error) => {
    console.warn("data load failed:", error);
    notice("stateDataFailed");
  });
  window.addEventListener("offline", () => notice("stateOffline"));
  window.addEventListener("online", () => { if ($("notice").textContent === tr("stateOffline")) notice(null); });
}
