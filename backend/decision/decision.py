"""Aide à la décision (pôle B). Formules : voir docs/contrats.md.

TODO (B) : EV(raise) en v2 (hypothèse de fold equity).
"""


def pot_odds(pot: float, to_call: float) -> float:
    total = pot + to_call
    return to_call / total if total > 0 else 0.0


def ev_call(equity: float, pot: float, to_call: float) -> float:
    return equity * (pot + to_call) - to_call


def analyze(equity: float, pot: float, to_call: float) -> dict:
    po = pot_odds(pot, to_call)
    return {
        "pot_odds": po,
        "ev": {"fold": 0.0, "call": ev_call(equity, pot, to_call)},
        "recommendation": "call" if equity > po else "fold",
    }
