// SPDX-License-Identifier: MIT
// Brain view: draws site/data/neurons.json as faint dots and replays one recorded
// trial (site/data/replay/<cell>.bin) over 1 s. Everything drawn as activity is a
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

export const FLAG = { sugar: 1, bitter: 2, water: 4, ir94e: 8, mn9_left: 16, mn9_right: 32 };

export const COLORS = {
  background: "#14110e",
  dot: "rgba(240, 232, 220, 0.16)",
  spike: "rgba(240, 232, 220, 0.85)",
  sugar: "#e0774a",
  bitter: "#8e6bd6",
  water: "#4aa3df",
  ir94e: "#3fb3a1",
  mn9: "#ffd84a",
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
  return { n: json.n, nIndexed: json.n_indexed, layout: json.layout, xy, flags, gitCommit: json.git_commit };
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
  return COLORS.spike;
}

export class BrainView {
  constructor(canvas, neurons) {
    this.canvas = canvas;
    this.neurons = neurons;
    this.replay = null;
    this.speed = 1;
    this.onMn9 = null;
    this.onEnd = null;
    this.raf = 0;
    this.background = null;
    this.pixelRatio = typeof devicePixelRatio === "number" ? Math.min(2, devicePixelRatio) : 1;
    this.resize();
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

  project(i) {
    const pad = 12 * this.pixelRatio;
    const x = pad + (this.neurons.xy[i * 2] / 65535) * (this.canvas.width - 2 * pad);
    const y = pad + (this.neurons.xy[i * 2 + 1] / 65535) * (this.canvas.height - 2 * pad);
    return [x, y];
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
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, off.width, off.height);
    const r = Math.max(0.6, 0.9 * this.pixelRatio);
    ctx.fillStyle = COLORS.dot;
    for (let i = 0; i < this.neurons.n; i += 1) {
      const [x, y] = this.project(i);
      ctx.fillRect(x - r / 2, y - r / 2, r, r);
    }
    // Input and readout populations get a faint tinted halo so the eye can find them.
    for (let i = 0; i < this.neurons.nIndexed; i += 1) {
      const f = this.neurons.flags[i];
      if (!f) continue;
      const [x, y] = this.project(i);
      ctx.fillStyle = spikeColor(f);
      ctx.globalAlpha = 0.35;
      ctx.beginPath();
      ctx.arc(x, y, 1.6 * this.pixelRatio, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
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
        const x = this.px[i];
        const y = this.py[i];
        ctx.fillRect(x - size / 2, y - size / 2, size, size);
      }
    }
    for (let k = 0; k < special.length; k += 2) {
      const i = special[k];
      const age = special[k + 1];
      ctx.globalAlpha = 1 - 0.6 * age;
      ctx.fillStyle = spikeColor(flags[i]);
      ctx.beginPath();
      ctx.arc(this.px[i], this.py[i], 3.2 * pr * (1.35 - 0.35 * age), 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  // Plays the loaded replay in real time × speed. Resolves when the trial ends.
  play(speed = 1) {
    this.stop();
    this.speed = speed;
    if (!this.replay) return Promise.resolve();
    const left = this.replay.header.mn9_left_ms;
    const duration = this.replay.header.duration_ms;
    return new Promise((resolve) => {
      const start = performance.now();
      let counted = 0;
      const tick = (now) => {
        const tMs = Math.min(duration, (now - start) * this.speed);
        this.drawFrame(tMs);
        while (counted < left.length && left[counted] <= tMs) {
          counted += 1;
          if (this.onMn9) this.onMn9(counted, left.length);
        }
        if (tMs >= duration) {
          this.raf = 0;
          if (this.onMn9) this.onMn9(left.length, left.length);
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

// Fetches and caches replay files by cell id.
export function makeReplayLoader(baseUrl = "data/replay/") {
  const cache = new Map();
  return async function load(cellId) {
    if (cache.has(cellId)) return cache.get(cellId);
    const promise = fetch(`${baseUrl}${cellId}.bin`).then(async (response) => {
      if (!response.ok) throw new Error(`replay ${cellId}: HTTP ${response.status}`);
      return parseReplay(await response.arrayBuffer());
    });
    cache.set(cellId, promise);
    return promise;
  };
}
