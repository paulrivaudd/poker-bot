"""Joueurs ordinateur : ils décident avec le moteur du projet (Monte Carlo + module décision)."""
import random

from decision import analyze
from engine import equity_curve


def bot_action(game, n_sims: int = 400, rng: random.Random | None = None) -> tuple[str, int | None]:
    rng = rng or random.Random()
    i = game.current
    p = game.players[i]
    legal = game.legal()
    n_opp = sum(1 for j, q in enumerate(game.players) if q.in_hand and j != i)
    n_opp = max(1, n_opp)
    curve = equity_curve(p.hole, game.board, n_opp, n_sims)
    noise = rng.uniform(-0.05, 0.05)  # un peu d'imprévisibilité
    # Le modèle suppose des mains adverses aléatoires. Or celui qui relance (ou paie une relance)
    # a en moyenne une main plus forte : on rabote l'équité à chaque relance vue sur la rue.
    discount = 0.8 ** game.n_raises
    curve = [min(1.0, max(0.0, e * discount + noise)) for e in curve]
    eq = curve[-1]

    to_call = legal["call_amount"]
    pot = game.pot
    # adversaires qui parlent encore après le bot sur ce tour
    n = len(game.players)
    behind = sum(1 for k in range(1, n) if (q := game.players[(i + k) % n]).can_act and not q.acted)
    eff = min(p.stack, max((q.stack + q.bet for j, q in enumerate(game.players) if q.in_hand and j != i), default=0))
    d = analyze(eq, pot, to_call, fold_equity=0.35, n_opponents=n_opp, players_behind=min(behind, n_opp),
                effective_stack=eff, implied_fraction=0.4, hand=p.hole, board=game.board, equity_curve=curve)
    reco = d["recommendation"]

    # bluff occasionnel
    if reco in ("check", "fold") and legal["raise"] and rng.random() < 0.06:
        reco = "raise"

    # pas de guerre de relances sans une vraie main
    if reco == "raise" and game.n_raises >= 2 and eq < 0.6:
        reco = "call" if d["ev"].get("call", d["ev"].get("check", 0)) > 0 else "fold"

    if reco == "raise" and legal["raise"]:
        r = legal["raise"]
        frac = rng.choice([0.5, 0.66, 1.0]) if eq < 0.8 else rng.choice([1.0, 1.5])
        target = game.current_bet + int(frac * (pot + to_call))
        target = max(r["min"], min(r["max"], target))
        return "raise", target
    if reco == "raise" or reco == "call":
        return ("call", None) if legal["call"] else ("check", None)
    if reco == "check" or not legal["fold"]:
        return "check", None
    return "fold", None
