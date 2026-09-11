// SPDX-License-Identifier: MIT
// Ask the Fly — static front end. No LLM calls: dictionary lookup + lookup-table read.
// Pure functions are exported so they can be unit-tested with node (see test/).

import { BrainView, RasterView, SpikeClick, cellIdFor, decodeNeurons, makeReplayLoader, rasterRows, replayStats } from "./brain.js";
import { FlyScene, loadSprites, makeToken } from "./fly.js";

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
  for (const entry of entries) {
    const names = [entry.key, ...(entry.aliases || [])];
    for (const name of names) {
      const key = normalizeName(name);
      if (key && !index.has(key)) index.set(key, entry);
    }
  }
  return {
    entries,
    find(name) {
      return index.get(normalizeName(name)) || null;
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

export function scoreOptions(names, dictionary, lookup) {
  return names.map((name) => {
    const entry = dictionary.find(name);
    if (!entry) return { name, entry: null, cell: null };
    const cell = lookup.get({ sugar: entry.sugar, bitter: entry.bitter, water: entry.water, ir94e: "none" });
    // "Sugar response" = the same dish looked up with bitter = none. Equal to
    // `cell` when the dish has no bitter; shown anyway.
    const sugarOnly = lookup.get({ sugar: entry.sugar, bitter: "none", water: entry.water, ir94e: "none" });
    return { name, entry, cell, sugarOnly };
  });
}

// mode: "ask" picks the highest MN9; "opposite" picks the lowest, and also
// reports what the fly itself would have picked. Ties are reported as ties.
export function decide(scored, mode) {
  const known = scored.filter((item) => item.cell);
  if (known.length === 0) return { mode, winner: null, flyPick: null, tie: [], known, misses: scored.filter((i) => !i.cell) };
  const by = (sign) => [...known].sort((a, b) => sign * (b.cell.mn9_mean - a.cell.mn9_mean));
  const highest = by(1);
  const lowest = by(-1);
  const flyPick = highest[0];
  const chosen = mode === "opposite" ? lowest[0] : flyPick;
  const tie = known.filter((item) => Math.abs(item.cell.mn9_mean - chosen.cell.mn9_mean) < 1e-9);
  return {
    mode,
    winner: chosen,
    flyPick,
    tie: tie.length > 1 ? tie : [],
    known,
    misses: scored.filter((item) => !item.cell),
  };
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

export function issueUrl(name, lang) {
  const t = STRINGS[lang] || STRINGS.en;
  const title = fmt(t.issueTitle, { name });
  const body = fmt(t.issueBody, { name, lang });
  return `${REPO_URL}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
}

export function displayName(item, lang) {
  if (item.entry && item.entry.display && item.entry.display[lang]) return item.entry.display[lang];
  return item.name;
}

// The four fixed lines and the front-bottom line, filled for a decision.
// Ties are exact (same grid cell): the pick shows every tied name and the
// shared cell's numbers. With no known option every placeholder is "—".
export function cardLines(decision, lang) {
  const t = STRINGS[lang];
  const names = t.levelNames;
  const picked = decision.tie.length ? decision.tie : decision.winner ? [decision.winner] : [];
  const lead = picked[0];
  const values = lead
    ? {
        dish: picked.map((item) => displayName(item, lang)).join(" / "),
        hz: lead.cell.mn9_mean.toFixed(1),
        hz_sugar_only: lead.sugarOnly.mn9_mean.toFixed(1),
        sugar: names[lead.entry.sugar] ?? lead.entry.sugar,
        bitter: names[lead.entry.bitter] ?? lead.entry.bitter,
        water: names[lead.entry.water] ?? lead.entry.water,
      }
    : Object.fromEntries(["dish", "hz", "hz_sugar_only", "sugar", "bitter", "water"].map((k) => [k, t.cardEmptyValue]));
  return { fixed: t.fixedLines.map((line) => fmt(line, values)), bottom: t.cardBottom };
}

// ---------- share card (3:4, canvas) ----------

function wrapLines(ctx, text, maxWidth) {
  const words = /[㐀-鿿]/.test(text) ? Array.from(text) : text.split(" ");
  const joiner = /[㐀-鿿]/.test(text) ? "" : " ";
  const lines = [];
  let current = "";
  for (const word of words) {
    const candidate = current ? current + joiner + word : word;
    if (ctx.measureText(candidate).width > maxWidth && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
}

export function drawShareCard(canvas, decision, lang, options = {}) {
  const t = STRINGS[lang];
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  const pad = 64;
  ctx.fillStyle = options.stub ? "#fff3c4" : "#fbf8f2";
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = "#b5471f";
  ctx.fillRect(0, 0, W, 18);

  const font = (size, weight = 400) =>
    `${weight} ${size}px system-ui, -apple-system, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif`;

  ctx.fillStyle = "#1f1a17";
  ctx.font = font(56, 700);
  ctx.fillText(t.cardTitle, pad, 130);

  let y = 230;
  ctx.font = font(30);
  ctx.fillStyle = "#6b625b";
  let headline;
  if (!decision.winner) headline = t.verdictNone;
  else if (decision.tie.length) headline = t.cardTie;
  else if (decision.mode === "opposite") headline = fmt(t.cardOppositePicked, { fly: displayName(decision.flyPick, lang) });
  else headline = t.cardPicked;
  for (const line of wrapLines(ctx, headline, W - 2 * pad)) {
    ctx.fillText(line, pad, y);
    y += 40;
  }

  if (decision.winner) {
    ctx.fillStyle = "#1f1a17";
    ctx.font = font(72, 700);
    const names = decision.tie.length ? decision.tie.map((i) => displayName(i, lang)).join(" / ") : displayName(decision.winner, lang);
    for (const line of wrapLines(ctx, names, W - 2 * pad)) {
      y += 70;
      ctx.fillText(line, pad, y);
    }
    y += 30;
  }

  // Middle third: horizontal-bar comparison of every option's MN9 (monochrome;
  // the winner takes the card's accent). Bars share one scale so lengths compare.
  const bottomStart = H - 440;
  y += 36;
  const ranked = [...decision.known].sort((a, b) => b.cell.mn9_mean - a.cell.mn9_mean);
  const scale = Math.max(100, ...ranked.map((item) => item.cell.mn9_mean));
  const rowHeight = 58;
  const barHeight = 14;
  const trackWidth = W - 2 * pad;
  const maxRows = Math.max(1, Math.floor((bottomStart - y) / rowHeight));
  const shown = ranked.slice(0, maxRows);
  for (const item of shown) {
    const isWinner = decision.winner && (item === decision.winner || decision.tie.includes(item));
    ctx.font = font(26, isWinner ? 700 : 400);
    ctx.fillStyle = isWinner ? "#b5471f" : "#1f1a17";
    ctx.textAlign = "left";
    ctx.fillText(displayName(item, lang), pad, y);
    ctx.textAlign = "right";
    ctx.fillText(fmt(t.hzValue, { hz: item.cell.mn9_mean.toFixed(1) }), W - pad, y);
    ctx.textAlign = "left";
    const barY = y + 12;
    ctx.fillStyle = "#e2dbd0";
    ctx.fillRect(pad, barY, trackWidth, barHeight);
    const width = Math.max(0, Math.round((item.cell.mn9_mean / scale) * trackWidth));
    ctx.fillStyle = isWinner ? "#b5471f" : "#1f1a17";
    if (width > 0) ctx.fillRect(pad, barY, width, barHeight);
    y += rowHeight;
  }
  if (ranked.length > shown.length) {
    ctx.font = font(22);
    ctx.fillStyle = "#6b625b";
    ctx.fillText(fmt(t.cardMore, { n: ranked.length - shown.length }), pad, y);
    y += 34;
  }
  ctx.font = font(22);
  for (const item of decision.misses) {
    if (y > bottomStart - 10) break;
    ctx.fillStyle = "#6b625b";
    ctx.fillText(`${item.name} · ${t.missTitle}`, pad, y);
    y += 32;
  }

  // Four fixed lines, then the front-bottom line
  const lines = cardLines(decision, lang);
  let fy = H - 400;
  ctx.fillStyle = "#e2dbd0";
  ctx.fillRect(pad, fy - 40, W - 2 * pad, 2);
  ctx.font = font(24);
  ctx.fillStyle = "#1f1a17";
  for (const line of lines.fixed) {
    for (const part of wrapLines(ctx, line, W - 2 * pad)) {
      ctx.fillText(part, pad, fy);
      fy += 34;
    }
  }
  fy += 12;
  ctx.font = font(22, 600);
  ctx.fillStyle = "#b5471f";
  for (const part of wrapLines(ctx, lines.bottom, W - 2 * pad)) {
    ctx.fillText(part, pad, fy);
    fy += 30;
  }
  if (options.stub) {
    ctx.font = font(20, 700);
    ctx.fillStyle = "#4a3a00";
    ctx.fillText(t.stubStamp, pad, H - 30);
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
    options: [],
    dictionary: null,
    lookup: null,
    decision: null,
    brain: null,
    scene: null,
    raster: null,
    sound: new SpikeClick(),
    manifest: null,
    spriteFallbacks: {},
    sections: null,
    currentCell: null,
    currentItem: null,
    variant: "",
    loadReplay: makeReplayLoader("data/replay/"),
    token: null,
  };

  const $ = (id) => document.getElementById(id);
  const tr = (key, values) => fmt(STRINGS[state.lang][key], values || {});
  function notice(key, values) {
    const el = $("notice");
    if (!key) { el.hidden = true; el.textContent = ""; return; }
    el.textContent = tr(key, values);
    el.hidden = false;
  }

  function applyStrings() {
    const t = STRINGS[state.lang];
    document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
    document.title = t.pageTitle;
    for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t[el.dataset.i18n] ?? "";
    for (const el of document.querySelectorAll("[data-i18n-placeholder]")) el.placeholder = t[el.dataset.i18nPlaceholder] ?? "";
    for (const el of document.querySelectorAll("[data-i18n-aria]")) el.setAttribute("aria-label", t[el.dataset.i18nAria] ?? "");
    $("lang-toggle").textContent = state.lang === "zh" ? "EN" : "中文";
    if (state.lookup) {
      const table = state.lookup.table;
      $("table-meta").textContent = fmt(t.tableMeta, {
        version: table.stub ? "stub" : (table.git_commit || "").slice(0, 7),
        cells: table.cells.length,
        trials: table.n_trials_per_cell,
      });
    }
    renderOptions();
    renderTasted();
    if (state.brain) state.brain.setLang(state.lang);
    renderSilenceControls();
    if (state.decision) renderDecision();
  }

  // ---- details: raster, HUD, silencing ----
  function rasterLabels() {
    const t = STRINGS[state.lang];
    return { sugar: t.rasterSugar, bitter: t.rasterBitter, water: t.rasterWater, mn9_left: t.rasterMn9L, mn9_right: t.rasterMn9R };
  }

  function showReplayDetails(replay) {
    if (!state.raster) return;
    state.raster.setRows(rasterRows(replay, state.brain.neurons, rasterLabels()), replay.header.duration_ms);
    state.raster.draw(0);
    const st = replayStats(replay);
    const t = STRINGS[state.lang];
    $("hud-total").textContent = st.totalNeurons != null ? st.totalNeurons.toLocaleString() : "–";
    $("hud-active").textContent = st.activeNeurons.toLocaleString();
    $("hud-mn9").textContent = `${st.mn9Left} / ${st.mn9Right}`;
    $("hud-latency").textContent = st.mn9FirstMs == null ? t.hudNone : fmt(t.hudMs, { ms: st.mn9FirstMs });
    $("hud-inputs").textContent = fmt(t.hudRates, { sugar: st.hz.sugar, bitter: st.hz.bitter, water: st.hz.water });
  }

  // Silencing buttons: Clavicle plus the two neurons with the clearest, most
  // consistent MN9 effect (by |median change| and share of cells moving the same
  // way) are shown; the rest sit behind "More neurons". Order comes from the
  // manifest's recorded statistics, never from a guess.
  const silenceUi = { expanded: false };

  function silenceRanking() {
    const stats = state.manifest.variant_stats || {};
    const rows = (state.manifest.named_neurons || [])
      .filter((entry) => state.manifest.variants.includes(`silence_${entry.key}`))
      .map((entry) => {
        const st = stats[`silence_${entry.key}`] || {};
        const consistency = Math.max(st.frac_down || 0, st.frac_up || 0);
        return { ...entry, stats: st, score: Math.abs(st.median_delta || 0) * consistency };
      });
    const clavicle = rows.filter((r) => r.key === "clavicle");
    const others = rows.filter((r) => r.key !== "clavicle").sort((a, b) => b.score - a.score);
    return { primary: [...clavicle, ...others.slice(0, 2)], more: others.slice(2) };
  }

  function renderSilenceControls() {
    const box = $("silence-controls");
    if (!box || !state.manifest) return;
    const t = STRINGS[state.lang];
    box.innerHTML = "";
    const mk = (label, variant) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "btn btn-secondary btn-small";
      b.textContent = label;
      b.setAttribute("aria-pressed", state.variant === variant ? "true" : "false");
      b.addEventListener("click", () => playVariant(variant));
      return b;
    };
    const { primary, more } = silenceRanking();
    box.append(mk(t.silenceBaseline, ""));
    for (const entry of primary) box.append(mk(fmt(t.silenceButton, { name: entry.label }), entry.key));
    if (more.length) {
      const toggle = mk(silenceUi.expanded ? t.silenceLess : t.silenceMore, null);
      toggle.setAttribute("aria-pressed", "false");
      toggle.onclick = () => { silenceUi.expanded = !silenceUi.expanded; renderSilenceControls(); };
      box.append(toggle);
      if (silenceUi.expanded) for (const entry of more) box.append(mk(fmt(t.silenceButton, { name: entry.label }), entry.key));
    }
    const summary = document.createElement("div");
    summary.className = "silence-summary";
    for (const entry of [...primary, ...(silenceUi.expanded ? more : [])]) {
      const st = entry.stats;
      if (st.median_delta == null) continue;
      const line = document.createElement("div");
      line.textContent = fmt(t.silenceEffectSummary, {
        name: entry.label, median: (st.median_delta > 0 ? "+" : "") + st.median_delta,
        n: st.n_cells_mn9_active, down: Math.round((st.frac_down || 0) * 100),
      });
      summary.append(line);
    }
    box.append(summary);
    for (const entry of state.manifest.unmatched || []) {
      const span = document.createElement("span");
      span.className = "unavailable";
      span.textContent = fmt(t.silenceUnavailable, { name: entry.label });
      box.append(span);
    }
  }

  async function playVariant(variant) {
    if (!state.currentCell || !state.brain) return;
    state.variant = variant;
    renderSilenceControls();
    const t = STRINGS[state.lang];
    let replay;
    try {
      replay = await state.loadReplay(state.currentCell, variant);
    } catch (error) {
      console.warn("variant load failed:", error);
      $("silence-caption").textContent = t.stateReplayFailed;
      return;
    }
    const cellInfo = state.manifest.cells[state.currentCell];
    if (variant) {
      const before = cellInfo.mn9_left_count;
      const after = replay.header.mn9_left_count;
      const delta = after - before;
      const name = (state.manifest.named_neurons.find((n) => n.key === variant) || {}).label || variant;
      const st = (state.manifest.variant_stats || {})[`silence_${variant}`] || {};
      const medianText = st.median_delta == null ? "–" : (st.median_delta > 0 ? "+" : "") + st.median_delta;
      if (st.median_delta === 0) {
        // No consistent effect across cells (per-cell differences are stream noise):
        // that is the result, say it plainly alongside this cell's numbers.
        $("silence-caption").textContent = fmt(t.silenceCaptionNoEffect, { name, after, before, delta: (delta >= 0 ? "+" : "") + delta, median: medianText });
      } else {
        $("silence-caption").textContent = fmt(t.silenceCaption, { name, after, before, delta: (delta >= 0 ? "+" : "") + delta });
      }
    } else {
      $("silence-caption").textContent = "";
    }
    $("brain-caption").textContent = fmt(t.brainCaption, { cell: variant ? `${state.currentCell} (${replay.header.variant})` : state.currentCell, n: replay.header.n_spikes });
    $("mn9-count").textContent = "0";
    state.brain.onMn9 = (count) => { $("mn9-count").textContent = String(count); state.sound.click(); };
    state.brain.onTime = (ms) => { if (state.raster && !$("brain-details").hidden) state.raster.draw(ms); };
    state.brain.setReplay(replay);
    showReplayDetails(replay);
    await state.brain.play(speed());
  }

  // "The fly has tasted these": every dictionary entry as a tappable chip.
  let tastedInitialised = false;
  function renderTasted() {
    if (!state.dictionary) return;
    const box = $("tasted-chips");
    box.innerHTML = "";
    const byKey = new Map(state.dictionary.entries.map((e) => [e.key, e]));
    const label = (entry) => entry.display?.[state.lang] || entry.key;
    const sortEntries = (list) => [...list].sort((a, b) => label(a).localeCompare(label(b), state.lang === "zh" ? "zh-Hans-CN" : "en"));
    const addChip = (parent, entry) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.textContent = label(entry);
      chip.addEventListener("click", () => { addOption(chip.textContent); closeSuggest(); });
      parent.append(chip);
    };
    const placed = new Set();
    if (state.sections) {
      for (const section of state.sections.sections) {
        const entries = section.keys.map((k) => byKey.get(k)).filter(Boolean);
        if (!entries.length) continue;
        const group = document.createElement("div");
        group.className = "chip-group";
        const head = document.createElement("div");
        head.className = "chip-head";
        head.textContent = state.lang === "zh" ? section.zh : section.en;
        group.append(head);
        const row = document.createElement("div");
        row.className = "chips";
        for (const entry of sortEntries(entries)) { addChip(row, entry); placed.add(entry.key); }
        group.append(row);
        box.append(group);
      }
    }
    const rest = sortEntries(state.dictionary.entries.filter((e) => !placed.has(e.key)));
    if (rest.length) {
      const row = document.createElement("div");
      row.className = "chips";
      for (const entry of rest) addChip(row, entry);
      box.append(row);
    }
    if (!tastedInitialised) {
      $("tasted").open = window.innerWidth >= 560; // collapsed by default on mobile
      tastedInitialised = true;
    }
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
          b.addEventListener("mousedown", (event) => { event.preventDefault(); addOption(item.label); input.value = ""; closeSuggest(); });
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
    addOption(item.label);
    $("option-input").value = "";
    closeSuggest();
    $("option-input").focus();
  }

  function renderOptions() {
    const list = $("option-list");
    list.innerHTML = "";
    state.options.forEach((name, index) => {
      const li = document.createElement("li");
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
    const ready = Boolean(state.lookup && state.dictionary);
    $("ask-btn").disabled = !ready;
    $("opposite-btn").disabled = !ready;
    if (state.options.length >= 2) notice(null);
  }

  function levelText(level) {
    return STRINGS[state.lang].levelNames[level] ?? level;
  }

  function renderDecision() {
    const t = STRINGS[state.lang];
    const d = state.decision;
    const verdict = $("verdict");
    verdict.innerHTML = "";
    const lead = document.createElement("span");
    const strong = document.createElement("strong");
    if (!d.winner) {
      lead.textContent = t.verdictNone;
    } else if (d.tie.length) {
      lead.textContent = t.verdictTie;
      strong.textContent = d.tie.map((i) => displayName(i, state.lang)).join(" / ");
    } else if (d.mode === "opposite") {
      lead.textContent = fmt(t.verdictOpposite, { fly: displayName(d.flyPick, state.lang) });
      strong.textContent = displayName(d.winner, state.lang);
    } else {
      lead.textContent = t.verdictAsk;
      strong.textContent = displayName(d.winner, state.lang);
    }
    verdict.append(lead, strong);

    const body = $("results-body");
    body.innerHTML = "";
    const ordered = [...d.known].sort((a, b) => b.cell.mn9_mean - a.cell.mn9_mean).concat(d.misses);
    for (const item of ordered) {
      const tr = document.createElement("tr");
      if (item.cell && d.winner && (item === d.winner || d.tie.includes(item))) tr.className = "win";
      else if (item.cell && d.mode === "opposite" && item === d.flyPick) tr.className = "lose";
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
        for (const dimension of ["sugar", "bitter", "water"]) {
          const td = document.createElement("td");
          td.textContent = levelText(item.entry[dimension]);
          tr.append(td);
        }
        const mn9 = document.createElement("td");
        mn9.className = "mn9";
        mn9.textContent = fmt(t.mn9MeanStd, { mean: item.cell.mn9_mean.toFixed(1), std: item.cell.mn9_std.toFixed(1) }); // `tr` is the table row here
        tr.append(mn9);
      } else {
        const td = document.createElement("td");
        td.colSpan = 4;
        td.textContent = t.missTitle;
        tr.append(td);
      }
      body.append(tr);
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

    $("result-panel").hidden = false;
    $("input-panel").hidden = true;
  }

  function slugFor(key) {
    return String(key).normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "dish";
  }

  function speed() {
    return Number($("speed").value) || 1;
  }

  // Plays the fly + brain sequence for a decision, then reveals the result view.
  async function runScene(decision) {
    if (state.token) state.token.cancel();
    const token = makeToken();
    state.token = token;
    const scored = [...decision.known, ...decision.misses];
    const plates = scored.map((item) => ({
      key: item.entry ? item.entry.key : item.name,
      label: displayName(item, state.lang),
      sub: item.cell ? tr("hzValue", { hz: item.cell.mn9_mean.toFixed(1) }) : STRINGS[state.lang].plateUnknown,
      slug: item.entry ? (state.spriteFallbacks[slugFor(item.entry.key)] || slugFor(item.entry.key)) : null,
    }));
    const indexOf = (item) => scored.indexOf(item);
    const plan = {
      order: decision.known.map(indexOf),
      winner: decision.winner ? indexOf(decision.mode === "opposite" ? decision.flyPick : decision.winner) : null,
      loser: decision.mode === "opposite" && decision.winner ? indexOf(decision.winner) : null,
      tie: decision.tie.map(indexOf),
      mode: decision.mode,
    };
    $("scene-panel").hidden = false;
    $("input-panel").hidden = true;
    $("result-panel").hidden = true;
    $("card-panel").hidden = true;
    $("scene-status").textContent = tr("sceneIdle");
    $("brain-caption").textContent = tr("brainIdle");
    $("mn9-count").textContent = "0";
    state.brain.resize();
    await state.scene.setPlates(plates);
    window.scrollTo({ top: 0, behavior: "smooth" });

    const hooks = {
      onTaste: async (index) => {
        const item = scored[index];
        if (!item.cell || token.cancelled) return;
        $("scene-status").textContent = tr("sceneTasting", { dish: displayName(item, state.lang) });
        state.brain.setReplay(null); // blank brain while the replay is fetched
        $("mn9-count").textContent = "0";
        const cellId = cellIdFor(item.cell);
        let replay;
        try {
          replay = await state.loadReplay(cellId);
        } catch (error) {
          console.warn("replay load failed:", error);
          $("brain-caption").textContent = navigator.onLine === false ? tr("stateOffline") : tr("stateReplayFailed");
          notice(navigator.onLine === false ? "stateOffline" : "stateReplayFailed");
          return;
        }
        if (token.cancelled) return;
        $("brain-caption").textContent = tr("brainCaption", { cell: cellId, n: replay.header.n_spikes });
        $("mn9-count").textContent = "0";
        state.currentCell = cellId;
        state.currentItem = item;
        state.variant = "";
        $("silence-caption").textContent = "";
        renderSilenceControls();
        state.brain.onMn9 = (count) => { $("mn9-count").textContent = String(count); state.sound.click(); };
        state.brain.onTime = (ms) => { if (state.raster) state.raster.draw(ms); };
        state.brain.setReplay(replay);
        showReplayDetails(replay);
        const stopOnCancel = () => state.brain.stop();
        token.onCancel.push(stopOnCancel);
        await state.brain.play(speed());
      },
    };
    await state.scene.run(plan, hooks, token);
    if (state.token !== token) return;
    if (!decision.winner) $("scene-status").textContent = tr("sceneNone");
    else if (decision.tie.length) $("scene-status").textContent = tr("sceneTie");
    else if (decision.mode === "opposite") $("scene-status").textContent = tr("sceneOpposite", { fly: displayName(decision.flyPick, state.lang), dish: displayName(decision.winner, state.lang) });
    else $("scene-status").textContent = tr("sceneWinner", { dish: displayName(decision.winner, state.lang) });
    renderDecision();
  }

  function run(mode) {
    if (!state.lookup || !state.dictionary) { notice("stateDataFailed"); return; }
    if (state.options.length < 2) { notice("stateNoOptions"); return; }
    notice(null);
    const scored = scoreOptions(state.options, state.dictionary, state.lookup);
    state.decision = decide(scored, mode);
    if (state.decision.known.length === 0) {
      notice("stateAllUnknown");
      $("card-panel").hidden = true;
      renderDecision();
      return;
    }
    if (state.brain && state.scene) {
      runScene(state.decision).catch((error) => {
        console.warn("scene error:", error);
        $("scene-status").textContent = tr("stateSceneError");
        renderDecision();
      });
      return;
    }
    $("card-panel").hidden = true;
    renderDecision();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function showCard() {
    const canvas = $("share-card");
    drawShareCard(canvas, state.decision, state.lang, { stub: Boolean(state.lookup.table.stub) });
    try {
      $("download-link").href = canvas.toDataURL("image/png");
    } catch (_) {
      $("download-link").removeAttribute("href");
    }
    $("card-panel").hidden = false;
    $("card-panel").scrollIntoView({ behavior: "smooth" });
  }

  function addOption(raw) {
    for (const part of String(raw).split(/[\n,，、;；]+/)) {
      const name = part.trim();
      if (!name) continue;
      if (state.options.some((existing) => normalizeName(existing) === normalizeName(name))) continue;
      state.options.push(name);
    }
    renderOptions();
  }

  async function loadData() {
    const [dishes, table] = await Promise.all([
      fetch("data/dishes.json").then((r) => r.json()),
      fetch("data/lookup_table.json").then((r) => r.json()),
    ]);
    state.dictionary = buildDictionary(dishes);
    state.lookup = buildLookup(table);
    $("stub-banner").hidden = !table.stub;
    const [fallbacks, sections] = await Promise.all([
      fetch("assets/dishes/fallbacks.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("data/sections.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]);
    state.spriteFallbacks = (fallbacks && fallbacks.fallbacks) || {};
    state.sections = sections;
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
      const neurons = decodeNeurons(neuronsJson);
      state.brain = new BrainView($("brain-canvas"), neurons, { neuropils, lang: state.lang });
      state.raster = new RasterView($("raster-canvas"));
      state.manifest = manifest;
      if (manifest) {
        // Named neurons without a v783 match are listed so the site can say they were skipped.
        try {
          const named = await fetch("data/named_neurons.json").then((r) => (r.ok ? r.json() : null));
          manifest.unmatched = named ? named.neurons.filter((n) => !n.root_ids.length).map((n) => ({ key: n.key, label: n.label })) : [];
        } catch (_) { manifest.unmatched = []; }
      }
      renderSilenceControls();
      state.scene = new FlyScene($("scene-canvas"), sprites);
      $("layout-note").hidden = neurons.layout !== "placeholder";
    } catch (error) {
      console.warn("scene disabled:", error);
    }
  }

  function reset() {
    if (state.token) state.token.cancel();
    if (state.brain) state.brain.stop();
    if (state.scene) state.scene.stop();
    state.decision = null;
    $("scene-panel").hidden = true;
    $("result-panel").hidden = true;
    $("card-panel").hidden = true;
    $("input-panel").hidden = false;
  }

  $("lang-toggle").addEventListener("click", () => {
    state.lang = state.lang === "zh" ? "en" : "zh";
    try { localStorage.setItem("askfly.lang", state.lang); } catch (_) { /* ignore */ }
    applyStrings();
  });
  $("option-form").addEventListener("submit", (event) => {
    event.preventDefault();
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
  $("ask-btn").addEventListener("click", () => run("ask"));
  $("opposite-btn").addEventListener("click", () => run("opposite"));
  $("share-btn").addEventListener("click", showCard);
  $("close-card-btn").addEventListener("click", () => { $("card-panel").hidden = true; });
  $("again-btn").addEventListener("click", () => {
    reset();
    $("option-input").focus();
  });
  $("skip-btn").addEventListener("click", () => {
    if (state.token) state.token.cancel();
    if (state.brain) state.brain.stop();
    if (state.decision) renderDecision();
  });
  $("speed").addEventListener("change", () => {
    if (state.brain) state.brain.speed = speed();
  });
  $("sound-toggle").addEventListener("change", (event) => state.sound.enable(event.target.checked));
  $("brain-details").addEventListener("toggle", () => {
    if ($("brain-details").open && state.raster && state.raster.rows.length) state.raster.setRows(state.raster.rows, state.raster.duration);
  });
  window.addEventListener("resize", () => {
    if (state.brain && !$("scene-panel").hidden) state.brain.resize();
  });

  applyStrings();
  loadData().catch((error) => {
    console.warn("data load failed:", error);
    notice("stateDataFailed");
  });
  window.addEventListener("offline", () => notice("stateOffline"));
  window.addEventListener("online", () => { if ($("notice").textContent === tr("stateOffline")) notice(null); });
}
