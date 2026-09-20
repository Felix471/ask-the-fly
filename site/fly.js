// SPDX-License-Identifier: MIT
// Fly scene: plates in a row (grid on narrow screens), a fly that visits each
// plate, and the winner sequence. Sprites from site/assets/ when present,
// placeholder shapes otherwise. The scene never decides anything; it animates
// the decision computed in app.js.
import { RESPONSE_SEQUENCE, EMOTIONS } from './taste_states.js';

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

export function layoutPlates(count, width, captionExtra = 0) {
  const perRow = Math.max(1, Math.min(count, Math.floor((width - 16) / (PLATE + 28))));
  const rows = Math.ceil(count / perRow);
  const positions = [];
  for (let i = 0; i < count; i += 1) {
    const row = Math.floor(i / perRow);
    const inRow = Math.min(perRow, count - row * perRow);
    const col = i - row * perRow;
    const span = inRow * (PLATE + 28) - 28;
    const x = (width - span) / 2 + col * (PLATE + 28) + PLATE / 2;
    const y = 70 + row * (ROW_HEIGHT + captionExtra) + PLATE / 2;
    positions.push({ x, y });
  }
  return { positions, height: 70 + rows * (ROW_HEIGHT + captionExtra) };
}

async function loadImage(url) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
    img.src = url;
  });
}

// Loads and returns the sprite for a dish slug, or null when it did not load.
// Successes are cached; a failure is not (the next request retries); requests
// in flight for the same slug share one load (F13). `loader` is injectable.
export async function loadDishSprite(sprites, slug, loader = loadImage) {
  if (!slug) return null;
  if (sprites.dishCache.has(slug)) return sprites.dishCache.get(slug);
  if (!sprites.pending) sprites.pending = new Map();
  if (!sprites.pending.has(slug)) {
    const promise = loader(`${sprites.base}dishes/${slug}.png`).then((img) => {
      if (img) sprites.dishCache.set(slug, img);
      return img || null;
    }).finally(() => { if (sprites.pending.get(slug) === promise) sprites.pending.delete(slug); });
    sprites.pending.set(slug, promise);
  }
  return sprites.pending.get(slug);
}

// Fly frame sets: a set keeps the frames that loaded; a set with none is null.
export async function loadSprites(base = "assets/", loader = loadImage, flyBase = base) {
  const flyPath = typeof flyBase === 'string' ? `${flyBase}fly/` : flyBase.fly;
  const responsePath = typeof flyBase === 'string' ? `${flyBase}response/` : flyBase.response;
  const fly = {};
  const frames = { idle: 2, fly: 4, land: 1, proboscis: 3 };
  await Promise.all(Object.entries(frames).map(async ([state, n]) => {
    const list = await Promise.all(Array.from({ length: n }, (_, i) => loader(`${flyPath}${state}_${i + 1}.png`)));
    const loaded = list.filter(Boolean);
    fly[state] = loaded.length ? loaded : null;
  }));
  const responses = {}, insets = {};
  await Promise.all(Object.keys(RESPONSE_SEQUENCE).map(async state => {
    const list = await Promise.all([1,2,3,4].map(i => loader(`${responsePath}${state}_${i}.png`)));
    responses[state] = list.every(Boolean) ? list : null;
    const detail = await Promise.all([1,2,3,4].map(i => loader(`${responsePath}inset_${state}_${i}.png`)));
    insets[state] = detail.every(Boolean) ? detail : null;
  }));
  return { fly, responses, insets, dishCache: new Map(), pending: new Map(), base };
}

// prep_male_sprites --promote writes this marker only after copying all 42 PNGs.
// Until approval/promotion, use the existing art without requesting absent files.
export async function loadMaleSprites(config = {}, base = 'assets/', loader = loadImage) {
  const variant = config.male_sprite_variant;
  if (variant == null) return loadSprites(base, loader);
  if (!['tip', 'tip_small', 'cool'].includes(variant)) throw new Error('Unknown male sprite variant');
  return loadSprites(base, async path => {
    const image = await loader(path);
    if (!image) throw new Error(`Promoted male sprite set incomplete: ${path}`);
    return image;
  }, {fly: `${base}fly_male/`, response: `${base}response_male/`});
}

// The pixel frames to draw for a fly state: its own set, else another pixel
// set in this order. Null only when no frame of any set loaded; that is the
// one case for the drawn fallback (F13).
const FRAME_FALLBACK = ["idle", "land", "fly", "proboscis"];
export function framesFor(fly, state) {
  if (!fly) return null;
  const own = fly[FRAME_SET[state] || "idle"];
  if (own && own.length) return own;
  for (const name of FRAME_FALLBACK) if (fly[name] && fly[name].length) return fly[name];
  return null;
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
    const frames = this.sprites ? framesFor(this.sprites.fly, "idle") : null;
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
  constructor(canvas, sprites, labelContainer) {
    this.canvas = canvas;
    this.labelContainer = labelContainer;
    this.labels = [];
    this.sprites = sprites || { fly: {}, dishCache: new Map(), base: "assets/" };
    this.plates = [];
    this.positions = [];
    this.fly = { x: 0, y: 0, dir: 1, state: "idle", frame: 0, t: 0, proboscis: 0 };
    this.pixelRatio = typeof devicePixelRatio === "number" ? Math.min(2, devicePixelRatio) : 1;
    this.raf = 0;
    this.lastTime = 0;
    this.highlight = -1;
    this.generation = 0; // bumped by setPlates() and stop(); a stale setPlates never starts the loop
  }

  async setPlates(plates) {
    this.plates = plates;
    const width = this.canvas.clientWidth || 360;
    const { positions, height } = layoutPlates(plates.length, width, plates.some(plate => plate.badge) ? 18 : 0);
    this.positions = positions;
    this.canvas.width = Math.round(width * this.pixelRatio);
    this.canvas.height = Math.round(height * this.pixelRatio);
    this.canvas.style.height = `${height}px`;
    // Names are HTML so CSS can clip them without changing the source text.
    // 112 px leaves 12 px between captions at the 124 px plate-center spacing.
    this.labels = plates.map((plate, i) => {
      const label = this.labelContainer.ownerDocument.createElement("span");
      label.className = "plate-label";
      this.renderPlateLabel(label, plate.label, plate.badge);
      label.style.left = `${positions[i].x / width * 100}%`;
      label.style.top = `${(positions[i].y + PLATE / 2 + 7) / height * 100}%`;
      label.style.width = `${112 / width * 100}%`;
      return label;
    });
    this.labelContainer.replaceChildren(...this.labels);
    this.fly.x = width / 2;
    this.fly.y = 34;
    const generation = ++this.generation;
    for (const plate of plates) await loadDishSprite(this.sprites, plate.slug);
    if (generation !== this.generation) return; // replaced or stopped while loading (F05)
    this.start();
  }

  // Text on the plates can change without restarting anything (language
  // switch, "loading…" while a replay is fetched).
  renderPlateLabel(node, label, badge) {
    node.textContent = label;
    node.title = label;
    node.classList.toggle('has-not-food', Boolean(badge));
    if (badge) {
      const name = node.ownerDocument.createElement('span');
      name.className = 'plate-name';
      name.textContent = label;
      const tag = node.ownerDocument.createElement('span');
      tag.className = 'not-food-badge';
      tag.textContent = badge;
      node.replaceChildren(name, tag);
      node.title = `${label} — ${badge}`;
    }
  }

  relabel(index, label, sub, badge) {
    const plate = this.plates[index];
    if (!plate) return;
    if (label != null) {
      plate.label = label;
    }
    if (badge != null) plate.badge = badge;
    this.renderPlateLabel(this.labels[index], plate.label, plate.badge);
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
    this.generation += 1; // invalidates a setPlates() still awaiting its sprites
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
    ctx.textAlign = "center";
    if (plate.sub) {
      ctx.fillStyle = "#6b625b";
      ctx.font = "12px system-ui, -apple-system, 'Segoe UI', sans-serif";
      ctx.fillText(plate.sub, 0, r + 38 + (plate.badge ? 18 : 0));
    }
    ctx.restore();
  }

  drawFly(ctx) {
    const f = this.fly;
    if (f.hidden) return;
    const response = f.responseState && this.sprites.responses?.[f.responseState];
    const frames = framesFor(this.sprites.fly, f.state);
    ctx.save();
    ctx.translate(f.x, f.y);
    ctx.scale(f.dir, 1);
    if (response) {
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(response[f.responseFrame || 0], -43, -37, 72, 72);
    } else if (frames) {
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
    if (this.bubble) {
      const text = this.speech ? this.speech() : '';
      this.bubble.hidden = !text || f.hidden;
      const label = this.bubble.querySelector('.bubble-text');
      if (label.textContent !== text) label.textContent = text;
      this.bubble.dataset.emotion = EMOTIONS[f.responseState] || 'deadpan';
      const width = this.canvas.clientWidth;
      const bubbleWidth = this.bubble.offsetWidth || 208;
      this.bubble.style.left = `${Math.max(8, Math.min(width - bubbleWidth - 8, f.x - bubbleWidth / 2))}px`;
      this.bubble.style.top = `${Math.max(0, f.y - (this.bubble.offsetHeight || 60) - 36)}px`;
    }
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
    f.hidden = false;
    f.responseState = null;
    this.speech = null;
    if (this.bubble) this.bubble.hidden = true;
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

  async respond(state, token, speech) {
    if (!RESPONSE_SEQUENCE[state]) return;
    const f = this.fly;
    const x = f.x, y = f.y;
    f.responseState = state;
    this.speech = speech;
    const reduced = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
    for (const [step, [index, ms]] of RESPONSE_SEQUENCE[state].entries()) {
      if (token.cancelled) break;
      f.responseFrame = reduced ? 0 : index;
      if (state === 'mouth_moves' && !reduced) f.x = x + ([0,2,2,1,0,2,2,-2][step] || 0) * f.dir;
      if (this.onResponse) this.onResponse(state, f.responseFrame);
      this.draw();
      await sleep(reduced ? 0 : ms, token);
    }
    f.x = x;
    if (state === 'no_response' && !token.cancelled) {
      this.speech = null;
      if (this.bubble) this.bubble.hidden = true;
      if (!reduced) await this.moveTo(-60, y - 40, token);
      f.hidden = true;
      this.draw();
    }
  }


  // plan: { order: [plate indices to taste], winner: the fly's own pick, tie: [indices] }
  // The fly's behaviour never depends on the mode: in "Do the opposite" it still
  // lands and extends its proboscis on its own pick; the captions say what the
  // human gets.
  // hooks: { onTaste(index) -> Promise, onLand(index) -> Promise (final landing,
  // before the proboscis; not called for ties) }
  async run(plan, hooks, token) {
    const f = this.fly;
    f.state = "idle";
    f.hidden = false;
    f.responseState = null;
    this.highlight = -1;
    await sleep(400, token);
    for (const i of plan.order) {
      if (token.cancelled) break;
      await this.visit(i, token);
      f.state = "taste";
      await hooks.onTaste(i, token);
      if (!token.cancelled && hooks.onReact) await hooks.onReact(i, token, false);
      this.highlight = -1;
      if (token.cancelled) break;
    }
    if (token.cancelled) return;
    if (plan.tie && plan.tie.length > 1) {
      await this.hoverBetween(plan.tie, token);
      this.highlight = -1;
      return;
    }
    if (plan.winner != null) {
      await this.visit(plan.winner, token);
      if (hooks.onLand && !token.cancelled) await hooks.onLand(plan.winner, token);
      if (token.cancelled) return;
      if (hooks.onReact) await hooks.onReact(plan.winner, token, true);
      else await this.proboscis(token);
    }
  }
}
