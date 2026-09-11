// SPDX-License-Identifier: MIT
// Ask the Fly — static front end. No LLM calls: dictionary lookup + lookup-table read.
// Pure functions are exported so they can be unit-tested with node (see test/).

import { BrainView, RasterView, SpikeClick, cellIdFor, decodeNeurons, makeReplayLoader, rasterRows, renderSnapshot, replayStats } from "./brain.js";
import { FlyScene, IdleFly, loadDishSprite, loadSprites, makeToken } from "./fly.js";
import { qrcode } from "./vendor/qrcode-generator/qrcode.mjs";

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
  return { fixed: t.fixedLines.map((line) => fmt(line, values)), bottom: t.cardHonesty };
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

// ?d=slug,slug,…&lang=zh[&m=opposite] replays a comparison on load. Known dishes
// travel as their sprite slug (short, scannable); unknown names as typed, encoded.
export function shareParams(decision, lang) {
  const parts = [...decision.known, ...decision.misses].map((item) =>
    (item.entry ? slugFor(item.entry.key) : encodeURIComponent(item.name)));
  let query = `?d=${parts.join(",")}&lang=${lang === "zh" ? "zh" : "en"}`;
  if (decision.mode === "opposite") query += "&m=opposite";
  return query;
}

export function shareUrl(decision, lang, base = SITE_URL) {
  return (base.endsWith("/") ? base : base + "/") + shareParams(decision, lang);
}

export function parseShareParams(search) {
  const params = new URLSearchParams(search || "");
  const d = params.get("d");
  if (!d) return null;
  const names = d.split(",").map((s) => s.trim()).filter(Boolean);
  if (!names.length) return null;
  const lang = params.get("lang");
  return {
    names,
    lang: lang === "zh" || lang === "en" ? lang : null,
    mode: params.get("m") === "opposite" ? "opposite" : "ask",
  };
}

// "sugar low · bitter none · water high" for a lookup cell or dictionary entry,
// in the page's language; the raw cell id stays in the details HUD.
export function levelsText(levels, lang) {
  const t = STRINGS[lang] || STRINGS.en;
  const name = (level) => t.levelNames[level] ?? level;
  return fmt(t.levelsLine, { sugar: name(levels.sugar), bitter: name(levels.bitter), water: name(levels.water) });
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

// Turns shared names back into selections: a slug or name that resolves to a
// dictionary entry becomes { key }; anything else stays as typed.
export function resolveShared(names, dictionary) {
  return names.map((name) => {
    const entry = dictionary.find(name) || dictionary.findSlug(name) || dictionary.find(name.replace(/-/g, " "));
    return entry ? { key: entry.key } : { text: name };
  });
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
  const chosen = decision.winner ? (decision.tie.length ? decision.tie : [decision.winner]) : [];
  const ranked = [...decision.known].sort((a, b) => b.cell.mn9_mean - a.cell.mn9_mean);
  const others = ranked.filter((item) => !chosen.includes(item));
  const big = chosen.length > 1 ? Math.min(120, Math.floor((width - 16 * (chosen.length + 1)) / chosen.length)) : 150;
  const small = 64;
  const gap = 16;
  const top = chosen.length > 1 ? Math.round(big * 0.2) : 0; // room for the hovering fly in a tie
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
    if (chosen.length > 1) drawFlyOn(ctx, flyFrames, width / 2 - big / 2, y - big * 0.16, big, false);
    chosen.forEach((item, i) => {
      const x = x0 + i * (big + gap);
      drawDish(ctx, spriteFor(item), x, y, big, false);
      if (chosen.length === 1 && decision.mode !== "opposite") drawFlyOn(ctx, flyFrames, x, y, big, true);
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
      const flyPick = decision.mode === "opposite" && item === decision.flyPick;
      drawDish(ctx, spriteFor(item), x, y, small, !flyPick);
      if (flyPick) drawFlyOn(ctx, flyFrames, x, y, small, true);
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
  const mono = (size) => `${size}px ui-monospace, Menlo, Consolas, "Courier New", monospace`;

  // Header: title, headline, the chosen name(s).
  ctx.fillStyle = "#1f1a17";
  ctx.font = font(50, 700);
  ctx.textAlign = "left";
  ctx.fillText(t.cardTitle, pad, 108);
  let y = 172;
  ctx.font = font(27);
  ctx.fillStyle = "#6b625b";
  let headline;
  if (!decision.winner) headline = t.verdictNone;
  else if (decision.tie.length) headline = t.cardTie;
  else if (decision.mode === "opposite") headline = fmt(t.cardOppositePicked, { fly: displayName(decision.flyPick, lang) });
  else headline = t.cardPicked;
  for (const line of wrapLines(ctx, headline, W - 2 * pad)) {
    ctx.fillText(line, pad, y);
    y += 36;
  }
  const chosen = decision.winner ? (decision.tie.length ? decision.tie : [decision.winner]) : [];
  if (chosen.length) {
    ctx.fillStyle = "#1f1a17";
    ctx.font = font(chosen.length > 1 ? 44 : 56, 700);
    const names = chosen.map((i) => displayName(i, lang)).join(" / ");
    for (const line of wrapLines(ctx, names, W - 2 * pad)) {
      y += chosen.length > 1 ? 50 : 62;
      ctx.fillText(line, pad, y);
    }
  }
  y += 24;

  // Bottom block is fixed: brain snapshot left, QR code right. Everything above
  // shares the rest: sprite, bars, MN9 line, honesty sentence.
  const qrSize = 220;
  const qrX = W - pad - qrSize;
  const bottomEstimate = H - 300; // the bottom block starts here at the latest

  // The chosen dish with the fly on it (ties: every tied dish, fly hovering above).
  const ranked = [...decision.known].sort((a, b) => b.cell.mn9_mean - a.cell.mn9_mean);
  const barRows = Math.min(ranked.length, 4);
  const barsHeight = ranked.length ? 16 + barRows * 44 + (ranked.length > barRows ? 28 : 0) : 0;
  const textBlock = 40 + 60; // MN9 line + honesty sentence (up to two lines)
  const spriteRoom = Math.max(0, bottomEstimate - 30 - textBlock - barsHeight - y);
  if (chosen.length && spriteRoom >= 120) {
    const bigSize = Math.max(120, Math.min(chosen.length > 1 ? 180 : 250, spriteRoom - (chosen.length > 1 ? 30 : 0)));
    const gap = 24;
    const rowWidth = chosen.length * bigSize + (chosen.length - 1) * gap;
    const x0 = (W - rowWidth) / 2;
    const sy = y + (chosen.length > 1 ? 30 : 0);
    const opposite = decision.mode === "opposite" && decision.flyPick && !chosen.includes(decision.flyPick);
    const shift = opposite ? -Math.round(bigSize * 0.36) : 0; // room for the fly's pick on the right
    if (chosen.length > 1) drawFlyOn(ctx, flyFrames, W / 2 - bigSize / 2, sy - bigSize * 0.16, bigSize, false);
    chosen.forEach((item, i) => {
      const x = x0 + shift + i * (bigSize + gap);
      drawDish(ctx, spriteFor(item), x, sy, bigSize, false);
      if (chosen.length === 1 && !opposite) drawFlyOn(ctx, flyFrames, x, sy, bigSize, true);
    });
    if (opposite) {
      // The human's dish stays large; the fly sits on its own pick beside it.
      const small = Math.round(bigSize * 0.56);
      const x = x0 + shift + rowWidth + 28;
      const yy = sy + bigSize - small;
      drawDish(ctx, spriteFor(decision.flyPick), x, yy, small, false);
      drawFlyOn(ctx, flyFrames, x, yy, small, true);
      ctx.font = font(20, 600);
      ctx.fillStyle = "#1f1a17";
      ctx.textAlign = "center";
      ctx.fillText(displayName(decision.flyPick, lang), x + small / 2, yy + small + 24);
      ctx.textAlign = "left";
    }
    y = sy + bigSize + (opposite ? 44 : 16);
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
    y += 44;
  }
  if (ranked.length > shown.length) {
    ctx.font = font(20);
    ctx.fillStyle = "#6b625b";
    ctx.fillText(fmt(t.cardMore, { n: ranked.length - shown.length }), pad, y);
    y += 28;
  }

  // The MN9 line and the one honesty sentence.
  const lines = cardLines(decision, lang);
  y += 6;
  ctx.font = font(21);
  ctx.fillStyle = "#1f1a17";
  for (const part of wrapLines(ctx, lines.fixed[1], W - 2 * pad)) {
    ctx.fillText(part, pad, y);
    y += 28;
  }
  y += 6;
  ctx.font = font(19, 600);
  ctx.fillStyle = "#b5471f";
  for (const part of wrapLines(ctx, lines.bottom, W - 2 * pad).slice(0, 3)) {
    ctx.fillText(part, pad, y);
    y += 26;
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
    lookup: null,
    decision: null,
    brain: null,
    scene: null,
    raster: null,
    sound: new SpikeClick(),
    manifest: null,
    spriteFallbacks: {},
    sections: null,
    siteUrl: SITE_URL,
    currentCell: null,
    currentItem: null,
    currentCellLevels: null,
    variant: "", // requested variant (button state)
    appliedVariant: "", // variant whose replay is on screen
    variantRequest: 0, // id of the latest silencing request; older responses are dropped (F03)
    session: 0, // run session; reset() and run() start a new one, older async work is dropped (F05)
    loadReplay: makeReplayLoader("data/replay/"),
    token: null,
    sceneStatus: null, // { key, item?, fly?, dish? } re-rendered on language switch
    brainCaption: null, // { cell, variant, n } re-rendered on language switch
    scenePlates: null, // scored items behind the plates, for relabelling
    idleFly: null,
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
        version: table.stub ? "stub" : currentCommit(table.git_commit).slice(0, 7),
        cells: table.cells.length,
        trials: table.n_trials_per_cell,
      });
    }
    renderOptions();
    renderTasted();
    if (state.brain) state.brain.setLang(state.lang);
    renderSilenceControls();
    renderSceneStatus();
    renderBrainCaption();
    relabelPlates();
    if (state.decision) renderDecision();
    if (state.decision && $("card-dialog").open) showCard().catch(() => {});
  }

  function renderBrainCaption() {
    const c = state.brainCaption;
    if (!c) return;
    const cell = levelsText(c.cell, state.lang) + (c.variant ? ` (${c.variant})` : "");
    $("brain-caption").textContent = tr("brainCaption", { cell, n: c.n });
  }

  function renderSceneStatus() {
    const st = state.sceneStatus;
    if (!st) return;
    const values = {};
    for (const k of ["dish", "fly"]) if (st[k]) values[k] = displayName(st[k], state.lang);
    $("scene-status").textContent = tr(st.key, values);
  }

  // Plate captions follow the language; a plate says "loading…" only while its
  // replay is being fetched, and shows its Hz once the fly has tasted it.
  function plateSub(item) {
    if (!item.cell) return STRINGS[state.lang].plateUnknown;
    if (item.loading) return STRINGS[state.lang].plateLoading;
    if (item.tasted) return tr("hzValue", { hz: item.cell.mn9_mean.toFixed(1) });
    return "";
  }

  function relabelPlates() {
    if (!state.scene || !state.scenePlates) return;
    state.scenePlates.forEach((item, i) => state.scene.relabel(i, displayName(item, state.lang), plateSub(item)));
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
    $("hud-cell").textContent = replay.header.cell_id || state.currentCell || "–";
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
    // The button factory only builds the element; each button gets exactly one
    // handler, passed in explicitly (F02).
    const button = (label, onClick) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "btn btn-secondary btn-small";
      b.textContent = label;
      b.addEventListener("click", onClick);
      return b;
    };
    const variantButton = (label, variant) => {
      const b = button(label, () => playVariant(variant));
      b.setAttribute("aria-pressed", state.variant === variant ? "true" : "false");
      return b;
    };
    const { primary, more } = silenceRanking();
    box.append(variantButton(t.silenceBaseline, ""));
    for (const entry of primary) box.append(variantButton(fmt(t.silenceButton, { name: entry.label }), entry.key));
    if (more.length) {
      // Expander: changes only the list, never the experiment condition.
      const toggle = button(silenceUi.expanded ? t.silenceLess : t.silenceMore, () => {
        silenceUi.expanded = !silenceUi.expanded;
        renderSilenceControls();
      });
      toggle.setAttribute("aria-expanded", silenceUi.expanded ? "true" : "false");
      toggle.setAttribute("aria-controls", "silence-controls");
      box.append(toggle);
      if (silenceUi.expanded) for (const entry of more) box.append(variantButton(fmt(t.silenceButton, { name: entry.label }), entry.key));
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
    // Identity of this request: only the latest request of the current session
    // for the cell that is still current may touch the UI (F03).
    const request = { id: ++state.variantRequest, session: state.session, cell: state.currentCell, levels: state.currentCellLevels };
    const current = () => request.id === state.variantRequest && request.session === state.session && state.currentCell === request.cell;
    state.variant = variant;
    renderSilenceControls();
    const t = STRINGS[state.lang];
    let replay;
    try {
      replay = await state.loadReplay(request.cell, variant);
    } catch (error) {
      console.warn("variant load failed:", error);
      if (!current()) return;
      state.variant = state.appliedVariant; // the buttons go back to what is actually shown
      renderSilenceControls();
      $("silence-caption").textContent = t.stateReplayFailed;
      return;
    }
    if (!current()) return;
    state.appliedVariant = variant;
    const cellInfo = state.manifest.cells[request.cell];
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
    state.brainCaption = { cell: request.levels, variant: variant ? replay.header.variant : "", n: replay.header.n_spikes };
    renderBrainCaption();
    $("mn9-count").textContent = "0";
    state.brain.onMn9 = (count) => { $("mn9-count").textContent = String(count); state.sound.click(); };
    state.brain.onTime = (ms) => { if (state.raster && !$("brain-details").hidden) state.raster.draw(ms); };
    state.brain.setReplay(replay);
    showReplayDetails(replay);
    await state.brain.play(speed());
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
    const ready = Boolean(state.lookup && state.dictionary);
    $("ask-btn").disabled = !ready;
    $("opposite-btn").disabled = !ready;
    if (state.options.length >= 2) notice(null);
    // Empty table: the one-line hint shows until a dish arrives; the fly rests
    // on the table's edge throughout.
    $("table-empty").hidden = state.options.length > 0;
    if (state.idleFly) state.idleFly.start();
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
    renderHero().catch((error) => console.warn("hero failed:", error));

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

    const cardLinesBox = $("card-lines");
    cardLinesBox.innerHTML = "";
    if (d.winner) {
      for (const line of cardLines(d, state.lang).fixed) {
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

    $("result-panel").hidden = false;
    $("input-panel").hidden = true;
  }

  // The winner sprite with the fly is the result's main image, drawn as soon
  // as the sprites are in the cache (the scene loaded them; the card reuses them).
  async function renderHero() {
    const canvas = $("result-hero");
    const decision = state.decision;
    const sprites = state.scene ? state.scene.sprites : null;
    if (!decision || !decision.winner || !sprites) { canvas.hidden = true; return; }
    await Promise.all(decision.known.map((item) => loadDishSprite(sprites, spriteSlug(item)).catch(() => null)));
    if (state.decision !== decision) return;
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

  function speed() {
    return Number($("speed").value) || 1;
  }

  // Plays the fly + brain sequence for a decision, then reveals the result view.
  async function runScene(decision, session) {
    if (state.token) state.token.cancel();
    const token = makeToken();
    state.token = token;
    // Live while this session is current and the sequence has not been skipped.
    const live = () => state.session === session && !token.cancelled;
    const scored = [...decision.known, ...decision.misses];
    for (const item of scored) { item.loading = false; item.tasted = false; }
    state.scenePlates = scored;
    const plates = scored.map((item) => ({
      key: item.entry ? item.entry.key : item.name,
      label: displayName(item, state.lang),
      sub: plateSub(item),
      slug: spriteSlug(item),
    }));
    // Replays are fetched up front so the fly rarely waits at a plate.
    for (const item of decision.known) state.loadReplay(cellIdFor(item.cell)).catch(() => {});
    const indexOf = (item) => scored.indexOf(item);
    const plan = {
      order: decision.known.map(indexOf),
      winner: decision.winner ? indexOf(decision.flyPick) : null, // the fly lands on its own pick in every mode
      tie: decision.tie.map(indexOf),
    };
    $("scene-panel").hidden = false;
    $("input-panel").hidden = true;
    $("result-panel").hidden = true;
    state.sceneStatus = { key: "sceneIdle" };
    renderSceneStatus();
    state.brainCaption = null;
    $("brain-caption").textContent = "";
    $("mn9-count").textContent = "0";
    $("mn9-pill").hidden = true;
    $("hud-idle").hidden = false;
    state.brain.resize();
    await state.scene.setPlates(plates);
    if (!live()) return;
    window.scrollTo({ top: 0, behavior: "smooth" });

    const hooks = {
      onTaste: async (index) => {
        const item = scored[index];
        if (!item.cell || !live()) return;
        state.sceneStatus = { key: "sceneTasting", dish: item };
        renderSceneStatus();
        state.brain.setReplay(null); // blank brain while the replay is fetched
        $("mn9-count").textContent = "0";
        const cellId = cellIdFor(item.cell);
        item.loading = true;
        state.scene.relabel(index, null, plateSub(item));
        let replay;
        try {
          replay = await state.loadReplay(cellId);
        } catch (error) {
          console.warn("replay load failed:", error);
          if (state.session !== session) return; // reset while loading: nothing to show
          item.loading = false;
          state.scene.relabel(index, null, plateSub(item));
          $("brain-caption").textContent = navigator.onLine === false ? tr("stateOffline") : tr("stateReplayFailed");
          notice(navigator.onLine === false ? "stateOffline" : "stateReplayFailed");
          return;
        }
        if (state.session !== session) return; // reset while loading (F05)
        item.loading = false;
        item.tasted = true;
        state.scene.relabel(index, null, plateSub(item));
        if (token.cancelled) return; // skipped: the result view shows the numbers
        state.currentCellLevels = item.cell;
        state.brainCaption = { cell: item.cell, variant: "", n: replay.header.n_spikes };
        renderBrainCaption();
        $("mn9-count").textContent = "0";
        $("mn9-pill").hidden = false;
        $("hud-idle").hidden = true;
        state.currentCell = cellId;
        state.currentItem = item;
        state.variant = "";
        state.appliedVariant = "";
        state.variantRequest += 1; // pending silencing requests for the previous dish are stale
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
    if (state.session !== session || state.token !== token) return;
    for (const item of decision.known) item.tasted = true; // skipped plates still show their Hz
    relabelPlates();
    if (!decision.winner) state.sceneStatus = { key: "sceneNone" };
    else if (decision.tie.length) state.sceneStatus = { key: "sceneTie" };
    else if (decision.mode === "opposite") state.sceneStatus = { key: "sceneOpposite", fly: decision.flyPick, dish: decision.winner };
    else state.sceneStatus = { key: "sceneWinner", dish: decision.winner };
    renderSceneStatus();
    renderDecision();
  }

  function run(mode) {
    if (!state.lookup || !state.dictionary) { notice("stateDataFailed"); return; }
    if (state.options.length < 2) { notice("stateNoOptions"); return; }
    notice(null);
    state.session += 1;
    const session = state.session;
    const scored = scoreOptions(state.options.map(optionQuery), state.dictionary, state.lookup);
    state.decision = decide(scored, mode);
    if (state.decision.known.length === 0) {
      notice("stateAllUnknown");
      renderDecision();
      return;
    }
    if (state.brain && state.scene) {
      runScene(state.decision, session).catch((error) => {
        console.warn("scene error:", error);
        if (state.session !== session) return;
        $("scene-status").textContent = tr("stateSceneError");
        renderDecision();
      });
      return;
    }
    renderDecision();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function spriteSlug(item) {
    return item.entry ? (state.spriteFallbacks[slugFor(item.entry.key)] || slugFor(item.entry.key)) : null;
  }

  // The brain snapshot shows the response being reported: the winner's recorded
  // run; in "opposite" the fly's own pick; in a tie the tied dish with the most
  // MN9 spikes. Null when the brain view or the replay is unavailable.
  async function snapshotFor(decision) {
    if (!state.brain || !decision.winner) return null;
    const candidates = decision.mode === "opposite" ? [decision.flyPick] : (decision.tie.length ? decision.tie : [decision.winner]);
    const loaded = await Promise.all(candidates.map(async (item) => {
      try { return { item, replay: await state.loadReplay(cellIdFor(item.cell)) }; } catch (_) { return null; }
    }));
    const best = loaded.filter(Boolean).sort((a, b) => (b.replay.header.mn9_left_count || 0) - (a.replay.header.mn9_left_count || 0))[0];
    if (!best) return null;
    const snap = renderSnapshot(state.brain.neurons, state.brain.neuropils, best.replay, 340, 2);
    const stats = replayStats(best.replay);
    return { canvas: snap.canvas, mn9: stats.mn9Left ?? snap.count, neurons: stats.totalNeurons };
  }

  async function showCard() {
    const canvas = $("share-card");
    const sprites = state.scene ? state.scene.sprites : null;
    const [snapshot] = await Promise.all([
      snapshotFor(state.decision).catch((error) => { console.warn("snapshot failed:", error); return null; }),
      sprites ? Promise.all(state.decision.known.map((item) => loadDishSprite(sprites, spriteSlug(item)).catch(() => null))) : null,
    ]);
    drawShareCard(canvas, state.decision, state.lang, {
      stub: Boolean(state.lookup.table.stub),
      sprites,
      snapshot,
      siteUrl: state.siteUrl,
      spriteFor: (item) => (sprites && spriteSlug(item) ? sprites.dishCache.get(spriteSlug(item)) || null : null),
    });
    try {
      $("download-link").href = canvas.toDataURL("image/png");
    } catch (_) {
      $("download-link").removeAttribute("href");
    }
    const dialog = $("card-dialog");
    if (!dialog.open) dialog.showModal();
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
      fetch("data/lookup_table.json").then((r) => r.json()),
    ]);
    state.dictionary = buildDictionary(dishes);
    state.lookup = buildLookup(table);
    $("stub-banner").hidden = !table.stub;
    const [fallbacks, sections, config] = await Promise.all([
      fetch("assets/dishes/fallbacks.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("data/sections.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("config.json").then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]);
    state.spriteFallbacks = (fallbacks && fallbacks.fallbacks) || {};
    state.sections = sections;
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
      state.idleFly = new IdleFly($("idle-fly"), sprites);
      renderOptions();
      $("layout-note").hidden = neurons.layout !== "placeholder";
    } catch (error) {
      console.warn("scene disabled:", error);
    }
  }

  // Reset discards the current run: a new session id makes every pending await
  // of the old run a no-op, and the run-time fields are cleared (F05). Skip is
  // different: it keeps the session and shows this run's result.
  function reset() {
    state.session += 1;
    if (state.token) state.token.cancel();
    state.token = null;
    if (state.brain) { state.brain.stop(); state.brain.setReplay(null); }
    if (state.scene) state.scene.stop();
    state.decision = null;
    state.sceneStatus = null;
    state.brainCaption = null;
    state.scenePlates = null;
    state.currentCell = null;
    state.currentItem = null;
    state.currentCellLevels = null;
    state.variant = "";
    state.appliedVariant = "";
    state.variantRequest += 1;
    $("brain-caption").textContent = "";
    $("silence-caption").textContent = "";
    $("mn9-pill").hidden = true;
    $("mn9-count").textContent = "0";
    renderSilenceControls();
    $("scene-panel").hidden = true;
    $("result-panel").hidden = true;
    if ($("card-dialog").open) $("card-dialog").close();
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
  $("view-all-btn").addEventListener("click", () => {
    library.open = !library.open;
    renderTasted();
    if (library.open) $("library-search").focus({ preventScroll: true });
  });
  $("library-search").addEventListener("input", (event) => { library.query = event.target.value; renderTasted(); });
  $("ask-btn").addEventListener("click", () => run("ask"));
  $("opposite-btn").addEventListener("click", () => run("opposite"));
  $("share-btn").addEventListener("click", () => { showCard().catch((error) => console.warn("share card failed:", error)); });
  $("close-card-btn").addEventListener("click", () => $("card-dialog").close());
  $("card-dialog").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });
  $("again-btn").addEventListener("click", () => {
    reset();
    $("option-input").focus();
  });
  $("skip-btn").addEventListener("click", () => {
    if (state.token) state.token.cancel();
    if (state.brain) state.brain.stop();
    if (state.scenePlates) { for (const item of state.scenePlates) { item.loading = false; item.tasted = Boolean(item.cell); } relabelPlates(); }
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

  // Read-only view of the run state for browser regression checks (scripts/browser_checks.py).
  window.__askfly = {
    snapshot: () => ({
      phase: state.phase ?? null,
      session: state.session ?? null,
      currentCell: state.currentCell,
      variant: state.variant,
      options: state.options.map((o) => o.key || o.text),
      sceneRunning: Boolean(state.scene && state.scene.raf),
      brainPlaying: Boolean(state.brain && state.brain.raf),
      idleRunning: Boolean(state.idleFly && state.idleFly.raf),
      dialogOpen: $("card-dialog").open,
    }),
  };

  applyStrings();
  loadData().then(() => {
    // A shared link (?d=…&lang=…) fills the options and runs the sequence.
    const shared = parseShareParams(window.location.search);
    if (!shared || !state.dictionary) return;
    if (shared.lang && shared.lang !== state.lang) {
      state.lang = shared.lang; // for this view only; the saved preference is untouched
      applyStrings();
    }
    for (const option of resolveShared(shared.names, state.dictionary)) addSelection(option);
    if (state.options.length >= 2) run(shared.mode);
  }).catch((error) => {
    console.warn("data load failed:", error);
    notice("stateDataFailed");
  });
  window.addEventListener("offline", () => notice("stateOffline"));
  window.addEventListener("online", () => { if ($("notice").textContent === tr("stateOffline")) notice(null); });
}
