// SPDX-License-Identifier: MIT
// Ask the Fly — static front end. No LLM calls: dictionary lookup + lookup-table read.
// Pure functions are exported so they can be unit-tested with node (see test/).

export const LEVELS = ["none", "low", "medium", "high", "very_high"];
export const DIMENSIONS = ["sugar", "bitter", "water", "ir94e"];

// Set this to the public repository once it exists; the report button opens a prefilled issue there.
export const REPO_URL = "https://github.com/Felix471/ask-the-fly";

export const STRINGS = {
  en: {
    title: "Ask the Fly",
    lead: "Type the dishes you are choosing between. A fly-brain model tastes each one.",
    inputPlaceholder: "a dish, e.g. mapo tofu",
    add: "Add",
    hint: "Add at least two options. The fly only does the first bite.",
    ask: "Ask the fly",
    opposite: "Do the opposite",
    share: "Share card",
    again: "Ask again",
    download: "Save image",
    close: "Close",
    colOption: "Option",
    colSugar: "Sugar",
    colBitter: "Bitter",
    colWater: "Water",
    colMn9: "MN9 (Hz)",
    verdictAsk: "The fly picks",
    verdictOpposite: "The fly would pick {fly}. You do the opposite:",
    verdictTie: "The fly cannot tell these apart:",
    verdictNone: "The fly has not tasted any of these yet.",
    missTitle: "The fly hasn't tasted this yet.",
    missReport: "Report it",
    missNote: "Not in the dictionary: {names}",
    honesty: "In this model weak water is only visible as a helper to sugar; the fly notices water when the food is mostly water.",
    provenance: "Scores come from a published female-brain LIF model (Shiu 2024 / FlyWire v783). It only does the first bite.",
    stubBanner: "STUB DATA: the lookup table on this page is a placeholder, not simulation output.",
    tableMeta: "Lookup table {version} · {cells} cells · {trials} trials per cell",
    cardTitle: "Ask the Fly",
    cardPicked: "The fly picks",
    cardOppositePicked: "The fly picks {fly}; I take",
    cardTie: "The fly can't tell these apart",
    levelNames: { none: "none", low: "low", medium: "medium", high: "high", very_high: "very high" },
    // The four fixed lines (product owner, 2026-09-11). Placeholders are filled by cardLines().
    fixedLines: [
      "Today's pick: {dish}",
      "MN9: {hz} Hz (sugar response {hz_sugar_only} · after bitter suppression {hz})",
      "Taste input: sugar {sugar} · bitter {bitter} · water {water} (estimated by LLM)",
      "Simulation: precomputed from the whole-brain connectome, not run live",
    ],
    cardBottom: "The model turns the dish into taste signals. The connectome predicts whether the fly would extend its proboscis. We use that response to choose the winner.",
  },
  zh: {
    title: "问问果蝇",
    lead: "输入你在纠结的几道菜，让一只果蝇脑模型逐个尝一口。",
    inputPlaceholder: "一道菜，例如：麻婆豆腐",
    add: "添加",
    hint: "至少加两个选项。果蝇只管第一口。",
    ask: "问问果蝇",
    opposite: "反着来",
    share: "生成分享卡",
    again: "再问一次",
    download: "保存图片",
    close: "关闭",
    colOption: "选项",
    colSugar: "糖",
    colBitter: "苦",
    colWater: "水",
    colMn9: "MN9 (Hz)",
    verdictAsk: "果蝇选",
    verdictOpposite: "果蝇会选 {fly}。你反着来：",
    verdictTie: "果蝇分不出这几个：",
    verdictNone: "这些果蝇都还没尝过。",
    missTitle: "果蝇还没尝过这个。",
    missReport: "报上去",
    missNote: "词典里没有：{names}",
    honesty: "在这个模型里，微量的水只在帮糖时才被看见；只有食物基本是水时，果蝇才注意到水。",
    provenance: "分数来自已发表的雌性果蝇脑 LIF 模型（Shiu 2024 / FlyWire v783）。它只管第一口。",
    stubBanner: "占位数据：本页的查找表是占位符，不是仿真结果。",
    tableMeta: "查找表 {version} · {cells} 个格子 · 每格 {trials} 次试验",
    cardTitle: "问问果蝇",
    cardPicked: "果蝇选",
    cardOppositePicked: "果蝇选 {fly}，我反着来：",
    cardTie: "果蝇分不出这几个",
    levelNames: { none: "无", low: "低", medium: "中", high: "高", very_high: "很高" },
    fixedLines: [
      "今日选择：{dish}",
      "MN9：{hz} Hz（甜味反应 {hz_sugar_only} · 加入苦味抑制后 {hz}）",
      "味觉输入：甜 {sugar} · 苦 {bitter} · 水 {water}（由 LLM 估算）",
      "仿真：基于全脑连接组预先计算，并非现场实时运行",
    ],
    cardBottom: "模型先把菜品转换成味觉信号，连接组再预测果蝇会不会伸出口器。最后我们根据这个反应决定选哪一道。",
  },
};

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

export function issueUrl(name, lang) {
  const title = `New dish: ${name}`;
  const body = [
    "The fly hasn't tasted this yet.",
    "",
    `- name as typed: ${name}`,
    `- language: ${lang}`,
    "- zh name: ",
    "- en name: ",
    "- what it is (one line): ",
  ].join("\n");
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
    : { dish: "—", hz: "—", hz_sugar_only: "—", sugar: "—", bitter: "—", water: "—" };
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
    ctx.fillText(`${item.cell.mn9_mean.toFixed(1)} Hz`, W - pad, y);
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
    ctx.fillText(`+${ranked.length - shown.length}`, pad, y);
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
    ctx.fillText("STUB DATA", pad, H - 30);
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
  };

  const $ = (id) => document.getElementById(id);

  function applyStrings() {
    const t = STRINGS[state.lang];
    document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
    document.title = state.lang === "zh" ? "问问果蝇 · Ask the Fly" : "Ask the Fly · 问问果蝇";
    for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t[el.dataset.i18n] ?? "";
    for (const el of document.querySelectorAll("[data-i18n-placeholder]")) el.placeholder = t[el.dataset.i18nPlaceholder] ?? "";
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
    if (state.decision) renderDecision();
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
      remove.setAttribute("aria-label", `remove ${name}`);
      remove.addEventListener("click", () => {
        state.options.splice(index, 1);
        renderOptions();
      });
      li.append(span, remove);
      list.append(li);
    });
    const ready = state.options.length >= 2 && state.lookup && state.dictionary;
    $("ask-btn").disabled = !ready;
    $("opposite-btn").disabled = !ready;
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
        mn9.textContent = `${item.cell.mn9_mean.toFixed(1)} ± ${item.cell.mn9_std.toFixed(1)}`;
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

  function run(mode) {
    if (!state.lookup || !state.dictionary) return;
    const scored = scoreOptions(state.options, state.dictionary, state.lookup);
    state.decision = decide(scored, mode);
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
    applyStrings();
  }

  $("lang-toggle").addEventListener("click", () => {
    state.lang = state.lang === "zh" ? "en" : "zh";
    try { localStorage.setItem("askfly.lang", state.lang); } catch (_) { /* ignore */ }
    applyStrings();
  });
  $("option-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const input = $("option-input");
    addOption(input.value);
    input.value = "";
    input.focus();
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
    state.decision = null;
    $("result-panel").hidden = true;
    $("card-panel").hidden = true;
    $("input-panel").hidden = false;
    $("option-input").focus();
  });

  applyStrings();
  loadData().catch((error) => {
    $("verdict").textContent = `Failed to load data: ${error.message}`;
    $("result-panel").hidden = false;
  });
}
