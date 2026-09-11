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
    this.drawStatic();
  }

  drawFrame(tMs) {
    const ctx = this.canvas.getContext("2d");
    ctx.drawImage(this.background, 0, 0);
    if (!this.replay) return;
    const { idx, t } = this.replay;
    const windowMs = 45;
    const tUnits = tMs * 10;
    const startUnits = Math.max(0, (tMs - windowMs) * 10);
    // t is sorted ascending: binary search the window start, scan to the end.
    let lo = 0;
    let hi = t.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (t[mid] < startUnits) lo = mid + 1;
      else hi = mid;
    }
    const pr = this.pixelRatio;
    for (let i = lo; i < t.length && t[i] <= tUnits; i += 1) {
      const age = (tUnits - t[i]) / 10 / windowMs; // 0 fresh .. 1 old
      const f = idx[i] < this.neurons.flags.length ? this.neurons.flags[idx[i]] : 0;
      const [x, y] = this.project(idx[i]);
      const special = f !== 0;
      const radius = (special ? 3.2 : 1.7) * pr * (1.35 - 0.35 * age);
      ctx.globalAlpha = special ? 1 - 0.6 * age : 0.9 - 0.8 * age;
      ctx.fillStyle = spikeColor(f);
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
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
