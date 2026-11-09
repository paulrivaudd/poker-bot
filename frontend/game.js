// Mode JEU : vraie partie contre l'ordinateur ou entre amis sur le même ordi.
// Toute la logique (enchères, pots, showdown, bots) est côté serveur : /api/game/*.
// Ce fichier ne fait qu'afficher l'état et animer les changements.

const GAME_API = location.port === "5000" ? "/api/game" : "http://localhost:5000/api/game";

const G = {
  id: null,
  mode: null,      // "solo" | "local"
  s: null,         // dernier état reçu
  viewer: null,    // joueur dont on montre les cartes en bas
  me: null,        // solo : index du joueur humain (toujours en bas)
  busy: false,
  bubbles: {},     // index joueur -> texte de la dernière action
};

const isGame = () => document.body.dataset.mode === "game";

async function gApi(path, body) {
  const q = G.viewer != null ? `?viewer=${G.viewer}` : "";
  const r = await fetch(GAME_API + path + q, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || "Erreur serveur");
  return d;
}

function gStatus(msg, error = false) {
  $("g-status").textContent = msg || "";
  $("g-status").className = error ? "error" : "";
}

// ---------------------------------------------------------------- affichage
// Joueurs autour de la table : tous sauf celui du bas (solo), ou tous (local).
function seatIndexes() {
  const all = G.s.players.map((_, i) => i);
  if (G.mode === "solo") {
    const n = all.length;
    return all.slice(G.me + 1).concat(all.slice(0, G.me)).slice(0, n - 1);
  }
  return all;
}

function seatEl(playerIdx) { return $("seats").querySelector(`[data-p="${playerIdx}"]`); }

function renderGameSeats() {
  const s = G.s;
  const idx = seatIndexes();
  const pos = seatPositions(idx.length);
  const el = $("seats");
  el.innerHTML = "";
  idx.forEach((pi, k) => {
    const p = s.players[pi];
    const seat = document.createElement("div");
    seat.className = "seat game-seat";
    seat.dataset.p = pi;
    if (pi === s.current) seat.classList.add("turn");
    if (p.folded || p.out) seat.classList.add("folded");
    seat.style.left = pos[k].left + "%";
    seat.style.top = pos[k].top + "%";
    let cards = "";
    const shownBelow = G.mode === "local" && pi === G.viewer && !s.hand_over;
    if (p.hole && !shownBelow) cards = p.hole.map((c) => `<div class="mini face ${colorClass(c)}">${faceHTML(c)}</div>`).join("");
    else cards = [0, 1].map((j) => `<div class="mini ${j < p.n_cards ? "card-back" : "empty"}"></div>`).join("");
    const initials = p.bot ? "🤖" : p.name.slice(0, 2).toUpperCase();
    seat.innerHTML = `
      <div class="who">
        <div class="avatar">${initials}${pi === s.button ? '<span class="dbtn">D</span>' : ""}</div>
        <div class="seat-name">${p.name}</div>
        <div class="seat-stack">${p.out ? "éliminé" : p.stack + (p.all_in ? " · tapis" : "")}</div>
      </div>
      <div class="seat-cards">${cards}</div>
      ${p.bet ? `<div class="bet-chip">${p.bet}</div>` : ""}
      ${G.bubbles[pi] ? `<div class="bubble">${G.bubbles[pi]}</div>` : ""}`;
    el.appendChild(seat);
  });
}

function bottomPlayer() {
  if (G.mode === "solo") return G.me;
  return G.viewer;
}

function renderGame() {
  const s = G.s;
  if (!s) return;
  const b = bottomPlayer();
  const bp = b != null ? s.players[b] : null;

  // les cases du bas et du board réutilisent l'affichage du mode TRICHE
  state.hand = bp && bp.hole && !bp.folded ? [...bp.hole] : [null, null];
  state.board = [...s.board, ...Array(5 - s.board.length).fill(null)];
  state.active = null;
  renderSlots();

  $("hand-label").textContent = bp ? (G.mode === "local" ? "Main de " + bp.name : bp.name) : "En attente…";
  $("me-info").innerHTML = bp
    ? `<span>${bp.stack} jetons</span>${bp.bet ? `<span class="bet-chip inline">${bp.bet}</span>` : ""}`
      + (b === s.button ? '<span class="dbtn">D</span>' : "") + (bp.folded ? " · couché" : "")
    : "";
  $("hand-slots").classList.toggle("turn", b != null && b === s.current);
  $("pot-display").textContent = s.pot ? `Pot : ${s.pot}` : "";

  renderGameSeats();
  renderActions();
  $("g-log").innerHTML = s.log.slice().reverse().map((l) => `<li>${l}</li>`).join("");

  const banner = $("banner");
  if (s.hand_over && s.results.length) {
    banner.hidden = false;
    banner.innerHTML = s.results.filter((r) => r.amount > 0)
      .map((r) => `🏆 <b>${r.name}</b> remporte ${r.amount}${r.hand_name ? " — " + r.hand_name : ""}`).join("<br>");
  } else banner.hidden = true;
  $("g-next").hidden = !s.hand_over || s.game_over;
}

function humanTurn() {
  const s = G.s;
  return s && !s.hand_over && s.current != null && !s.players[s.current].bot && G.viewer === s.current;
}

function renderActions() {
  const s = G.s;
  const box = $("g-actions");
  const on = humanTurn() && !G.busy;
  box.classList.toggle("disabled", !on);
  $("g-advice-btn").disabled = !on;
  if (!on || !s.legal) return;
  const L = s.legal;
  const me = s.players[s.current];

  $("g-fold").hidden = !L.fold;
  $("g-call").textContent = L.check ? "Checker" : `Suivre ${L.call_amount}` + (L.call_amount >= me.stack ? " (tapis)" : "");

  const R = L.raise;
  $("g-raise").hidden = !R;
  if (R) {
    const range = $("g-raise-range"), num = $("g-raise-amount");
    range.min = num.min = R.min; range.max = num.max = R.max;
    range.step = Math.max(1, s.bb / 2);
    if (!(Number(num.value) >= R.min && Number(num.value) <= R.max)) num.value = range.value = R.min;
    updateRaiseLabel();
  }
}

function updateRaiseLabel() {
  const s = G.s, R = s.legal && s.legal.raise;
  if (!R) return;
  const v = Number($("g-raise-amount").value);
  const verb = s.current_bet === 0 ? "Miser" : "Relancer à";
  $("g-raise-btn").textContent = v >= R.max ? `Tapis (${R.max})` : `${verb} ${v}`;
}

// ---------------------------------------------------------------- animations
function newLogLines(prev, next) {
  if (!prev || prev.hand_no !== next.hand_no) return next.log;
  const last = prev.log[prev.log.length - 1];
  const k = next.log.lastIndexOf(last);
  return k >= 0 ? next.log.slice(k + 1) : next.log;
}

async function flyBackTo(target) {
  const dealer = dealerEl();
  dealer.classList.add("dealing");
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
    [{ transform: `translate(${dx}px, ${dy}px) rotate(-120deg)` }, { transform: "none" }],
    { duration: REDUCED ? 1 : 260, easing: "cubic-bezier(.2,.7,.3,1)", fill: "forwards" }
  ).finished;
  target.classList.remove("empty");
  target.classList.add("card-back");
  el.remove();
}

// Distribution d'une nouvelle main : deux tours, face cachée (les cartes du bas se retournent).
async function animateNewHand() {
  const s = G.s;
  const holes = s.players.map((p) => p.n_cards);
  // on affiche la table sans cartes, puis on distribue
  const saved = s.players.map((p) => ({ hole: p.hole, n: p.n_cards }));
  s.players.forEach((p) => { p.hole = null; p.n_cards = 0; });
  renderGame();
  const b = bottomPlayer();
  const order = [];
  for (let k = 1; k <= s.players.length; k++) order.push((s.button + k) % s.players.length);
  for (let round = 0; round < 2; round++) {
    for (const pi of order) {
      if (!holes[pi]) continue;
      if (pi === b && saved[pi].hole) {
        await flyCard("hand", round, saved[pi].hole[round]);
      } else if (pi === b) {
        await flyBackTo($("hand-slots").children[round]);
      } else {
        const seat = seatEl(pi);
        if (seat) await flyBackTo(seat.querySelectorAll(".mini")[round]);
      }
      if (!REDUCED) await sleep(25);
    }
  }
  s.players.forEach((p, i) => { p.hole = saved[i].hole; p.n_cards = saved[i].n; });
  renderGame();
}

// Applique un nouvel état : bulle d'action, cartes du board qui arrivent, rendu.
async function applyState(next) {
  const prev = G.s;
  const actor = prev ? prev.current : null;
  const lines = newLogLines(prev, next);
  G.bubbles = {};
  if (actor != null && lines.length && prev.hand_no === next.hand_no) {
    const name = prev.players[actor].name;
    const first = lines[0].startsWith(name) ? lines[0].slice(name.length).trim() : null;
    if (first) G.bubbles[actor] = first;
  }

  const sameHand = prev && prev.hand_no === next.hand_no;
  const newBoard = sameHand ? next.board.slice(prev.board.length) : [];
  G.s = next;
  if (newBoard.length) {
    // on garde l'ancien board à l'écran puis on fait voler les nouvelles cartes
    G.s = { ...next, board: prev.board };
    renderGame();
    await sleep(REDUCED ? 0 : 350);
    for (let k = 0; k < newBoard.length; k++) {
      await flyCard("board", prev.board.length + k, newBoard[k]);
      G.s.board = next.board.slice(0, prev.board.length + k + 1);
    }
    G.s = next;
  }
  renderGame();
}

// ---------------------------------------------------------------- boucle de jeu
async function gameLoop() {
  if (G.busy) return;
  G.busy = true;
  try {
    while (isGame() && G.s) {
      const s = G.s;
      if (s.hand_over) {
        const humansLeft = s.players.filter((p) => !p.bot && p.stack > 0).length;
        if (s.game_over || humansLeft === 0) showGameOver();
        break;
      }
      const cur = s.players[s.current];
      if (cur.bot) {
        renderGame();
        await sleep(REDUCED ? 0 : 650 + Math.random() * 500);
        await applyState(await gApi(`/${G.id}/bot`, {}));
        continue;
      }
      // humain
      if (G.mode === "local" && G.viewer !== s.current) {
        G.viewer = null;
        renderGame();
        await handoff(cur.name);
        G.viewer = s.current;
        G.s = await gApi(`/${G.id}`);
        // révélation : les cartes du joueur arrivent face cachée puis se retournent
        const me = G.s.players[G.viewer];
        const hole = me.hole;
        me.hole = null;
        renderGame();
        for (let i = 0; i < 2; i++) await flyCard("hand", i, hole[i]);
        me.hole = hole;
      }
      break; // on attend le clic du joueur
    }
  } catch (e) {
    gStatus(e.message === "Failed to fetch" ? "Back-end injoignable : lance `python app.py` dans backend/." : e.message, true);
  } finally {
    G.busy = false;
    renderGame();
  }
}

function handoff(name) {
  return new Promise((resolve) => {
    $("handoff-title").textContent = `Au tour de ${name}`;
    $("handoff").hidden = false;
    $("handoff-btn").onclick = () => { $("handoff").hidden = true; resolve(); };
  });
}

async function humanAct(action, amount) {
  if (!humanTurn() || G.busy) return;
  G.busy = true;
  $("g-advice").textContent = "";
  gStatus("");
  try {
    const next = await gApi(`/${G.id}/action`, { action, amount });
    await applyState(next);
    if (G.mode === "local" && !next.hand_over) { G.viewer = null; G.s = await gApi(`/${G.id}`); }
  } catch (e) {
    gStatus(e.message, true);
  } finally {
    G.busy = false;
  }
  renderGame();
  gameLoop();
}

async function nextHand() {
  if (G.busy) return;
  G.busy = true;
  try {
    G.bubbles = {};
    if (G.mode === "local") G.viewer = null;
    G.s = await gApi(`/${G.id}/next`, {});
    await animateNewHand();
  } catch (e) {
    gStatus(e.message, true);
  } finally {
    G.busy = false;
  }
  gameLoop();
}

// Le « conseil » réutilise l'API du mode TRICHE sur la situation réelle.
async function askAdvice() {
  if (!humanTurn()) return;
  const s = G.s, me = s.players[s.current];
  const opp = s.players.filter((p, i) => i !== s.current && p.n_cards && !p.folded).length;
  $("g-advice").textContent = "Le bot réfléchit…";
  try {
    const d = await callApi({
      hand: me.hole, board: s.board, n_opponents: Math.max(1, opp),
      pot: s.pot, to_call: s.legal.call_amount, n_sims: 4000, fold_equity: 0.3,
      raise_size: null, effective_stack: me.stack,
    });
    $("g-advice").innerHTML = `Conseil : <b>${d.recommendation.toUpperCase()}</b> — équité ${pct(d.equity)}, cote du pot ${pct(d.pot_odds)}`;
  } catch (e) {
    $("g-advice").textContent = e.message;
  }
}

function showGameOver() {
  const box = $("setup-box");
  const busted = !G.s.game_over;
  box.innerHTML = `<h2>${busted ? (G.mode === "solo" ? "💸 Tu es éliminé !" : "💸 Tous les humains sont éliminés !")
                              : `🏆 ${G.s.winner} gagne la partie !`}</h2>
    <p>${G.s.hand_no} mains jouées.</p>
    <div class="setup-row"><button class="primary" id="go-again">Rejouer</button><button id="go-menu">Menu</button></div>`;
  $("setup").hidden = false;
  $("go-again").onclick = () => { $("setup").hidden = true; startGame(G.lastConfig); };
  $("go-menu").onclick = () => openSetup();
}

async function startGame(cfg) {
  G.lastConfig = cfg;
  document.body.dataset.mode = "game";
  $("subtitle").textContent = cfg.mode === "solo" ? "Partie contre l'ordinateur" : "Partie entre amis (même ordinateur)";
  $("result").hidden = true;
  G.mode = cfg.mode;
  G.bubbles = {};
  G.me = cfg.mode === "solo" ? 0 : null;
  G.viewer = G.me;
  G.s = null;
  gStatus("");
  $("g-advice").textContent = "";
  try {
    G.busy = true;
    G.s = await gApi("/new", { players: cfg.players, stack: cfg.stack, small_blind: cfg.sb, big_blind: cfg.bb });
    G.id = G.s.id;
    await animateNewHand();
  } catch (e) {
    gStatus(e.message === "Failed to fetch" ? "Back-end injoignable : lance `python app.py` dans backend/." : e.message, true);
  } finally {
    G.busy = false;
  }
  gameLoop();
}

// ---------------------------------------------------------------- boutons
$("g-fold").onclick = () => humanAct("fold");
$("g-call").onclick = () => humanAct(G.s.legal.check ? "check" : "call");
$("g-raise-btn").onclick = () => {
  const R = G.s.legal.raise, v = Number($("g-raise-amount").value);
  humanAct(v >= R.max ? "allin" : "raise", Math.round(v));
};
$("g-raise-range").oninput = () => { $("g-raise-amount").value = $("g-raise-range").value; updateRaiseLabel(); };
$("g-raise-amount").oninput = () => { $("g-raise-range").value = $("g-raise-amount").value; updateRaiseLabel(); };
document.querySelectorAll(".g-quick button").forEach((b) => {
  b.onclick = () => {
    const s = G.s, R = s.legal && s.legal.raise;
    if (!R) return;
    const f = b.dataset.frac;
    let v = f === "all" ? R.max : s.current_bet + Number(f) * (s.pot + s.legal.call_amount);
    v = Math.max(R.min, Math.min(R.max, Math.round(v)));
    $("g-raise-amount").value = $("g-raise-range").value = v;
    updateRaiseLabel();
  };
});
$("g-next").onclick = nextHand;
$("g-menu").onclick = () => openSetup();
$("g-advice-btn").onclick = askAdvice;
