"""Aide à la décision (pôle B). Formules : voir docs/contrats.md.

Conventions : `pot` = ce qu'il y a déjà au milieu (mises adverses comprises),
`to_call` = montant à ajouter pour suivre, `raise_size` = montant total ajouté
par le héros s'il relance (> to_call). Les EV sont des gains nets à partir de
maintenant (l'argent déjà au pot est perdu).

Modèle multiway :
- `fold_equity` (f) est la probabilité qu'UN adversaire se couche face à une
  relance, chacun indépendamment : tout le monde se couche avec probabilité f^n,
  et le nombre de payeurs suit une loi binomiale B(n, 1 - f) ;
- `players_behind` (b) = adversaires qui parlent encore après nous sur ce tour :
  si on suit, chacun paie aussi `to_call` avec probabilité 1 - f, ce qui
  grossit le pot attendu ;
- `equity_curve[m - 1]` = équité contre m adversaires (si fournie), utilisée
  quand m adversaires paient la relance.

Cotes implicites (petites paires) : avec une paire servie sans brelan, on
suit pour toucher le brelan à la prochaine carte : on se couche si on rate,
et si on touche on gagne le pot plus une part `implied_fraction` du tapis
effectif restant. EV implicite = P(brelan) × gain attendu − to_call.
Hypothèses : on gagne toujours quand on touche (on néglige brelan contre
brelan supérieur) et on ne paie rien de plus quand on rate.
"""
from math import comb


def pot_odds(pot: float, to_call: float) -> float:
    total = pot + to_call
    return to_call / total if total > 0 else 0.0


def expected_pot_if_call(pot: float, to_call: float, players_behind: int = 0,
                         fold_equity: float = 0.0) -> float:
    """Pot attendu si on suit : notre mise + celles des joueurs qui parlent après nous."""
    return pot + to_call + players_behind * (1 - fold_equity) * to_call


def ev_call(equity: float, pot: float, to_call: float, players_behind: int = 0,
            fold_equity: float = 0.0) -> float:
    return equity * expected_pot_if_call(pot, to_call, players_behind, fold_equity) - to_call


def p_set_next(hand: list[str] | None, board: list[str] | None) -> float | None:
    """P(toucher le brelan ou mieux à la prochaine rue) pour une paire servie, sinon None."""
    if not hand or len(hand) != 2 or hand[0][0] != hand[1][0]:
        return None
    board = board or []
    if any(c[0] == hand[0][0] for c in board) or len(board) >= 5:
        return None  # déjà brelan, ou plus de carte à venir
    unseen = 52 - 2 - len(board)
    outs = 2
    if not board:  # flop : 3 cartes d'un coup
        return 1 - comb(unseen - outs, 3) / comb(unseen, 3)
    return outs / unseen


def ev_implied(p_hit: float, pot: float, to_call: float, effective_stack: float,
               implied_fraction: float, players_behind: int = 0, fold_equity: float = 0.0) -> float:
    gain = expected_pot_if_call(pot, to_call, players_behind, fold_equity) \
        + implied_fraction * max(effective_stack - to_call, 0)
    return p_hit * gain - to_call


def ev_raise(equity: float, pot: float, to_call: float, raise_size: float, fold_equity: float,
             n_opponents: int = 1, players_behind: int = 0,
             equity_curve: list[float] | None = None) -> float:
    """EV d'une relance contre n adversaires qui se couchent chacun avec proba f.

    Un payeur ajoute raise_size − to_call s'il avait déjà mis to_call, raise_size
    s'il parlait après nous : en moyenne raise_size − to_call × (1 − b/n).
    """
    n, f = n_opponents, fold_equity
    per_caller = raise_size - to_call * (1 - players_behind / n)
    ev = f ** n * pot
    for m in range(1, n + 1):
        p_m = comb(n, m) * (1 - f) ** m * f ** (n - m)
        eq_m = equity_curve[m - 1] if equity_curve and len(equity_curve) >= m else equity
        ev += p_m * (eq_m * (pot + raise_size + m * per_caller) - raise_size)
    return ev


def default_raise_size(pot: float, to_call: float) -> float:
    """Relance « taille du pot » : on paie, puis on mise le pot obtenu."""
    return to_call + (pot + to_call)


def analyze(equity: float, pot: float, to_call: float,
            raise_size: float | None = None, fold_equity: float = 0.3,
            n_opponents: int = 1, players_behind: int = 0,
            effective_stack: float | None = None, implied_fraction: float = 0.5,
            hand: list[str] | None = None, board: list[str] | None = None,
            equity_curve: list[float] | None = None) -> dict:
    if raise_size is None:
        raise_size = default_raise_size(pot, to_call)
    players_behind = max(0, min(players_behind, n_opponents))

    passive = "check" if to_call == 0 else "call"
    direct = ev_call(equity, pot, to_call, players_behind, fold_equity)

    p_set = p_set_next(hand, board) if effective_stack is not None and to_call > 0 else None
    implied = (ev_implied(p_set, pot, to_call, effective_stack, implied_fraction, players_behind, fold_equity)
               if p_set is not None else None)

    evs = {
        "fold": 0.0,
        passive: max(direct, implied) if implied is not None else direct,
        "raise": ev_raise(equity, pot, to_call, raise_size, fold_equity,
                          n_opponents, players_behind, equity_curve),
    }
    # check gratuit : ne jamais recommander fold
    candidates = {k: v for k, v in evs.items() if not (k == "fold" and to_call == 0)}
    reco = max(candidates, key=candidates.get)

    return {
        "pot_odds": pot_odds(pot, to_call),
        "expected_pot": expected_pot_if_call(pot, to_call, players_behind, fold_equity),
        "ev": evs,
        "ev_call_direct": direct,
        "ev_call_implied": implied,
        "p_set": p_set,
        "p_all_fold": fold_equity ** n_opponents,
        "raise_size": raise_size,
        "recommendation": reco,
    }
