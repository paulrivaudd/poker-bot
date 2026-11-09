"""Aide à la décision (pôle B). Formules : voir docs/contrats.md.

Conventions : `pot` inclut déjà la mise adverse, `to_call` = montant à ajouter pour suivre,
`raise_size` = montant total ajouté par le héros s'il relance (> to_call).
Les EV sont des gains nets à partir de maintenant (l'argent déjà au pot est perdu).

Hypothèses simplificatrices du modèle de relance :
- l'adversaire se couche avec probabilité `fold_equity`, sinon il paie (pas de sur-relance) ;
- l'équité quand il paie est la même que l'équité contre une main aléatoire.
"""


def pot_odds(pot: float, to_call: float) -> float:
    total = pot + to_call
    return to_call / total if total > 0 else 0.0


def ev_call(equity: float, pot: float, to_call: float) -> float:
    return equity * (pot + to_call) - to_call


def ev_raise(equity: float, pot: float, to_call: float, raise_size: float, fold_equity: float) -> float:
    called_pot = pot + raise_size + (raise_size - to_call)
    ev_if_called = equity * called_pot - raise_size
    return fold_equity * pot + (1 - fold_equity) * ev_if_called


def default_raise_size(pot: float, to_call: float) -> float:
    """Relance « taille du pot » : on paie, puis on mise le pot obtenu."""
    return to_call + (pot + to_call)


def analyze(equity: float, pot: float, to_call: float,
            raise_size: float | None = None, fold_equity: float = 0.3) -> dict:
    if raise_size is None:
        raise_size = default_raise_size(pot, to_call)

    passive = "check" if to_call == 0 else "call"
    evs = {
        "fold": 0.0,
        passive: ev_call(equity, pot, to_call),
        "raise": ev_raise(equity, pot, to_call, raise_size, fold_equity),
    }
    # check gratuit : ne jamais recommander fold
    candidates = {k: v for k, v in evs.items() if not (k == "fold" and to_call == 0)}
    reco = max(candidates, key=candidates.get)

    return {
        "pot_odds": pot_odds(pot, to_call),
        "ev": evs,
        "raise_size": raise_size,
        "recommendation": reco,
    }
