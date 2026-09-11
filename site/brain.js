// SPDX-License-Identifier: MIT
// Brain view: neuropil outlines (FlyWire-space meshes projected to 2D), neurons at
// their FlyWire soma positions, and a replay of one recorded trial
// (site/data/replay/<cell>[_silence_<name>].bin). Everything drawn as activity is a
// replay of recorded simulation output; nothing is simulated in the browser.

// requestAnimationFrame pauses in background tabs; fall back to a timer so a
// sequence started before the tab was hidden still completes.
export function frame(callback) {
  if (typeof document !== "undefined" && document.hidden) return setTimeout(() => callback(performance.now()), 16);
  return requestAnimationFrame(callback);
}

export const BIN_MS = 10;
export const BINS_IN_WINDOW = 5; // 50 ms trail

// Groups a replay's spikes into BIN_MS bins of unique neuron indices.
export function binReplay(replay, binMs = BIN_MS) {
  const nBins = Math.ceil(replay.header.duration_ms / binMs);
  const bins = new Array(nBins);
  const { idx, t } = replay;
  let i = 0;
  for (let b = 0; b < nBins; b += 1) {
    const endUnits = (b + 1) * binMs * 10;
    const seen = new Set();
    while (i < t.length && t[i] < endUnits) {
      seen.add(idx[i]);
      i += 1;
    }
    bins[b] = Uint32Array.from(seen);
  }
  return bins;
}

export const FLAG = { sugar: 1, bitter: 2, water: 4, ir94e: 8, mn9_left: 16, mn9_right: 32, named: 64 };

export const COLORS = {
  background: "#14110e",
  dot: "rgba(240, 232, 220, 0.16)",
  spike: "rgba(240, 232, 220, 0.85)",
  sugar: "#e0774a",
  bitter: "#8e6bd6",
  water: "#4aa3df",
  ir94e: "#3fb3a1",
  mn9: "#ffd84a",
  named: "#f0e6c8",
  neuropil: "rgba(240, 232, 220, 0.22)",
  neuropilFill: "rgba(240, 232, 220, 0.035)",
  label: "rgba(240, 232, 220, 0.55)",
};

function b64ToBytes(b64) {
  if (typeof atob === "function") {
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i += 1) out[i] = bin.charCodeAt(i);
    return out;
  }
  return new Uint8Array(Buffer.from(b64, "base64"));
}

export function decodeNeurons(json) {
  const xyBytes = b64ToBytes(json.xy_b64);
  const xy = new Uint16Array(xyBytes.buffer, xyBytes.byteOffset, xyBytes.byteLength / 2);
  const flags = b64ToBytes(json.flags_b64);
  if (xy.length !== json.n * 2 || flags.length !== json.n) throw new Error("neurons.json: length mismatch");
  return {
    n: json.n, nIndexed: json.n_indexed, layout: json.layout, xy, flags, gitCommit: json.git_commit,
    named: json.named || [], frame: json.frame || null,
  };
}

export function parseReplay(buffer) {
  const bytes = new Uint8Array(buffer);
  const magic = String.fromCharCode(bytes[0], bytes[1], bytes[2], bytes[3]);
  if (magic !== "AFR1") throw new Error(`replay: bad magic ${magic}`);
  const view = new DataView(buffer);
  const hlen = view.getUint32(4, true);
  const header = JSON.parse(new TextDecoder("utf-8").decode(bytes.subarray(8, 8 + hlen)));
  const n = header.n_spikes;
  let offset = 8 + hlen;
  const wide = header.idx_dtype !== "u16";
  const idx = new Uint32Array(n);
  const t = new Uint16Array(n);
  for (let i = 0; i < n; i += 1) idx[i] = wide ? view.getUint32(offset + i * 4, true) : view.getUint16(offset + i * 2, true);
  offset += n * (wide ? 4 : 2);
  for (let i = 0; i < n; i += 1) t[i] = view.getUint16(offset + i * 2, true);
  return { header, idx, t };
}

// Canonical cell id for a lookup-table cell (its level names are already canonical).
export function cellIdFor(cell) {
  return `G_s${cell.sugar}_b${cell.bitter}_w${cell.water}_i${cell.ir94e}`;
}

export function spikeColor(flag) {
  if (flag & (FLAG.mn9_left | FLAG.mn9_right)) return COLORS.mn9;
  if (flag & FLAG.sugar) return COLORS.sugar;
  if (flag & FLAG.bitter) return COLORS.bitter;
  if (flag & FLAG.water) return COLORS.water;
  if (flag & FLAG.ir94e) return COLORS.ir94e;
  if (flag & FLAG.named) return COLORS.named;
  return COLORS.spike;
}

// HUD numbers, all read from the replay header (recorded, never computed live).
export function replayStats(replay) {
  const h = replay.header;
  return {
    totalNeurons: h.n_model_neurons ?? null,
    activeNeurons: h.n_neurons_active,
    spikes: h.n_spikes,
    mn9Left: h.mn9_left_count,
    mn9Right: h.mn9_right_count,
    mn9FirstMs: h.mn9_left_first_ms ?? (h.mn9_left_ms && h.mn9_left_ms.length ? h.mn9_left_ms[0] : null),
    hz: h.hz,
    seed: h.seed,
    variant: h.variant || "baseline",
    silenced: h.silenced || null,
  };
}

// Raster rows built from the replay: one row per population, ticks at recorded times.
// Returns [{key, label, colour, times: Float32Array (ms)}] in display order.
export function rasterRows(replay, neurons, labels) {
  const groups = [
    { key: "sugar", bit: FLAG.sugar, colour: COLORS.sugar },
    { key: "bitter", bit: FLAG.bitter, colour: COLORS.bitter },
    { key: "water", bit: FLAG.water, colour: COLORS.water },
  ];
  const namedIndex = new Map();
  for (const entry of neurons.named) for (const cell of entry.cells) namedIndex.set(cell.index, entry.key);
  const buckets = new Map(groups.map((g) => [g.key, []]));
  for (const entry of neurons.named) buckets.set(`named:${entry.key}`, []);
  buckets.set("mn9_left", []);
  buckets.set("mn9_right", []);
  const { idx, t } = replay;
  for (let i = 0; i < idx.length; i += 1) {
    const f = idx[i] < neurons.flags.length ? neurons.flags[idx[i]] : 0;
    if (!f) continue;
    const ms = t[i] / 10;
    if (f & FLAG.mn9_left) buckets.get("mn9_left").push(ms);
    else if (f & FLAG.mn9_right) buckets.get("mn9_right").push(ms);
    if (f & FLAG.named) {
      const key = namedIndex.get(idx[i]);
      if (key) buckets.get(`named:${key}`).push(ms);
    }
    for (const g of groups) if (f & g.bit) buckets.get(g.key).push(ms);
  }
  const rows = groups.map((g) => ({ key: g.key, label: labels[g.key] || g.key, colour: g.colour, times: Float32Array.from(buckets.get(g.key)) }));
  for (const entry of neurons.named) {
    rows.push({ key: `named:${entry.key}`, label: entry.label, colour: COLORS.named, times: Float32Array.from(buckets.get(`named:${entry.key}`)) });
  }
  rows.push({ key: "mn9_left", label: labels.mn9_left || "MN9 L", colour: COLORS.mn9, times: Float32Array.from(buckets.get("mn9_left")) });
  rows.push({ key: "mn9_right", label: labels.mn9_right || "MN9 R", colour: COLORS.mn9, times: Float32Array.from(buckets.get("mn9_right")) });
  return rows;
}

export class BrainView {
  constructor(canvas, neurons, options = {}) {
    this.canvas = canvas;
    this.neurons = neurons;
    this.neuropils = options.neuropils || null;
    this.lang = options.lang || "en";
    this.showLabels = options.showLabels !== false;
    this.replay = null;
    this.bins = null;
    this.speed = 1;
    this.onMn9 = null;
    this.onTime = null;
    this.raf = 0;
    this.background = null;
    this.pixelRatio = options.pixelRatio || (typeof devicePixelRatio === "number" ? Math.min(2, devicePixelRatio) : 1);
    this.resize();
  }

  setLang(lang) {
    this.lang = lang;
    this.background = null;
    this.drawStatic();
  }

  resize() {
    const cssWidth = this.canvas.clientWidth || this.canvas.width;
    const cssHeight = Math.round(cssWidth * 0.72);
    this.canvas.width = Math.round(cssWidth * this.pixelRatio);
    this.canvas.height = Math.round(cssHeight * this.pixelRatio);
    this.canvas.style.height = `${cssHeight}px`;
    this.background = null;
    this.drawStatic();
  }

  toCanvas(nx, ny) {
    const pad = 12 * this.pixelRatio;
    return [pad + nx * (this.canvas.width - 2 * pad), pad + ny * (this.canvas.height - 2 * pad)];
  }

  project(i) {
    return this.toCanvas(this.neurons.xy[i * 2] / 65535, this.neurons.xy[i * 2 + 1] / 65535);
  }

  buildBackground() {
    const n = this.neurons.n;
    this.px = new Float32Array(n);
    this.py = new Float32Array(n);
    for (let i = 0; i < n; i += 1) {
      const [x, y] = this.project(i);
      this.px[i] = x;
      this.py[i] = y;
    }
    const off = document.createElement("canvas");
    off.width = this.canvas.width;
    off.height = this.canvas.height;
    const ctx = off.getContext("2d");
    const pr = this.pixelRatio;
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, off.width, off.height);
    // Neuropil outlines under the dots (anterior view, same frame as the neurons).
    if (this.neuropils) {
      ctx.lineWidth = 1 * pr;
      for (const group of this.neuropils.groups) {
        ctx.beginPath();
        group.polygon.forEach(([x, y], k) => {
          const [cx, cy] = this.toCanvas(x, y);
          if (k === 0) ctx.moveTo(cx, cy);
          else ctx.lineTo(cx, cy);
        });
        ctx.closePath();
        ctx.fillStyle = COLORS.neuropilFill;
        ctx.fill();
        ctx.strokeStyle = COLORS.neuropil;
        ctx.stroke();
      }
      if (this.showLabels) {
        ctx.font = `${10 * pr}px system-ui, -apple-system, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", sans-serif`;
        ctx.fillStyle = COLORS.label;
        ctx.textAlign = "center";
        for (const group of this.neuropils.groups) {
          const [lx, ly] = this.toCanvas(group.label_at[0], group.label_at[1]);
          const text = this.lang === "zh" ? `${group.label_en} ${group.label_zh}` : group.label_en;
          ctx.fillText(text, lx, ly);
        }
        ctx.textAlign = "left";
      }
    }
    const r = Math.max(0.6, 0.9 * pr);
    ctx.fillStyle = COLORS.dot;
    for (let i = 0; i < n; i += 1) ctx.fillRect(this.px[i] - r / 2, this.py[i] - r / 2, r, r);
    // Input and readout populations get a faint tinted halo so the eye can find them.
    for (let i = 0; i < this.neurons.nIndexed; i += 1) {
      const f = this.neurons.flags[i];
      if (!f) continue;
      ctx.fillStyle = spikeColor(f);
      ctx.globalAlpha = f & FLAG.named ? 0.6 : 0.35;
      ctx.beginPath();
      ctx.arc(this.px[i], this.py[i], (f & FLAG.named ? 2.6 : 1.6) * pr, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
    // Named neurons: larger ring per cell; labels stacked along the bottom edge
    // (they all sit in the SEZ) with a thin leader line to the first cell.
    if (this.showLabels && this.neurons.named.length) {
      ctx.font = `${9 * pr}px system-ui, -apple-system, "Segoe UI", sans-serif`;
      ctx.lineWidth = 0.8 * pr;
      for (const entry of this.neurons.named) {
        ctx.strokeStyle = COLORS.named;
        for (const cell of entry.cells) {
          ctx.beginPath();
          ctx.arc(this.px[cell.index], this.py[cell.index], 3.6 * pr, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
      const ordered = [...this.neurons.named].sort((a, b) => this.px[a.cells[0].index] - this.px[b.cells[0].index]);
      const slot = (off.width - 24 * pr) / ordered.length;
      ctx.textAlign = "center";
      ordered.forEach((entry, k) => {
        const first = entry.cells[0];
        const lx = 12 * pr + slot * (k + 0.5);
        const ly = off.height - (k % 2 === 0 ? 6 : 18) * pr;
        ctx.strokeStyle = "rgba(240, 230, 200, 0.35)";
        ctx.beginPath();
        ctx.moveTo(this.px[first.index], this.py[first.index] + 4 * pr);
        ctx.lineTo(lx, ly - 10 * pr);
        ctx.stroke();
        ctx.fillStyle = COLORS.named;
        ctx.fillText(entry.label, lx, ly);
      });
      ctx.textAlign = "left";
    }
    this.background = off;
  }

  drawStatic() {
    if (!this.background) this.buildBackground();
    const ctx = this.canvas.getContext("2d");
    ctx.drawImage(this.background, 0, 0);
  }

  setReplay(replay) {
    this.stop();
    this.replay = replay;
    this.bins = replay ? binReplay(replay, BIN_MS) : null;
    this.drawStatic();
  }

  drawFrame(tMs) {
    const ctx = this.canvas.getContext("2d");
    ctx.drawImage(this.background, 0, 0);
    if (!this.replay || !this.bins) return;
    // Draws are batched per BIN_MS bin: each neuron is painted once per bin it
    // spiked in, so a frame costs at most (bins in window) x (unique neurons),
    // whatever the raw spike count. Flagged neurons are painted last, on top.
    const windowMs = BIN_MS * BINS_IN_WINDOW;
    const lastBin = Math.min(this.bins.length - 1, Math.floor(tMs / BIN_MS));
    const firstBin = Math.max(0, Math.floor((tMs - windowMs) / BIN_MS));
    const pr = this.pixelRatio;
    const flags = this.neurons.flags;
    const special = [];
    for (let b = firstBin; b <= lastBin; b += 1) {
      const age = Math.min(1, Math.max(0, (tMs - b * BIN_MS) / windowMs));
      const size = 2 * pr * (1.5 - 0.6 * age);
      ctx.globalAlpha = 0.9 - 0.8 * age;
      ctx.fillStyle = COLORS.spike;
      const list = this.bins[b];
      for (let k = 0; k < list.length; k += 1) {
        const i = list[k];
        if (i < flags.length && flags[i]) {
          special.push(i, age);
          continue;
        }
        ctx.fillRect(this.px[i] - size / 2, this.py[i] - size / 2, size, size);
      }
    }
    for (let k = 0; k < special.length; k += 2) {
      const i = special[k];
      const age = special[k + 1];
      const f = flags[i];
      ctx.globalAlpha = 1 - 0.6 * age;
      ctx.fillStyle = spikeColor(f);
      ctx.beginPath();
      ctx.arc(this.px[i], this.py[i], (f & FLAG.named ? 4.5 : 3.2) * pr * (1.35 - 0.35 * age), 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  // Plays the loaded replay: simulated time accumulates per frame from the
  // wall-clock delta × the speed in force at that frame, so changing the speed
  // never rewinds or jumps (F09). Resolves when the trial ends.
  play(speed = 1) {
    this.stop();
    this.speed = speed;
    if (!this.replay) return Promise.resolve();
    const playback = createPlayback(this.replay);
    const total = playback.left.length;
    return new Promise((resolve) => {
      const tick = (now) => {
        const { tMs, newSpikes, finished } = advancePlayback(playback, now, this.speed);
        this.drawFrame(tMs);
        if (this.onTime) this.onTime(tMs);
        for (let k = 0; k < newSpikes; k += 1) {
          if (this.onMn9) this.onMn9(playback.counted - newSpikes + k + 1, total);
        }
        if (finished) {
          this.raf = 0;
          this.resolvePlay = null;
          resolve();
          return;
        }
        this.raf = frame(tick);
      };
      this.raf = frame(tick);
      this.resolvePlay = resolve;
    });
  }

  stop() {
    if (this.raf) { cancelAnimationFrame(this.raf); clearTimeout(this.raf); }
    this.raf = 0;
    if (this.resolvePlay) {
      const done = this.resolvePlay;
      this.resolvePlay = null;
      done();
    }
  }
}

// Oscilloscope-style raster: rows of ticks, time axis 0..duration, revealed up to tMs.
// The window (BIN_MS x BINS_IN_WINDOW, i.e. what one drawn frame shows) with the
// most MN9 spikes in a replay: its end time in ms and the MN9 spike count inside.
// Without any MN9 spike, the busiest single bin is used instead (count 0).
export function peakMn9Window(replay, neurons, windowMs = BIN_MS * BINS_IN_WINDOW) {
  const { idx, t } = replay;
  const flags = neurons.flags;
  const times = [];
  for (let i = 0; i < idx.length; i += 1) {
    const n = idx[i];
    if (n < flags.length && (flags[n] & (FLAG.mn9_left | FLAG.mn9_right))) times.push(t[i] / 10);
  }
  if (!times.length) {
    const bins = binReplay(replay);
    let best = 0;
    for (let b = 1; b < bins.length; b += 1) if (bins[b].length > bins[best].length) best = b;
    return { tMs: Math.min(replay.header.duration_ms, (best + 1) * BIN_MS), count: 0 };
  }
  times.sort((a, b) => a - b);
  let best = 0;
  let bestEnd = times[0];
  let j = 0;
  for (let i = 0; i < times.length; i += 1) {
    while (times[i] - times[j] > windowMs) j += 1;
    if (i - j + 1 > best) {
      best = i - j + 1;
      bestEnd = times[i];
    }
  }
  return { tMs: Math.min(replay.header.duration_ms, bestEnd + 1), count: best };
}

// One frame of a replay on an offscreen canvas with the brain view's renderer
// (outlines, dots, spikes; no labels), at the frame with the most MN9 activity,
// MN9 cells ringed. For the share card. Browser only (needs a canvas).
export function renderSnapshot(neurons, neuropils, replay, width, pixelRatio = 2) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  const view = new BrainView(canvas, neurons, { neuropils, showLabels: false, pixelRatio });
  view.setReplay(replay);
  const peak = peakMn9Window(replay, neurons);
  view.drawFrame(peak.tMs);
  const ctx = canvas.getContext("2d");
  const pr = view.pixelRatio;
  ctx.strokeStyle = COLORS.mn9;
  ctx.lineWidth = 1.2 * pr;
  ctx.globalAlpha = 0.9;
  for (let i = 0; i < neurons.nIndexed; i += 1) {
    if (neurons.flags[i] & (FLAG.mn9_left | FLAG.mn9_right)) {
      ctx.beginPath();
      ctx.arc(view.px[i], view.py[i], 6 * pr, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  ctx.globalAlpha = 1;
  return { canvas, tMs: peak.tMs, count: peak.count };
}

export class RasterView {
  constructor(canvas) {
    this.canvas = canvas;
    this.rows = [];
    this.duration = 1000;
    this.pixelRatio = typeof devicePixelRatio === "number" ? Math.min(2, devicePixelRatio) : 1;
  }

  setRows(rows, duration = 1000) {
    this.rows = rows;
    this.duration = duration;
    const cssWidth = this.canvas.clientWidth || 360;
    const rowH = 14;
    const cssHeight = 22 + rows.length * rowH + 18;
    this.canvas.width = Math.round(cssWidth * this.pixelRatio);
    this.canvas.height = Math.round(cssHeight * this.pixelRatio);
    this.canvas.style.height = `${cssHeight}px`;
    this.draw(this.duration);
  }

  draw(tMs) {
    const ctx = this.canvas.getContext("2d");
    const pr = this.pixelRatio;
    const W = this.canvas.width;
    const H = this.canvas.height;
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, W, H);
    const labelW = 72 * pr;
    const x0 = labelW;
    const x1 = W - 8 * pr;
    const top = 8 * pr;
    const rowH = 14 * pr;
    ctx.font = `${9 * pr}px system-ui, -apple-system, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", sans-serif`;
    // time axis
    ctx.strokeStyle = "rgba(240,232,220,0.25)";
    ctx.fillStyle = "rgba(240,232,220,0.55)";
    ctx.lineWidth = 1 * pr;
    const axisY = top + this.rows.length * rowH + 4 * pr;
    ctx.beginPath();
    ctx.moveTo(x0, axisY);
    ctx.lineTo(x1, axisY);
    ctx.stroke();
    ctx.textAlign = "center";
    for (let ms = 0; ms <= this.duration; ms += 200) {
      const x = x0 + (ms / this.duration) * (x1 - x0);
      ctx.beginPath();
      ctx.moveTo(x, axisY);
      ctx.lineTo(x, axisY + 3 * pr);
      ctx.stroke();
      ctx.fillText(ms === this.duration ? `${ms} ms` : `${ms}`, x, axisY + 12 * pr);
    }
    ctx.textAlign = "right";
    this.rows.forEach((row, r) => {
      const y = top + r * rowH;
      ctx.fillStyle = "rgba(240,232,220,0.7)";
      ctx.fillText(row.label, x0 - 6 * pr, y + rowH * 0.75);
      ctx.fillStyle = "rgba(240,232,220,0.06)";
      ctx.fillRect(x0, y + 1, x1 - x0, rowH - 2);
      ctx.fillStyle = row.colour;
      ctx.globalAlpha = 0.65; // dense populations read as density rather than a solid bar
      const times = row.times;
      for (let k = 0; k < times.length && times[k] <= tMs; k += 1) {
        const x = x0 + (times[k] / this.duration) * (x1 - x0);
        ctx.fillRect(x, y + 2 * pr, Math.max(1, 1 * pr), rowH - 4 * pr);
      }
      ctx.globalAlpha = 1;
    });
    // playhead
    if (tMs < this.duration) {
      const x = x0 + (tMs / this.duration) * (x1 - x0);
      ctx.strokeStyle = "rgba(255,216,74,0.6)";
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, axisY);
      ctx.stroke();
    }
    ctx.textAlign = "left";
  }
}

// One short click per MN9 spike (WebAudio); created lazily on the first user gesture.
export class SpikeClick {
  constructor() {
    this.ctx = null;
    this.enabled = false;
  }

  enable(on) {
    this.enabled = on;
    if (on && !this.ctx && typeof AudioContext !== "undefined") this.ctx = new AudioContext();
    if (this.ctx && this.ctx.state === "suspended") this.ctx.resume();
  }

  click() {
    if (!this.enabled || !this.ctx) return;
    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = "square";
    osc.frequency.value = 1800;
    gain.gain.setValueAtTime(0.08, t);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.02);
    osc.connect(gain).connect(this.ctx.destination);
    osc.start(t);
    osc.stop(t + 0.025);
  }
}

// Fetches and caches replay files by cell id (and optional silencing variant).
// Replay loader: in-flight requests are shared and successes stay cached; a
// failed request (HTTP error or parse error) is dropped from the cache so the
// next call retries it (F01). `fetchImpl` is injectable for tests.
// Playback clock, pure so it can be tested with a fake clock: `t` is the
// simulated time in ms, `counted` the MN9 (left) spikes at or before t.
export function createPlayback(replay) {
  return { t: 0, last: null, counted: 0, done: false, duration: replay.header.duration_ms, left: replay.header.mn9_left_ms || [] };
}

// Advances by (nowMs - previous nowMs) × speed, clamps at the duration, and
// returns the new time, how many MN9 spikes were crossed, and whether the
// trial ended on this step (reported once).
export function advancePlayback(playback, nowMs, speed) {
  if (playback.done) return { tMs: playback.t, newSpikes: 0, finished: false };
  if (playback.last == null) playback.last = nowMs;
  const dt = Math.max(0, nowMs - playback.last);
  playback.last = nowMs;
  playback.t = Math.min(playback.duration, playback.t + dt * Math.max(0, speed));
  let newSpikes = 0;
  while (playback.counted < playback.left.length && playback.left[playback.counted] <= playback.t) {
    playback.counted += 1;
    newSpikes += 1;
  }
  const finished = playback.t >= playback.duration;
  if (finished) playback.done = true;
  return { tMs: playback.t, newSpikes, finished };
}

export function makeReplayLoader(baseUrl = "data/replay/", fetchImpl = null) {
  const cache = new Map();
  return async function load(cellId, variant = "") {
    const key = variant ? `${cellId}_silence_${variant}` : cellId;
    if (cache.has(key)) return cache.get(key);
    const doFetch = fetchImpl || globalThis.fetch;
    const promise = doFetch(`${baseUrl}${key}.bin`).then(async (response) => {
      if (!response.ok) throw new Error(`replay ${key}: HTTP ${response.status}`);
      return parseReplay(await response.arrayBuffer());
    });
    cache.set(key, promise);
    promise.catch(() => { if (cache.get(key) === promise) cache.delete(key); });
    return promise;
  };
}
