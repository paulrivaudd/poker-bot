// Pôle D
const USE_MOCK = false;  // true : pas besoin du back-end
const API_URL = location.port === "5000" ? "/api/analyze" : "http://localhost:5000/api/analyze";

const RANKS = "AKQJT98765432";
const SUITS = { s: "♠\uFE0E", h: "♥\uFE0E", d: "♦\uFE0E", c: "♣\uFE0E" };
const RED = new Set(["h", "d"]);

const $ = (id) => document.getElementById(id);
const pct = (x) => (100 * x).toFixed(1) + " %";
const fmt = (x) => (x >= 0 ? "+" : "") + x.toFixed(1);

// État : 2 cases main + 5 cases board
const state = { hand: [null, null], board: [null, null, null, null, null], active: { zone: "hand", i: 0 } };

const label = (c) => (c[0] === "T" ? "10" : c[0]) + SUITS[c[1]];
const colorClass = (c) => (RED.has(c[1]) ? "red" : "black");
const faceHTML = (c) => `<span class="rk">${c[0] === "T" ? "10" : c[0]}</span><span class="st">${SUITS[c[1]]}</span>`;
const used = () => new Set([...state.hand, ...state.board].filter(Boolean));

function nextEmpty() {
  const i = state.hand.indexOf(null);
  if (i >= 0) return { zone: "hand", i };
  const j = state.board.indexOf(null);
  if (j >= 0) return { zone: "board", i: j };
  return null;
}

function renderSlots() {
  for (const zone of ["hand", "board"]) {
    const el = $(zone + "-slots");
    el.innerHTML = "";
    state[zone].forEach((c, i) => {
      const d = document.createElement("div");
      d.className = "slot";
      if (c) { d.classList.add("filled", colorClass(c)); d.innerHTML = faceHTML(c); }
      if (state.active && state.active.zone === zone && state.active.i === i) d.classList.add("active");
      d.onclick = () => {
        if (c) state[zone][i] = null;
        state.active = { zone, i };
        render();
      };
      el.appendChild(d);
    });
  }
}

function renderPicker() {
  const el = $("picker");
  el.innerHTML = "";
  const u = used();
  for (const s of Object.keys(SUITS)) {
    for (const r of RANKS) {
      const c = r + s;
      const d = document.createElement("div");
      d.className = "card " + colorClass(c) + (u.has(c) ? " used" : "");
      d.textContent = label(c);
      d.onclick = () => {
        if (u.has(c)) return;
        const target = state.active || nextEmpty();
        if (!target) return;
        state[target.zone][target.i] = c;
        state.active = nextEmpty();
        render();
      };
      el.appendChild(d);
    }
  }
}

const ALL_CARDS = [...RANKS].flatMap((r) => Object.keys(SUITS).map((s) => r + s));
const STREETS = ["Flop →", "Turn →", "River →", "Board complet"];

function drawRandom(n) {
  const pool = ALL_CARDS.filter((c) => !used().has(c));
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, n);
}

function boardCount() { return state.board.filter(Boolean).length; }

function compactBoard() {
  const b = state.board.filter(Boolean);
  state.board = [...b, ...Array(5 - b.length).fill(null)];
}

function updateDealButton() {
  const n = boardCount();
  const idx = n === 0 ? 0 : n === 3 ? 1 : n === 4 ? 2 : n === 5 ? 3 : 0;
  const btn = $("deal-next");
  btn.textContent = STREETS[idx];
  btn.disabled = n === 5;
}

// ---------- Animation de distribution ----------
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let dealing = false;

function dealerEl() {
  const photo = $("dealer-photo");
  return photo && !photo.hidden ? photo : $("dealer");
}

function slotEl(zone, i) { return $(zone + "-slots").children[i]; }

// Une carte part du sabot, vole jusqu'à sa case, se retourne, puis est posée.
async function flyCard(zone, i, card) {
  const dealer = dealerEl();
  dealer.classList.add("dealing");
  await sleep(REDUCED ? 0 : 140);

  const from = $("deck").getBoundingClientRect();
  const to = slotEl(zone, i).getBoundingClientRect();
  const el = document.createElement("div");
  el.className = "flying";
  Object.assign(el.style, { left: to.left + "px", top: to.top + "px", width: to.width + "px", height: to.height + "px" });
  el.innerHTML = `<div class="inner"><div class="card-back"></div><div class="face ${colorClass(card)}">${faceHTML(card)}</div></div>`;
  document.body.appendChild(el);

  const dx = from.left + from.width / 2 - (to.left + to.width / 2);
  const dy = from.top + from.height / 2 - (to.top + to.height / 2);
  const spin = (Math.random() - 0.5) * 40;
  const flight = el.animate(
    [
      { transform: `translate(${dx}px, ${dy}px) rotate(${spin - 90}deg) scale(.8)` },
      { transform: `translate(${dx * 0.4}px, ${dy * 0.4 - 18}px) rotate(${spin / 2}deg) scale(1.05)`, offset: 0.6 },
      { transform: "translate(0, 0) rotate(0) scale(1)" },
    ],
    { duration: REDUCED ? 1 : 420, easing: "cubic-bezier(.2,.7,.3,1)", fill: "forwards" }
  );
  setTimeout(() => dealer.classList.remove("dealing"), REDUCED ? 0 : 200);
  await flight.finished;

  const inner = el.querySelector(".inner");
  await inner.animate([{ transform: "rotateY(0)" }, { transform: "rotateY(180deg)" }],
    { duration: REDUCED ? 1 : 260, easing: "ease-in-out", fill: "forwards" }).finished;

  state[zone][i] = card;
  renderSlots();
  el.remove();
}

// ---------- Adversaires ----------
const nOpp = () => Math.min(9, Math.max(1, Number($("n_opponents").value) || 1));
let oppCards = [];  // nombre de cartes (face cachée) devant chaque adversaire

// Positions sur l'ellipse : moitié à gauche, moitié à droite, espacées à distance égale
// le long du bord (sens horaire depuis le bas gauche, en laissant libres notre place et le croupier).
function arcPoints(a0, a1, count) {
  if (count === 0) return [];
  const felt = document.querySelector(".felt").getBoundingClientRect();
  const rx = felt.width / 2, ry = felt.height / 2, N = 300;
  const pts = [], cum = [0];
  for (let j = 0; j <= N; j++) {
    const r = ((a0 + ((a1 - a0) * j) / N) * Math.PI) / 180;
    pts.push([Math.cos(r), Math.sin(r)]);
    if (j) cum.push(cum[j - 1] + Math.hypot(rx * (pts[j][0] - pts[j - 1][0]), ry * (pts[j][1] - pts[j - 1][1])));
  }
  const out = [];
  for (let k = 0; k < count; k++) {
    const target = (cum[N] * (k + 0.5)) / count;
    const j = cum.findIndex((c) => c >= target);
    out.push({ left: 50 + 50 * pts[j][0], top: 50 + 50 * pts[j][1] });
  }
  return out;
}

function seatPositions(n) {
  const left = Math.ceil(n / 2);
  return [...arcPoints(120, 240, left), ...arcPoints(300, 420, n - left)];
}

function renderSeats(animate = false) {
  const n = nOpp();
  const el = $("seats");
  el.innerHTML = "";
  const pos = seatPositions(n);
  for (let k = 0; k < n; k++) {
    const p = pos[k];
    const s = document.createElement("div");
    s.className = "seat" + (animate ? " pop" : "");
    s.style.left = p.left + "%"; s.style.top = p.top + "%";
    if (animate) s.style.animationDelay = k * 70 + "ms";
    const cards = [0, 1].map((j) => `<div class="mini ${j < (oppCards[k] || 0) ? "card-back" : "empty"}"></div>`).join("");
    s.innerHTML = `<div class="who"><div class="avatar">J${k + 1}</div><div class="seat-name">Joueur ${k + 1}</div></div><div class="seat-cards">${cards}</div>`;
    el.appendChild(s);
  }
}

async function flyToSeat(k) {
  const dealer = dealerEl();
  dealer.classList.add("dealing");
  const target = $("seats").children[k].querySelectorAll(".mini")[oppCards[k] || 0];
  const from = $("deck").getBoundingClientRect();
  const to = target.getBoundingClientRect();
  const el = document.createElement("div");
  el.className = "flying";
  Object.assign(el.style, { left: to.left + "px", top: to.top + "px", width: to.width + "px", height: to.height + "px" });
  el.innerHTML = `<div class="inner"><div class="card-back"></div></div>`;
  document.body.appendChild(el);
  const dx = from.left + from.width / 2 - (to.left + to.width / 2);
  const dy = from.top + from.height / 2 - (to.top + to.height / 2);
  setTimeout(() => dealer.classList.remove("dealing"), REDUCED ? 0 : 150);
  await el.animate(
    [{ transform: `translate(${dx}px, ${dy}px) rotate(-120deg) scale(1.4)` }, { transform: "translate(0,0) rotate(0) scale(1)" }],
    { duration: REDUCED ? 1 : 300, easing: "cubic-bezier(.2,.7,.3,1)", fill: "forwards" }
  ).finished;
  oppCards[k] = (oppCards[k] || 0) + 1;
  target.className = "mini card-back";
  el.remove();
}

function setDealButtons(disabled) {
  for (const id of ["deal-new", "deal-hand", "deal-next", "reset", "open-setup"]) $(id).disabled = disabled;
  if (!disabled) updateDealButton();
}

// targets : [{zone, i}] dans l'ordre de distribution
async function animateDeal(targets) {
  if (dealing) return;
  dealing = true;
  setDealButtons(true);
  const cards = drawRandom(targets.filter((t) => t.seat === undefined).length);
  state.active = null;
  renderSlots();
  try {
    let c = 0;
    for (const t of targets) {
      if (t.seat !== undefined) { await flyToSeat(t.seat); if (!REDUCED) await sleep(30); continue; }
      await flyCard(t.zone, t.i, cards[c++]);
      if (!REDUCED) await sleep(90);
    }
  } finally {
    dealing = false;
    setDealButtons(false);
    afterDeal();
  }
}

function afterDeal() {
  state.active = nextEmpty();
  render();
  if ($("auto").checked && state.hand.every(Boolean)) runAnalysis();
}

function dealHand() {
  state.hand = [null, null];
  animateDeal([{ zone: "hand", i: 0 }, { zone: "hand", i: 1 }]);
}

function dealNext() {
  compactBoard();
  const n = boardCount();
  if (n === 5) return;
  const targets = [];
  state.hand.forEach((c, i) => { if (!c) targets.push({ zone: "hand", i }); });
  // board incomplet (1 ou 2 cartes) -> on complète jusqu'au flop
  const k = n < 3 ? 3 - n : 1;
  for (let j = 0; j < k; j++) targets.push({ zone: "board", i: n + j });
  render();
  animateDeal(targets);
}

function newDeal() {
  state.hand = [null, null];
  state.board = [null, null, null, null, null];
  $("result").hidden = true;
  oppCards = [];
  renderSeats();
  render();
  const targets = [];
  for (let round = 0; round < 2; round++) {
    for (let k = 0; k < nOpp(); k++) targets.push({ seat: k });
    targets.push({ zone: "hand", i: round });
  }
  animateDeal(targets);
}

function render() { renderSlots(); renderPicker(); updateDealButton(); }

async function callApi(payload) {
  if (USE_MOCK) return (await fetch("mock/analyze.json")).json();
  const r = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || "Erreur serveur");
  return data;
}

function renderResult(d) {
  const reco = $("r-reco");
  reco.textContent = d.recommendation.toUpperCase();
  reco.className = "reco " + d.recommendation;
  $("r-hand-name").textContent = d.hand_name ? "Main actuelle : " + d.hand_name : "Préflop";

  $("bar-win").style.width = pct(d.win).replace(" ", "");
  $("bar-tie").style.width = pct(d.tie).replace(" ", "");
  $("bar-lose").style.width = pct(d.lose).replace(" ", "");
  $("r-win").textContent = pct(d.win);
  $("r-tie").textContent = pct(d.tie);
  $("r-lose").textContent = pct(d.lose);

  $("r-equity").textContent = pct(d.equity);
  $("r-ci").textContent = "± " + pct(d.equity_ci);
  $("r-pot-odds").textContent = pct(d.pot_odds);

  const passive = "check" in d.ev ? "check" : "call";
  $("r-ev-fold").textContent = fmt(d.ev.fold);
  $("r-ev-passive-label").textContent = "EV " + passive;
  $("r-ev-passive").textContent = fmt(d.ev[passive]);
  $("r-ev-raise-label").textContent = "EV raise " + d.raise_size.toFixed(0);
  $("r-ev-raise").textContent = fmt(d.ev.raise);

  const cells = { fold: "r-ev-fold", call: "r-ev-passive", check: "r-ev-passive", raise: "r-ev-raise" };
  for (const id of ["r-ev-fold", "r-ev-passive", "r-ev-raise"]) $(id).parentElement.classList.remove("best");
  $(cells[d.recommendation]).parentElement.classList.add("best");
  $("result").hidden = false;
}

async function runAnalysis() {
  const status = $("status");
  const btn = $("analyze");
  status.className = "";
  const hand = state.hand.filter(Boolean);
  const board = state.board.filter(Boolean);
  if (hand.length !== 2) { status.className = "error"; status.textContent = "Choisis 2 cartes pour ta main."; return; }
  if (![0, 3, 4, 5].includes(board.length)) {
    status.className = "error"; status.textContent = "Le board doit avoir 0, 3, 4 ou 5 cartes."; return;
  }

  status.textContent = "Simulation en cours…";
  btn.disabled = true;
  try {
    const d = await callApi({
      hand, board,
      n_opponents: Number($("n_opponents").value),
      pot: Number($("pot").value),
      to_call: Number($("to_call").value),
      n_sims: Number($("n_sims").value),
      raise_size: $("raise_size").value === "" ? null : Number($("raise_size").value),
      fold_equity: Number($("fold_equity").value) / 100,
    });
    status.textContent = "";
    renderResult(d);
  } catch (err) {
    status.className = "error";
    status.textContent = err.message === "Failed to fetch"
      ? "Back-end injoignable : lance `python app.py` dans backend/."
      : err.message;
  } finally {
    btn.disabled = false;
  }
}

$("analyze").onclick = runAnalysis;
$("fold_equity").oninput = () => { $("fe-val").textContent = $("fold_equity").value + " %"; };
$("deal-new").onclick = newDeal;
$("deal-hand").onclick = dealHand;
$("deal-next").onclick = dealNext;

$("reset").onclick = () => {
  state.hand = [null, null];
  state.board = [null, null, null, null, null];
  state.active = { zone: "hand", i: 0 };
  $("result").hidden = true;
  $("status").textContent = "";
  oppCards = [];
  renderSeats();
  render();
};

// ---------- Écran de départ ----------
function openSetup() {
  const grid = $("setup-grid");
  grid.innerHTML = "";
  for (let n = 1; n <= 9; n++) {
    const b = document.createElement("button");
    b.innerHTML = `${n}<small>${n === 1 ? "heads-up" : n + 1 + " joueurs"}</small>`;
    b.onclick = () => {
      $("n_opponents").value = n;
      $("setup").hidden = true;
      oppCards = [];
      renderSeats(true);
      setTimeout(newDeal, REDUCED ? 0 : 450);
    };
    grid.appendChild(b);
  }
  $("setup").hidden = false;
}

$("open-setup").onclick = openSetup;
window.addEventListener("resize", () => { if (!dealing) renderSeats(); });
$("n_opponents").oninput = () => {
  const n = nOpp();
  oppCards = oppCards.slice(0, n).concat(Array(Math.max(0, n - oppCards.length)).fill(state.hand.every(Boolean) ? 2 : 0));
  renderSeats(true);
};

renderSeats();
render();
openSetup();
