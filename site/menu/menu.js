// SPDX-License-Identifier: MIT
// The menu is a read-only view of precomputed data. It does not run the model.
import {STRINGS} from '../strings.js';

const $ = id => document.getElementById(id);
const format = (value, fields = {}) => value.replace(/\{(\w+)\}/g, (_, key) => String(fields[key] ?? '{' + key + '}'));
const normalize = value => String(value).normalize('NFKC').trim().toLowerCase().replace(/\s+/g, ' ');
const queryLang = new URLSearchParams(location.search).get('lang');
let lang = queryLang === 'zh' || queryLang === 'en' ? queryLang : (() => {
  try { const saved = localStorage.getItem('askfly.lang'); if (saved === 'zh' || saved === 'en') return saved; }
  catch (_) { /* localStorage can be disabled */ }
  return /^zh/i.test(navigator.language || '') ? 'zh' : 'en';
})();
let numbers = false;
let menu, sections, release, byKey;
let sectionFilter = 'all', sortFly = 'female', search = '';
const t = () => STRINGS[lang];
const tr = (key, fields) => format(key.split('.').reduce((v, part) => v?.[part], t()), fields);
const link = (dish, fly) => '../?v=2&d=k.' + encodeURIComponent(dish.slug) + '&lang=' + lang + (fly === 'male' ? '&f=male' : '');
const name = dish => dish.display[lang];
const otherName = dish => dish.display[lang === 'zh' ? 'en' : 'zh'];
const sprite = dish => {
  const image = document.createElement('img');
  image.src = '../assets/dishes/' + encodeURIComponent(dish.sprite) + '.png';
  image.alt = '';
  image.width = 48; image.height = 48;
  image.className = 'dish-sprite';
  return image;
};
const stateIcon = (dish, fly) => {
  const state = dish[fly].state;
  const frame = {eats:3,mouth_moves:3,proboscis_only:3,no_response:1}[state];
  const image = document.createElement('img');
  image.src = '../assets/' + (fly === 'male' ? 'response_male/' : 'response/') + 'inset_' + state + '_' + frame + '.png';
  image.alt = t().stateV12[({eats:'Eats',mouth_moves:'MouthMoves',proboscis_only:'ProboscisOnly',no_response:'NoResponse'})[state] + 'Label'];
  image.title = image.alt;
  image.width = 34; image.height = 34; image.className = 'state-icon';
  return image;
};
const numeric = (dish, fly) => {
  const text = document.createElement('span');
  text.className = 'numbers';
  text.hidden = !numbers;
  text.textContent = tr('menu.numbers', {mn9:dish[fly].mn9.toFixed(1),mn11d:dish[fly].mn11d.toFixed(1)});
  return text;
};
const primaryName = dish => {
  const box = document.createElement('span');
  box.className = 'names';
  const main = document.createElement('strong'); main.textContent = name(dish); main.title = name(dish);
  const sub = document.createElement('small'); sub.textContent = otherName(dish); sub.title = otherName(dish);
  box.append(main,sub);
  return box;
};
function standardRow(dish, fly) {
  const row = document.createElement('a');
  row.className = 'menu-row';
  row.href = link(dish, fly); row.dataset.key = dish.key; row.dataset.fly = fly;
  const rank = document.createElement('span'); rank.className = 'rank'; rank.textContent = tr('menu.rank',{rank:dish[fly].rank});
  row.append(rank,sprite(dish),primaryName(dish),stateIcon(dish,fly));
  const line = document.createElement('span'); line.className = 'speech'; line.textContent = dish[fly].line[lang]; line.title = line.textContent;
  row.append(line,numeric(dish,fly));
  return row;
}
function compactTier(tier, fly, divergence = false) {
  const box = document.createElement('div'); box.className = 'tied-group';
  const title = document.createElement('div'); title.className = 'tied-title';
  // A tied tier shares a rank; a divergence tier shares a rank gap between the two flies.
  title.textContent = divergence ? tr('menu.gapTied',{diff:tier.diff,n:tier.keys.length}) : tr('menu.tied',{rank:tier.rank,n:tier.keys.length});
  if (!divergence) title.append(stateIcon(byKey.get(tier.keys[0]),fly));
  box.append(title);
  const grid = document.createElement('div'); grid.className = 'tied-grid';
  for (const key of tier.keys) {
    const dish = byKey.get(key);
    const a = document.createElement('a'); a.href = link(dish,fly); a.title = name(dish) + ' / ' + otherName(dish);
    a.append(sprite(dish));
    const label = document.createElement('span'); label.textContent = name(dish); a.append(label);
    grid.append(a);
  }
  box.append(grid);
  if (numbers && !divergence) box.append(numeric(byKey.get(tier.keys[0]),fly));
  return box;
}
function divergenceRow(dish) {
  const row = document.createElement('div'); row.className = 'menu-row divergence-row'; row.dataset.key = dish.key;
  row.append(sprite(dish),primaryName(dish));
  for (const fly of ['female','male']) {
    const a = document.createElement('a'); a.className = 'fly-detail'; a.href = link(dish,fly); a.dataset.fly = fly;
    a.append(stateIcon(dish,fly));
    const label = document.createElement('span');
    label.textContent = t().flyName[fly] + ' ' + tr('menu.rank',{rank:dish[fly].rank}) + ' · ' + dish[fly].line[lang];
    label.title = label.textContent;
    a.append(label,numeric(dish,fly)); row.append(a);
  }
  return row;
}
function sectionRow(index, fly) {
  const top = menu.lists.section_tops[index][fly];
  const dish = byKey.get(top.keys[0]);
  const row = document.createElement('a'); row.className = 'menu-row section-row'; row.href = link(dish,fly);
  const sectionName = document.createElement('b'); sectionName.textContent = sections[index][lang]; row.append(sectionName,sprite(dish),primaryName(dish));
  if (top.keys.length > 1) {
    const tied = document.createElement('span'); tied.textContent = '+' + (top.keys.length - 1);
    tied.title = top.keys.map(key => name(byKey.get(key))).join(' / ');
    row.append(tied);
  }
  row.append(numeric(dish,fly));
  return row;
}
function block(id,title) {
  const section = document.createElement('section'); section.id = id; section.className = 'menu-block';
  const head = document.createElement('header'); head.className = 'block-head';
  const attribution = document.createElement('small'); attribution.className = 'attribution';
  attribution.textContent = tr('menu.attribution',{version:release.version});
  const h = document.createElement('h2'); h.textContent = title;
  head.append(attribution,h); section.append(head);
  return section;
}
function addPaginated(id,title,elements) {
  const host = $('lists');
  let part = 1, current = block(id,title); host.append(current);
  for (const element of elements) {
    current.append(element);
    if (current.getBoundingClientRect().height > 838 && current.children.length > 2) {
      element.remove();
      part++;
      current = block(id + '-part-' + part,title);
      host.append(current);
      current.append(element); // the row that did not fit opens the next part
    }
  }
  if (part > 1) {
    // Avoid an almost empty final screenshot when the cutoff group alone spills.
    const previous = $(part === 2 ? id : id + '-part-' + (part - 1));
    while (current.getBoundingClientRect().height < 350 && previous.children.length > 2) {
      current.insertBefore(previous.lastElementChild, current.children[1]);
    }
    for (let i=1;i<=part;i++) {
      const target = $(i===1 ? id : id+'-part-'+i);
      const marker = document.createElement('span'); marker.className = 'part-marker';
      marker.textContent = tr('menu.part',{i,n:part}); target.querySelector('h2').append(' ',marker);
    }
  }
}
function renderLists() {
  $('lists').replaceChildren();
  const definitions = [
    ['female-top',tr('menu.femaleTop'),menu.lists.female_top,'female'],
    ['male-top',tr('menu.maleTop'),menu.lists.male_top,'male'],
    ['divergence',tr('menu.divergence'),menu.lists.divergence,null],
    ['not-food-female',tr('menu.notFood',{fly:t().flyName.female}),menu.lists.not_food.female,'female'],
    ['not-food-male',tr('menu.notFood',{fly:t().flyName.male}),menu.lists.not_food.male,'male'],
  ];
  for (const [id,title,tiers,fly] of definitions) {
    const entries = [];
    let preceding = 0;
    for (const tier of tiers) {
      const compact = preceding < 10 && preceding + tier.keys.length > 10;
      if (compact) entries.push(compactTier(tier,fly || 'female',!fly));
      else for (const key of tier.keys) entries.push(fly ? standardRow(byKey.get(key),fly) : divergenceRow(byKey.get(key)));
      preceding += tier.keys.length;
    }
    if (id === 'divergence') {
      // The fixed sentence on why the two flies can differ belongs wherever they are compared.
      const note = document.createElement('p'); note.className = 'menu-note'; note.textContent = t().disagreement.sentence;
      entries.unshift(note);
    }
    addPaginated(id,title,entries);
  }
  for (const fly of ['female','male']) {
    addPaginated('section-tops-'+fly,tr('menu.sectionTops')+' · '+t().flyName[fly],sections.map((_,i)=>sectionRow(i,fly)));
  }
  const nav = $('menu-contents'); nav.replaceChildren();
  for (const [id,title] of [...definitions.map(d=>d.slice(0,2)),...['female','male'].map(fly=>['section-tops-'+fly,tr('menu.sectionTops')+' · '+t().flyName[fly]]),['all',tr('menu.allTitle',{n:menu.dishes.length})]]) {
    const a = document.createElement('a'); a.href = '#'+id; a.textContent = title; nav.append(a);
  }
}
function renderTable() {
  const selected = menu.dishes.filter(dish => (sectionFilter === 'all' || dish.section === Number(sectionFilter)) &&
    (!search || normalize(dish.display.zh).includes(normalize(search)) || normalize(dish.display.en).includes(normalize(search))));
  selected.sort((a,b)=>b[sortFly].mn9-a[sortFly].mn9); // stable sort retains dictionary order for ties
  // The heading already says how many there are in all; count only a filtered view.
  $('table-count').textContent = selected.length === menu.dishes.length ? '' : tr('menu.shown',{n:selected.length});
  const fragment = document.createDocumentFragment();
  for (const dish of selected) {
    const row = document.createElement('div'); row.className = 'table-row'; row.dataset.key = dish.key;
    row.append(sprite(dish),primaryName(dish));
    if (dish.not_food) {
      const badge = document.createElement('span'); badge.className='not-food-badge';badge.textContent=t().notFood.badge;row.append(badge);
    }
    for (const fly of ['female','male']) {
      const a = document.createElement('a'); a.href=link(dish,fly); a.dataset.fly=fly;
      a.textContent=t().flyName[fly]+' '+tr('menu.rank',{rank:dish[fly].rank});
      a.append(numeric(dish,fly));row.append(a);
    }
    fragment.append(row);
  }
  if (!selected.length) {
    const empty=document.createElement('p');empty.textContent=tr('menu.empty');fragment.append(empty);
  }
  $('table-rows').replaceChildren(fragment);
}
function renderStatic() {
  document.documentElement.lang=lang==='zh'?'zh-CN':'en';
  $('lang-toggle').textContent=lang==='zh'?'EN':'中文';
  $('lang-toggle').setAttribute('aria-label',t().ariaLangToggle);
  $('back-link').textContent=tr('menu.back');
  $('page-title').textContent=tr('menu.title');
  $('numbers-toggle').textContent=tr(numbers?'menu.hideNumbers':'menu.showNumbers');
  $('menu-honesty').textContent=tr('menu.honesty');
  $('all').querySelector('.attribution').textContent=tr('menu.attribution',{version:release.version});
  $('all').querySelector('h2').textContent=tr('menu.allTitle',{n:menu.dishes.length});
  const filter=$('section-filter'),sort=$('table-sort');
  filter.replaceChildren(new Option(tr('menu.allSections'),'all'),...sections.map((section,i)=>new Option(section[lang],String(i))));
  filter.value=sectionFilter;
  sort.replaceChildren(new Option(tr('menu.sortFemale'),'female'),new Option(tr('menu.sortMale'),'male'));
  sort.value=sortFly;
  $('table-search').placeholder=tr('menu.search');
  $('menu-contents').setAttribute('aria-label',tr('menu.aria.contents'));
  $('label-section').textContent=tr('menu.aria.section');
  $('label-sort').textContent=tr('menu.aria.sort');
  $('label-search').textContent=tr('menu.search');
  renderLists();renderTable();
}
async function load() {
  const json=async path=>{const response=await fetch(path);if(!response.ok)throw new Error(path+': '+response.status);return response.json();};
  [menu,{sections},release]=await Promise.all([json('../data/menu.json'),json('../data/sections.json'),json('../data/release.json')]);
  byKey=new Map(menu.dishes.map(dish=>[dish.key,dish]));
  renderStatic();
  if (location.hash) requestAnimationFrame(()=>document.querySelector(location.hash)?.scrollIntoView());
}
$('lang-toggle').addEventListener('click',()=>{lang=lang==='zh'?'en':'zh';try{localStorage.setItem('askfly.lang',lang);}catch(_){/* optional preference */}renderStatic();});
$('numbers-toggle').addEventListener('click',()=>{numbers=!numbers;renderStatic();});
$('section-filter').addEventListener('change',event=>{sectionFilter=event.target.value;renderTable();});
$('table-sort').addEventListener('change',event=>{sortFly=event.target.value;renderTable();});
$('table-search').addEventListener('input',event=>{search=event.target.value;renderTable();});
load().catch(error=>{console.error(error);$('lists').textContent=error.message;});
