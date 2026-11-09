"""Aide à la décision (pôle B). Formules : voir docs/contrats.md.

TODO (B, v2) : EV(raise) avec hypothèse de fold equity.
"""


def pot_odds(pot: float, to_call: float) -> float:
    total = pot + to_call
    return to_call / total if total > 0 else 0.0


def ev_call(equity: float, pot: float, to_call: float) -> float:
    return equity * (pot + to_call) - to_call


def analyze(equity: float, pot: float, to_call: float) -> dict:
    po = pot_odds(pot, to_call)
    if to_call == 0:
        reco = "check"
    else:
        reco = "call" if equity > po else "fold"
    return {
        "pot_odds": po,
        "ev": {"fold": 0.0, "call": ev_call(equity, pot, to_call)},
        "recommendation": reco,
    }
