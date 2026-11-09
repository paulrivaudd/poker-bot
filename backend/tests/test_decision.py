from decision import analyze
from decision.decision import ev_call, pot_odds


def test_pot_odds():
    assert abs(pot_odds(100, 20) - 20 / 120) < 1e-9


def test_ev_call():
    assert abs(ev_call(0.5, 100, 20) - 40) < 1e-9


def test_recommendation():
    assert analyze(0.5, 100, 20)["recommendation"] == "call"
    assert analyze(0.1, 100, 20)["recommendation"] == "fold"
