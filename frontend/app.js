// Pôle D
const USE_MOCK = false;              // true : pas besoin du back-end
const API_URL = "http://localhost:5000/api/analyze";

const $ = (id) => document.getElementById(id);
const parseCards = (s) => s.trim().split(/[\s,]+/).filter(Boolean);
const pct = (x) => (100 * x).toFixed(1) + " %";

async function analyze(payload) {
  if (USE_MOCK) {
    const r = await fetch("mock/analyze.json");
    return r.json();
  }
  const r = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || "Erreur serveur");
  return data;
}

function render(d) {
  $("r-equity").textContent = pct(d.equity);
  $("r-pot-odds").textContent = pct(d.pot_odds);
  $("r-ev-fold").textContent = d.ev.fold.toFixed(1);
  $("r-ev-call").textContent = d.ev.call.toFixed(1);
  const reco = $("r-reco");
  reco.textContent = d.recommendation.toUpperCase();
  reco.className = d.recommendation;
  $("result").hidden = false;
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = $("status");
  status.className = "";
  status.textContent = "Simulation en cours…";
  $("result").hidden = true;
  try {
    const d = await analyze({
      hand: parseCards($("hand").value),
      board: parseCards($("board").value),
      n_opponents: Number($("n_opponents").value),
      pot: Number($("pot").value),
      to_call: Number($("to_call").value),
      n_sims: 10000,
    });
    status.textContent = "";
    render(d);
  } catch (err) {
    status.className = "error";
    status.textContent = err.message;
  }
});
