// SPDX-License-Identifier: MIT
// Fly scene: plates in a row (grid on narrow screens), a fly that visits each
// plate, and the winner sequence. Sprites from site/assets/ when present,
// placeholder shapes otherwise. The scene never decides anything; it animates
// the decision computed in app.js.

// requestAnimationFrame pauses in background tabs; fall back to a timer so a
// sequence started before the tab was hidden still completes.
export function frame(callback) {
  if (typeof document !== "undefined" && document.hidden) return setTimeout(() => callback(performance.now()), 16);
  return requestAnimationFrame(callback);
}

const PLATE = 96;
const ROW_HEIGHT = 150;
const FLY_SPEED_PX_S = 520;
// Every fly state draws from the same four sprite sets; "hover" (tie, turning
// away) and "taste" have no frames of their own.
export const FRAME_SET = { idle: "idle", fly: "fly", land: "land", taste: "land", hover: "idle", proboscis: "proboscis" };


function sleep(ms, token) {
  return new Promise((resolve) => {
    if (token.cancelled) return resolve();
    const id = setTimeout(resolve, ms);
    token.onCancel.push(() => { clearTimeout(id); resolve(); });
  });
}

export function makeToken() {
  const token = { cancelled: false, onCancel: [] };
  token.cancel = () => {
    token.cancelled = true;
    for (const fn of token.onCancel.splice(0)) fn();
  };
  return token;
}

export function layoutPlates(count, width) {
  const perRow = Math.max(1, Math.min(count, Math.floor((width - 16) / (PLATE + 28))));
  const rows = Math.ceil(count / perRow);
  const positions = [];
  for (let i = 0; i < count; i += 1) {
    const row = Math.floor(i / perRow);
    const inRow = Math.min(perRow, count - row * perRow);
    const col = i - row * perRow;
    const span = inRow * (PLATE + 28) - 28;
    const x = (width - span) / 2 + col * (PLATE + 28) + PLATE / 2;
    const y = 70 + row * ROW_HEIGHT + PLATE / 2;
    positions.push({ x, y });
  }
  return { positions, height: 70 + rows * ROW_HEIGHT };
}

async function loadImage(url) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = url;
  });
}

// Loads (once) and returns the sprite for a dish slug, or null when none exists.
export async function loadDishSprite(sprites, slug) {
  if (!slug) return null;
  if (!sprites.dishCache.has(slug)) sprites.dishCache.set(slug, await loadImage(`${sprites.base}dishes/${slug}.png`));
  return sprites.dishCache.get(slug);
}

export async function loadSprites(base = "assets/") {
  const fly = {};
  const frames = { idle: 2, fly: 4, land: 1, proboscis: 3 };
  await Promise.all(Object.entries(frames).map(async ([state, n]) => {
    const list = await Promise.all(Array.from({ length: n }, (_, i) => loadImage(`${base}fly/${state}_${i + 1}.png`)));
    fly[state] = list.every(Boolean) ? list : null;
  }));
  return { fly, dishCache: new Map(), base };
}

// The resting fly next to the empty table: idle frames at 3 fps on a small canvas.
export class IdleFly {
  constructor(canvas, sprites) {
    this.canvas = canvas;
    this.sprites = sprites;
    this.raf = 0;
    this.t = 0;
    this.last = 0;
  }

  start() {
    if (this.raf) return;
    const loop = (now) => {
      this.t += this.last ? (now - this.last) / 1000 : 0;
      this.last = now;
      this.draw();
      this.raf = frame(loop);
    };
    this.raf = frame(loop);
  }

  stop() {
    if (this.raf) { cancelAnimationFrame(this.raf); clearTimeout(this.raf); }
    this.raf = 0;
    this.last = 0;
  }

  draw() {
    const ctx = this.canvas.getContext("2d");
    const size = this.canvas.width;
    ctx.clearRect(0, 0, size, this.canvas.height);
    const frames = this.sprites && this.sprites.fly && this.sprites.fly.idle;
    if (frames) {
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(frames[Math.floor(this.t * 3) % frames.length], 0, 0, size, size);
    } else {
      ctx.fillStyle = "#2a2420";
      ctx.beginPath();
      ctx.ellipse(size / 2, size / 2, size * 0.22, size * 0.12, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

export class FlyScene {
  constructor(canvas, sprites) {
    this.canvas = canvas;
    this.sprites = sprites || { fly: {}, dishCache: new Map(), base: "assets/" };
    this.plates = [];
    this.positions = [];
    this.fly = { x: 0, y: 0, dir: 1, state: "idle", frame: 0, t: 0, proboscis: 0 };
    this.pixelRatio = typeof devicePixelRatio === "number" ? Math.min(2, devicePixelRatio) : 1;
    this.raf = 0;
    this.lastTime = 0;
    this.highlight = -1;
  }

  async setPlates(plates) {
    this.plates = plates;
    const width = this.canvas.clientWidth || 360;
    const { positions, height } = layoutPlates(plates.length, width);
    this.positions = positions;
    this.canvas.width = Math.round(width * this.pixelRatio);
    this.canvas.height = Math.round(height * this.pixelRatio);
    this.canvas.style.height = `${height}px`;
    this.fly.x = width / 2;
    this.fly.y = 34;
    for (const plate of plates) await loadDishSprite(this.sprites, plate.slug);
    this.start();
  }

  // Text on the plates can change without restarting anything (language
  // switch, "loading…" while a replay is fetched).
  relabel(index, label, sub) {
    const plate = this.plates[index];
    if (!plate) return;
    if (label != null) plate.label = label;
    if (sub != null) plate.sub = sub;
    if (!this.raf) this.draw();
  }

  start() {
    if (this.raf) return;
    const loop = (now) => {
      const dt = this.lastTime ? (now - this.lastTime) / 1000 : 0;
      this.lastTime = now;
      this.fly.t += dt;
      this.draw();
      this.raf = frame(loop);
    };
    this.raf = frame(loop);
  }

  stop() {
    if (this.raf) { cancelAnimationFrame(this.raf); clearTimeout(this.raf); }
    this.raf = 0;
    this.lastTime = 0;
  }

  drawPlate(ctx, plate, pos, index) {
    const r = PLATE / 2;
    ctx.save();
    ctx.translate(pos.x, pos.y);
    ctx.beginPath();
    ctx.ellipse(0, r * 0.55, r + 6, r * 0.5, 0, 0, Math.PI * 2);
    ctx.fillStyle = index === this.highlight ? "rgba(181, 71, 31, 0.28)" : "rgba(0, 0, 0, 0.10)";
    ctx.fill();
    const img = plate.slug ? this.sprites.dishCache.get(plate.slug) : null;
    if (img) {
      // Dish sprites are drawn with their own plate, so only the shadow is added.
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(img, -r, -r * 0.7, r * 2, r * 2);
    } else {
      ctx.beginPath();
      ctx.ellipse(0, r * 0.45, r + 2, r * 0.42, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#f4efe7";
      ctx.strokeStyle = "#d8cfc2";
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();
      // One neutral plate for every dish without a sprite (typed, unknown dishes).
      ctx.beginPath();
      ctx.ellipse(0, r * 0.4, r * 0.62, r * 0.26, 0, 0, Math.PI * 2);
      ctx.fillStyle = "#ebe4d8";
      ctx.strokeStyle = "#cfc5b6";
      ctx.fill();
      ctx.stroke();
    }
    ctx.fillStyle = "#1f1a17";
    ctx.font = "600 13px system-ui, -apple-system, 'Segoe UI', 'PingFang SC', 'Noto Sans CJK SC', sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(plate.label, 0, r + 22);
    if (plate.sub) {
      ctx.fillStyle = "#6b625b";
      ctx.font = "12px system-ui, -apple-system, 'Segoe UI', sans-serif";
      ctx.fillText(plate.sub, 0, r + 38);
    }
    ctx.restore();
  }

  drawFly(ctx) {
    const f = this.fly;
    const frames = this.sprites.fly[FRAME_SET[f.state] || "idle"];
    ctx.save();
    ctx.translate(f.x, f.y);
    ctx.scale(f.dir, 1);
    if (frames) {
      const frame = frames[Math.floor(f.t * (f.state === "fly" ? 16 : 3)) % frames.length];
      ctx.imageSmoothingEnabled = false;
      const size = 56;
      ctx.drawImage(frame, -size / 2, -size * 0.6, size, size);
    } else {
      // Placeholder fly: body, head, wings that beat in flight, six leg strokes.
      const beat = f.state === "fly" || f.state === "hover" ? Math.sin(f.t * 40) : 0.3;
      ctx.fillStyle = "rgba(120, 130, 170, 0.45)";
      ctx.beginPath();
      ctx.ellipse(-4, -9 - 5 * beat, 13, 4.5, -0.35 * beat, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(-4, -9 + 5 * beat, 13, 4.5, 0.35 * beat, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#2a2420";
      ctx.beginPath();
      ctx.ellipse(-2, 0, 12, 6.5, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(11, -1, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#b5471f";
      ctx.beginPath();
      ctx.arc(13, -2.5, 1.8, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#2a2420";
      ctx.lineWidth = 1.2;
      for (const dx of [-7, 0, 7]) {
        ctx.beginPath();
        ctx.moveTo(dx, 4);
        ctx.lineTo(dx - 3, 11);
        ctx.stroke();
      }
      if (f.proboscis > 0) {
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#b5471f";
        ctx.beginPath();
        ctx.moveTo(13, 2);
        ctx.lineTo(15, 2 + 16 * f.proboscis);
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  draw() {
    const ctx = this.canvas.getContext("2d");
    ctx.setTransform(this.pixelRatio, 0, 0, this.pixelRatio, 0, 0);
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.plates.forEach((plate, i) => this.drawPlate(ctx, plate, this.positions[i], i));
    this.drawFly(ctx);
  }

  // ---- motion primitives (all cancellable through the token) ----

  async moveTo(x, y, token, state = "fly") {
    const f = this.fly;
    const dx = x - f.x;
    const dy = y - f.y;
    const dist = Math.hypot(dx, dy);
    const duration = Math.max(0.35, dist / FLY_SPEED_PX_S);
    if (Math.abs(dx) > 2) f.dir = dx > 0 ? 1 : -1;
    f.state = state;
    const x0 = f.x;
    const y0 = f.y;
    const start = performance.now();
    await new Promise((resolve) => {
      const step = (now) => {
        if (token.cancelled) return resolve();
        const u = Math.min(1, (now - start) / 1000 / duration);
        const ease = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
        f.x = x0 + dx * ease;
        f.y = y0 + dy * ease - Math.sin(u * Math.PI) * 26;
        if (u >= 1) return resolve();
        frame(step);
      };
      frame(step);
    });
    f.x = x;
    f.y = y;
  }

  plateLanding(i) {
    const p = this.positions[i];
    return { x: p.x, y: p.y - PLATE * 0.18 };
  }

  async visit(i, token) {
    const { x, y } = this.plateLanding(i);
    await this.moveTo(x, y - 36, token);
    await this.moveTo(x, y, token, "land");
    this.fly.state = "land";
    this.highlight = i;
    await sleep(180, token);
  }

  async hoverBetween(indices, token, ms = 1800) {
    const pts = indices.map((i) => this.plateLanding(i));
    const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
    const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length - 40;
    await this.moveTo(cx, cy, token);
    this.fly.state = "hover";
    const start = performance.now();
    await new Promise((resolve) => {
      const step = (now) => {
        if (token.cancelled || now - start > ms) return resolve();
        const u = (now - start) / 1000;
        this.fly.x = cx + Math.sin(u * 3) * Math.min(40, Math.abs(pts[0].x - cx));
        this.fly.dir = Math.cos(u * 3) >= 0 ? 1 : -1;
        frame(step);
      };
      frame(step);
    });
    this.fly.x = cx;
    this.fly.state = "hover";
  }

  async proboscis(token) {
    this.fly.state = "proboscis";
    for (const level of [0.4, 1, 0.6, 1, 0.2]) {
      this.fly.proboscis = level;
      await sleep(260, token);
    }
    this.fly.proboscis = 0;
    this.fly.state = "idle";
  }

  async turnAway(token) {
    this.fly.dir = -this.fly.dir;
    this.fly.state = "hover";
    await sleep(320, token);
  }

  // plan: { order: [plate indices to taste], winner, loser, tie: [indices], mode }
  // hooks: { onTaste(index) -> Promise, onDone() }
  async run(plan, hooks, token) {
    const f = this.fly;
    f.state = "idle";
    this.highlight = -1;
    await sleep(400, token);
    for (const i of plan.order) {
      if (token.cancelled) break;
      await this.visit(i, token);
      f.state = "taste";
      await hooks.onTaste(i, token);
      this.highlight = -1;
      if (token.cancelled) break;
    }
    if (token.cancelled) return;
    if (plan.tie && plan.tie.length > 1) {
      await this.hoverBetween(plan.tie, token);
      this.highlight = -1;
      return;
    }
    if (plan.mode === "opposite" && plan.winner != null && plan.loser != null && plan.winner !== plan.loser) {
      const w = this.plateLanding(plan.winner);
      await this.moveTo(w.x, w.y - 40, token);
      await sleep(350, token);
      await this.turnAway(token);
      await this.visit(plan.loser, token);
      await this.proboscis(token);
      return;
    }
    if (plan.winner != null) {
      await this.visit(plan.winner, token);
      await this.proboscis(token);
    }
  }
}
