// SPDX-License-Identifier: MIT
// One independent fly experiment and its presentation. Queries are scoped to the root.
import {BrainView, RasterView, SpikeClick, cellIdFor, rasterRows, replayStats, renderSnapshot} from './brain.js';
import {FlyScene, makeToken} from './fly.js';
import {readoutState, stateLabel, stateExplanation, speechLine, finalSpeechContext} from './taste_states.js';
import {fmt, displayName, levelsText, scenePlan, finalLanding, silenceStats, silenceStatsFrom, scoreOptions, decide} from './app.js';
import {STRINGS} from './strings.js';

export class FlyPanel {
  constructor(root, sources = {}, host = {}) {
    this.root = root;
    this.host = host;
    this.sound = new SpikeClick();
    this.session = 0;
    this.variantRequest = 0;
    this.variant = '';
    this.appliedVariant = '';
    this.scored = [];
    this.silenceUi = {expanded:false};
    this.bindSources(sources);
  }
  get lang() { return this.host.lang?.() || 'en'; }
  el(name) { return this.root.querySelector(`[data-panel="${name}"]`); }
  tr(key, values = {}) { return fmt(STRINGS[this.lang][key], values); }
  bindSources(sources) {
    for (const key of ['lookup','loadReplay','neurons','manifest','neuropils','sprites','flyKey','synapseCentroidIndexed']) {
      if (key in sources) this[key] = sources[key];
    }
  }
  mount(root = this.root) {
    this.root = root;
    if (!this.neurons || !this.sprites) return;
    this.brain = new BrainView(this.el('brain-canvas'),this.neurons,{neuropils:this.neuropils,lang:this.lang});
    this.raster = new RasterView(this.el('raster-canvas'));
    this.scene = new FlyScene(this.el('scene-canvas'),this.sprites,this.el('plate-labels'));
    this.scene.bubble = this.el('fly-bubble');
    this.scene.onResponse = (response,index) => {
      const canvas=this.el('mouth-inset'), ctx=canvas.getContext('2d');
      ctx.clearRect(0,0,canvas.width,canvas.height);
      const image=this.sprites.insets?.[response]?.[index];
      if(image) {ctx.imageSmoothingEnabled=false;ctx.drawImage(image,0,0,128,128);}
      this.el('response-detail').hidden=false;
      this.renderResponse();
    };
    this.el('speed').onchange=()=>{this.brain.speed=this.speed();};
    this.el('sound-toggle').onchange=e=>this.sound.enable(e.target.checked);
    this.el('brain-details').ontoggle=()=>{
      if(this.el('brain-details').open && this.raster.rows.length) this.raster.setRows(this.raster.rows,this.raster.duration);
    };
    this.el('skip-btn').onclick=()=>this.host.skip();
    this.renderStrings();
  }
  renderResponse() {
    const t=STRINGS[this.lang];
    if(this.responseItem) this.el('response-description').textContent=stateLabel(this.responseItem.cell,t)+' — '+stateExplanation(this.responseItem.cell,t);
    this.el('male-state-note').hidden=this.flyKey!=='male' || this.el('response-detail').hidden;
  }
  score(names, dictionary, mode, seed, selection = this.flyKey) {
    this.scored = scoreOptions(names, dictionary, this.lookup);
    this.decision = decide(this.scored, mode);
    this.decision.shareSeed = seed;
    if (selection !== 'female') this.decision.fly = selection;
    return this.decision;
  }
  showFinalResponse() {
    if (this.flyKey !== 'male' || !this.decision?.flyPick) return;
    this.responseItem = this.decision.flyPick;
    this.el('response-detail').hidden = false;
    this.renderResponse();
    const canvas = this.el('mouth-inset'), ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const image = this.sprites?.insets?.[readoutState(this.responseItem.cell)]?.[0];
    if (image) {ctx.imageSmoothingEnabled=false;ctx.drawImage(image,0,0,128,128);}
  }
  renderStrings() {
    const t=STRINGS[this.lang], male=this.flyKey==='male';
    const value = key => key.split('.').reduce((v,part)=>v?.[part],t) ?? '';
    for(const el of this.root.querySelectorAll('[data-i18n]')) el.textContent=value(el.dataset.i18n);
    for(const el of this.root.querySelectorAll('[data-i18n-aria]')) el.setAttribute('aria-label',value(el.dataset.i18nAria));
    this.el('fly-name').textContent=t.flyName[this.flyKey]+' · '+t.flySource[this.flyKey];
    this.el('fly-name').hidden=!male && this.host.selection?.()==='female';
    this.el('layout-note').hidden=!male && this.neurons?.layout!=='placeholder';
    this.el('layout-note').textContent=male?fmt(t.maleNote.brain,{n:this.synapseCentroidIndexed}):t.layoutPlaceholder;
    this.el('male-outlines-note').hidden=!male || !this.neuropils;
    this.el('male-outlines-note').textContent=male?t.maleNote.outlines:'';
    for(const key of ['anatomySource','replayHonesty','silenceTitle','silenceHonesty']) this.root.querySelector(`[data-i18n="${key}"]`).hidden=male;
    this.el('silence-controls').hidden=male;
    this.el('silence-caption').hidden=male;
    this.root.querySelector('[data-i18n="legendNamed"]').textContent=male?t.maleNote.legendNamed:t.legendNamed;
    this.root.querySelector('[data-i18n="responseDesign"]').textContent=male?t.maleNote.responseDesign:t.responseDesign;
    this.el('male-state-note').hidden=!male;
    this.el('male-state-note').textContent=male?t.maleNote.state:'';
    this.el('mn11-replay-note').textContent=male?t.maleNote.replay:(this.brain?.replay?(this.brain.replay.header.readout_rows?t.mn11ReplayNote:t.mn11VariantNote):'');
    // Male provenance must be visible even with the details closed.
    if(male) this.el('brain-details').before(this.el('mn11-replay-note'));
    else this.el('raster-canvas').after(this.el('mn11-replay-note'));
    this.brain?.setLang(this.lang);
    this.renderSilenceControls(); this.renderSceneStatus(); this.renderBrainCaption(); this.relabelPlates(); this.renderResponse();
  }
  reset() {
    this.session+=1;
    this.token?.cancel(); this.token=null;
    if(this.brain) {this.brain.stop();this.brain.setReplay(null);}
    this.scene?.stop();
    for(const key of ['responseItem','decision','sceneStatus','brainCaption','scenePlates','currentCell','currentItem','currentCellLevels']) this[key]=null;
    this.scored=[];this.variant='';this.appliedVariant='';this.variantRequest+=1;
    if(!this.root) return;
    for(const key of ['response-detail','male-state-note','fly-bubble','mn9-pill']) this.el(key).hidden=true;
    for(const key of ['brain-caption','silence-caption']) this.el(key).textContent='';
    this.el('mn9-count').textContent='0';
    this.renderSilenceControls();
  }
  skip() {
    this.token?.cancel();this.brain?.stop();
    if(this.scene) {this.scene.speech=null;this.scene.fly.hidden=true;this.scene.draw();}
    this.el('fly-bubble').hidden=true;this.el('response-detail').hidden=true;this.el('male-state-note').hidden=true;
    this.renderSilenceControls();
    if(this.scenePlates) {for(const item of this.scenePlates){item.loading=false;item.tasted=Boolean(item.cell);}this.relabelPlates();}
    if(this.decision){this.sceneStatus=this.finalSceneStatus(this.decision);this.renderSceneStatus();}
  }
  snapshot(common) {
    return {...common,session:this.session,currentCell:this.currentCell??null,variant:this.variant,
      sceneRunning:Boolean(this.scene?.raf),brainPlaying:Boolean(this.brain?.raf),
      responseState:this.scene?.fly.responseState??null,flyHidden:Boolean(this.scene?.fly.hidden),rasterKeys:this.raster?.rows.map(r=>r.key)||[]};
  }
  renderBrainCaption() {
    const c = this.brainCaption;
    if (!c) return;
    const cell = levelsText(c.cell, this.lang) + (c.variant ? ` (${c.variant})` : "");
    this.el("brain-caption").textContent = this.tr("brainCaption", { cell, n: c.n });
  }

  renderSceneStatus() {
    const st = this.sceneStatus;
    if (!st) return;
    const values = {};
    for (const k of ["dish", "fly", "pick", "fly_pick", "human_pick"]) if (st[k]) values[k] = displayName(st[k], this.lang);
    this.el("scene-status").textContent = this.statusText(st.key, values);
  }

  statusText(key, values = {}) {
    const t = STRINGS[this.lang];
    const template = this.host.selection?.() === 'both' ? t.panelStatus[key] : t[key];
    return fmt(template, {...values, fly:t.flyName[this.flyKey]});
  }

  verdictText(key, values = {}) {
    const t = STRINGS[this.lang];
    const template = this.host.selection?.() === 'both' ? t.panelVerdict[key] : t[key];
    return fmt(template, {...values, fly:t.flyName[this.flyKey]});
  }

  plateSub(item) {
    if (!item.cell) return STRINGS[this.lang].plateUnknown;
    if (item.loading) return STRINGS[this.lang].plateLoading;
    if (item.tasted) return this.tr("hzValue", { hz: item.cell.mn9_mean.toFixed(1) });
    return "";
  }

  relabelPlates() {
    if (!this.scene || !this.scenePlates) return;
    this.scenePlates.forEach((item, i) => this.scene.relabel(i, displayName(item, this.lang), this.plateSub(item)));
  }

  rasterLabels() {
    const t = STRINGS[this.lang];
    return { sugar: t.rasterSugar, bitter: t.rasterBitter, water: t.rasterWater, mn9_left: t.rasterMn9L, mn9_right: t.rasterMn9R };
  }

  showReplayDetails(replay) {
    if (!this.raster) return;
    this.raster.setRows(rasterRows(replay, this.brain.neurons, this.rasterLabels()), replay.header.duration_ms);
    this.raster.draw(0);
    const st = replayStats(replay);
    const t = STRINGS[this.lang];
    this.el('mn11-replay-note').textContent = this.flyKey === 'male' ? t.maleNote.replay : (replay.header.readout_rows ? t.mn11ReplayNote : t.mn11VariantNote);
    this.el("hud-total").textContent = st.totalNeurons != null ? st.totalNeurons.toLocaleString() : "–";
    this.el("hud-active").textContent = st.activeNeurons.toLocaleString();
    this.el("hud-mn9").textContent = `${st.mn9Left} / ${st.mn9Right}`;
    this.el("hud-cell").textContent = replay.header.cell_id || this.currentCell || "–";
    this.el("hud-latency").textContent = st.mn9FirstMs == null ? t.hudNone : fmt(t.hudMs, { ms: st.mn9FirstMs });
    this.el("hud-inputs").textContent = fmt(t.hudRates, { sugar: st.hz.sugar, bitter: st.hz.bitter, water: st.hz.water, ir94e: st.hz.ir94e });
  }

  silenceRanking() {
    const stats = this.manifest.variant_stats || {};
    const rows = (this.manifest.named_neurons || [])
      .filter((entry) => this.manifest.variants.includes(`silence_${entry.key}`))
      .map((entry) => {
        const st = stats[`silence_${entry.key}`] || {};
        const consistency = Math.max(st.frac_down || 0, st.frac_up || 0);
        return { ...entry, stats: st, score: Math.abs(st.median_delta || 0) * consistency };
      });
    const clavicle = rows.filter((r) => r.key === "clavicle");
    const others = rows.filter((r) => r.key !== "clavicle").sort((a, b) => b.score - a.score);
    return { primary: [...clavicle, ...others.slice(0, 2)], more: others.slice(2) };
  }

  sequenceRunning() {
    return Boolean(this.token && !this.token.cancelled);
  }

  renderSilenceControls() {
    const box = this.el("silence-controls");
    if (!box || !this.manifest || this.flyKey === 'male') return;
    const t = STRINGS[this.lang];
    const locked = this.sequenceRunning();
    box.innerHTML = "";
    box.setAttribute("aria-busy", locked ? "true" : "false");
    // The button factory only builds the element; each button gets exactly one
    // handler, passed in explicitly (F02).
    const button = (label, onClick) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "btn btn-secondary btn-small";
      b.textContent = label;
      b.disabled = locked;
      b.addEventListener("click", onClick);
      return b;
    };
    const variantButton = (label, variant) => {
      const b = button(label, () => this.playVariant(variant));
      b.setAttribute("aria-pressed", this.variant === variant ? "true" : "false");
      return b;
    };
    const { primary, more } = this.silenceRanking();
    box.append(variantButton(t.silenceBaseline, ""));
    for (const entry of primary) box.append(variantButton(fmt(t.silenceButton, { name: entry.label }), entry.key));
    if (more.length) {
      // Expander: changes only the list, never the experiment condition.
      const toggle = button(this.silenceUi.expanded ? t.silenceLess : t.silenceMore, () => {
        this.silenceUi.expanded = !this.silenceUi.expanded;
        this.renderSilenceControls();
      });
      toggle.setAttribute("aria-expanded", this.silenceUi.expanded ? "true" : "false");
      if (box.id) toggle.setAttribute("aria-controls", box.id);
      box.append(toggle);
      if (this.silenceUi.expanded) for (const entry of more) box.append(variantButton(fmt(t.silenceButton, { name: entry.label }), entry.key));
    }
    const summary = document.createElement("div");
    summary.className = "silence-summary";
    for (const entry of [...primary, ...(this.silenceUi.expanded ? more : [])]) {
      const st = entry.stats;
      if (st.median_delta == null) continue;
      const active = silenceStats(st);
      const all = silenceStatsFrom(this.manifest, `silence_${entry.key}`, "all");
      const line = document.createElement("div");
      line.textContent = fmt(t.silenceEffectSummary, { name: entry.label, ...active, nAll: all.n, medianAll: all.median });
      summary.append(line);
    }
    box.append(summary);
    for (const entry of this.manifest.unmatched || []) {
      const span = document.createElement("span");
      span.className = "unavailable";
      span.textContent = fmt(t.silenceUnavailable, { name: entry.label });
      box.append(span);
    }
  }

  async playVariant(variant) {
    if (!this.currentCell || !this.brain) return;
    // Identity of this request: only the latest request of the current session
    // for the cell that is still current may touch the UI (F03).
    const request = { id: ++this.variantRequest, session: this.session, cell: this.currentCell, levels: this.currentCellLevels };
    const current = () => request.id === this.variantRequest && request.session === this.session && this.currentCell === request.cell;
    this.variant = variant;
    this.renderSilenceControls();
    const t = STRINGS[this.lang];
    let replay;
    try {
      replay = await this.loadReplay(request.cell, variant);
    } catch (error) {
      console.warn("variant load failed:", error);
      if (!current()) return;
      this.variant = this.appliedVariant; // the buttons go back to what is actually shown
      this.renderSilenceControls();
      this.el("silence-caption").textContent = t.stateReplayFailed;
      return;
    }
    if (!current()) return;
    this.appliedVariant = variant;
    const cellInfo = this.manifest.cells[request.cell];
    if (variant) {
      const before = cellInfo.mn9_left_count;
      const after = replay.header.mn9_left_count;
      const delta = after - before;
      const name = (this.manifest.named_neurons.find((n) => n.key === variant) || {}).label || variant;
      const st = (this.manifest.variant_stats || {})[`silence_${variant}`] || {};
      // Only what was measured: this cell's counts, then the median and the
      // up/down/unchanged shares over the cells where the baseline MN9 fired.
      this.el("silence-caption").textContent = fmt(t.silenceCaption, { name, after, before, delta: (delta >= 0 ? "+" : "") + delta, ...silenceStats(st) });
    } else {
      this.el("silence-caption").textContent = "";
    }
    this.brainCaption = { cell: request.levels, variant: variant ? replay.header.variant : "", n: replay.header.n_spikes };
    this.renderBrainCaption();
    this.el("mn9-count").textContent = "0";
    this.brain.onMn9 = (count) => { this.el("mn9-count").textContent = String(count); this.sound.click(); };
    this.brain.onTime = (ms) => { if (this.raster && !this.el("brain-details").hidden) this.raster.draw(ms); };
    this.brain.setReplay(replay);
    this.showReplayDetails(replay);
    await this.brain.play(this.speed());
  }

  speed() {
    return Number(this.el("speed").value) || 1;
  }

  async runScene(decision, session) {
    if (this.token) this.token.cancel();
    const token = makeToken();
    this.token = token;
    this.renderSilenceControls(); // the sequence now owns the player: manual experiments disabled (F04)
    // Live while this session is current and the sequence has not been skipped.
    const live = () => this.session === session && !token.cancelled;
    const scored = [...decision.known, ...decision.misses];
    for (const item of scored) { item.loading = false; item.tasted = false; }
    this.scenePlates = scored;
    const plates = scored.map((item) => ({
      key: item.entry ? item.entry.key : item.name,
      label: displayName(item, this.lang),
      sub: this.plateSub(item),
      slug: this.host.spriteSlug(item),
    }));
    // Replays are fetched up front so the fly rarely waits at a plate.
    for (const item of decision.known) this.loadReplay(cellIdFor(item.cell)).catch(error => console.warn("replay prefetch failed:", error));
    const plan = scenePlan(decision, scored);
    this.sceneStatus = { key: "sceneIdle" };
    this.renderSceneStatus();
    this.brainCaption = null;
    this.el("brain-caption").textContent = "";
    this.el("mn9-count").textContent = "0";
    this.el("mn9-pill").hidden = true;
    this.el("hud-idle").hidden = false;
    this.brain.resize();
    await this.scene.setPlates(plates);
    if (!live()) return;
    window.scrollTo({ top: 0, behavior: this.host.scrollBehavior });

    const hooks = {
      onReact: async (index, reactionToken, final) => {
        if (!live()) return;
        const item = scored[index], response = readoutState(item.cell);
        if (!response) return;
        this.responseItem = item;
        const context = final ? finalSpeechContext(decision) : response;
        await this.scene.respond(response, reactionToken, context ? () => speechLine(context, item.cell, decision.shareSeed, this.lang) : null);
      },
      onTaste: async (index) => {
        const item = scored[index];
        if (!item.cell || !live()) return;
        this.sceneStatus = { key: "sceneTasting", dish: item };
        this.renderSceneStatus();
        this.brain.setReplay(null); // blank brain while the replay is fetched
        this.el("mn9-count").textContent = "0";
        const cellId = cellIdFor(item.cell);
        item.loading = true;
        this.scene.relabel(index, null, this.plateSub(item));
        let replay;
        try {
          replay = await this.loadReplay(cellId);
        } catch (error) {
          console.warn("replay load failed:", error);
          if (this.session !== session) return; // reset while loading: nothing to show
          item.loading = false;
          this.scene.relabel(index, null, this.plateSub(item));
          this.el("brain-caption").textContent = navigator.onLine === false ? this.tr("stateOffline") : this.tr("stateReplayFailed");
          this.host.notice(navigator.onLine === false ? "stateOffline" : "stateReplayFailed");
          return;
        }
        if (this.session !== session) return; // reset while loading (F05)
        item.loading = false;
        item.tasted = true;
        this.scene.relabel(index, null, this.plateSub(item));
        if (token.cancelled) return; // skipped: the result view shows the numbers
        await present(item, cellId, replay);
      },
      // Final landing: the brain switches to the run of the plate the fly lands
      // on (its own pick), unless that run is already showing because the pick
      // was the last plate tasted; then nothing restarts.
      onLand: async (index) => {
        if (!live()) return;
        const landing = finalLanding(plan, scored, this.currentCell);
        if (!landing || landing.index !== index) return;
        const item = scored[index];
        // The stage caption names the plate the fly is on ("Trying {dish}…",
        // the tasting string); untouched when no landing replay plays.
        this.sceneStatus = { key: "sceneTasting", dish: item };
        this.renderSceneStatus();
        let replay;
        try {
          replay = await this.loadReplay(landing.cellId);
        } catch (error) {
          console.warn("replay load failed:", error);
          if (live() && this.flyKey === 'male') this.host.notice("stateReplayFailed");
          return; // the last tasted run stays on screen
        }
        if (!live()) return;
        await present(item, landing.cellId, replay);
      },
    };

    // Show one recorded run: caption, HUD, raster, silencing state, then play it.
    const present = async (item, cellId, replay) => {
      this.currentCellLevels = item.cell;
      this.brainCaption = { cell: item.cell, variant: "", n: replay.header.n_spikes };
      this.renderBrainCaption();
      this.el("mn9-count").textContent = "0";
      this.el("mn9-pill").hidden = false;
      this.el("hud-idle").hidden = true;
      this.currentCell = cellId;
      this.currentItem = item;
      this.variant = "";
      this.appliedVariant = "";
      this.variantRequest += 1; // pending silencing requests for the previous dish are stale
      this.el("silence-caption").textContent = "";
      this.renderSilenceControls();
      this.brain.onMn9 = (count) => { this.el("mn9-count").textContent = String(count); this.sound.click(); };
      this.brain.onTime = (ms) => { if (this.raster) this.raster.draw(ms); };
      this.brain.setReplay(replay);
      this.showReplayDetails(replay);
      const stopOnCancel = () => this.brain.stop();
      token.onCancel.push(stopOnCancel);
      await this.brain.play(this.speed());
    };
    await this.scene.run(plan, hooks, token);
    if (this.session !== session || this.token !== token) return;
    if (decision.flyTies.length > 1) this.scene.speech = () => speechLine('tie', decision.flyPick.cell, decision.shareSeed, this.lang);
    token.cancel(); // the sequence is over: the player is free for manual experiments
    this.renderSilenceControls();
    for (const item of decision.known) item.tasted = true; // skipped plates still show their Hz
    this.relabelPlates();
    this.sceneStatus = this.finalSceneStatus(decision);
    this.renderSceneStatus();
  }

  finalSceneStatus(decision) {
    if (!decision.flyPick) return { key: "sceneNone" };
    if (decision.tie.length) return { key: "sceneTie" };
    if (readoutState(decision.flyPick.cell) === 'no_response') return { key: 'sceneNoResponse' };
    if (decision.mode === "opposite" && decision.many) return { key: "sceneOppositeMany", fly_pick: decision.flyPick };
    if (decision.mode === "opposite") return { key: "sceneOpposite", fly_pick: decision.flyPick, human_pick: decision.winner };
    return { key: "sceneWinner", pick: decision.winner };
  }

  async snapshotFor(decision) {
    if (!this.brain || !decision.flyPick) return null;
    const session = this.session;
    const candidates = decision.mode === "opposite" ? [decision.flyPick] : (decision.tie.length ? decision.tie : [decision.winner]);
    const loaded = await Promise.all(candidates.map(async (item) => {
      try { return { item, replay: await this.loadReplay(cellIdFor(item.cell)) }; }
      catch (error) {
        if (this.flyKey === 'male') {
          console.warn('male snapshot replay failed:', error);
          if (this.session === session && this.decision === decision) this.host.notice('stateReplayFailed');
        }
        return null;
      }
    }));
    const best = loaded.filter(Boolean).sort((a, b) => (b.replay.header.mn9_left_count || 0) - (a.replay.header.mn9_left_count || 0))[0];
    if (!best) return null;
    const snap = renderSnapshot(this.brain.neurons, this.brain.neuropils, best.replay, 340, 2);
    const stats = replayStats(best.replay);
    return { canvas: snap.canvas, mn9: stats.mn9Left ?? snap.count, neurons: stats.totalNeurons };
  }

}
