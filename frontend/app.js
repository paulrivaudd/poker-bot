// Pôle D
const USE_MOCK = false;  // true : pas besoin du back-end
const API_URL = location.port === "5000" ? "/api/analyze" : "http://localhost:5000/api/analyze";

const RANKS = "AKQJT98765432";
const SUITS = { s: "♠", h: "♥", d: "♦", c: "♣" };
const RED = new Set(["h", "d"]);

const $ = (id) => document.getElementById(id);
const pct = (x) => (100 * x).toFixed(1) + " %";
const fmt = (x) => (x >= 0 ? "+" : "") + x.toFixed(1);

// État : 2 cases main + 5 cases board
const state = { hand: [null, null], board: [null, null, null, null, null], active: { zone: "hand", i: 0 } };

const label = (c) => (c[0] === "T" ? "10" : c[0]) + SUITS[c[1]];
const colorClass = (c) => (RED.has(c[1]) ? "red" : "black");
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
      if (c) { d.classList.add("filled", colorClass(c)); d.textContent = label(c); }
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

function afterDeal() {
  state.active = nextEmpty();
  render();
  if ($("auto").checked && state.hand.every(Boolean)) runAnalysis();
}

function dealHand() {
  state.hand = [null, null];
  state.hand = drawRandom(2);
  afterDeal();
}

function dealNext() {
  compactBoard();
  const n = boardCount();
  if (n === 5) return;
  // board incomplet (1 ou 2 cartes) -> on complète jusqu'au flop
  const k = n < 3 ? 3 - n : 1;
  const cards = drawRandom(k);
  cards.forEach((c, i) => { state.board[n + i] = c; });
  if (!state.hand.every(Boolean)) {
    const missing = state.hand.filter((c) => !c).length;
    const extra = drawRandom(missing);
    state.hand = state.hand.map((c) => c || extra.shift());
  }
  afterDeal();
}

function newDeal() {
  state.hand = [null, null];
  state.board = [null, null, null, null, null];
  state.hand = drawRandom(2);
  afterDeal();
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
  $("r-pot-odds").textContent = pct(d.pot_odds);
  $("r-ev-fold").textContent = fmt(d.ev.fold);
  $("r-ev-call").textContent = fmt(d.ev.call);
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
$("deal-new").onclick = newDeal;
$("deal-hand").onclick = dealHand;
$("deal-next").onclick = dealNext;

$("reset").onclick = () => {
  state.hand = [null, null];
  state.board = [null, null, null, null, null];
  state.active = { zone: "hand", i: 0 };
  $("result").hidden = true;
  $("status").textContent = "";
  render();
};

render();
