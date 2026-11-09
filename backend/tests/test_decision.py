from decision import analyze
from decision.decision import default_raise_size, ev_call, ev_raise, pot_odds


def test_pot_odds():
    assert abs(pot_odds(100, 20) - 20 / 120) < 1e-9


def test_ev_call():
    assert abs(ev_call(0.5, 100, 20) - 40) < 1e-9


def test_ev_raise_formula():
    # pot 100, à suivre 20, relance de 80 au total, fold eq 0.5, équité 0.5
    # payé : pot final 100 + 80 + 60 = 240, EV = 0.5*240 - 80 = 40 ; EV = 0.5*100 + 0.5*40 = 70
    assert abs(ev_raise(0.5, 100, 20, 80, 0.5) - 70) < 1e-9


def test_raise_without_fold_equity_is_call_plus_bet():
    # sans fold equity, relancer = suivre + miser en plus (EV marginale = (2eq-1)*extra)
    eq, pot, tc, r = 0.6, 100, 20, 80
    assert abs(ev_raise(eq, pot, tc, r, 0) - (ev_call(eq, pot, tc) + (2 * eq - 1) * (r - tc))) < 1e-9


def test_default_raise_is_pot_sized():
    assert default_raise_size(100, 20) == 140


def test_recommendations():
    assert analyze(0.1, 100, 20, fold_equity=0)["recommendation"] == "fold"
    assert analyze(0.4, 100, 20, fold_equity=0)["recommendation"] == "call"
    assert analyze(0.9, 100, 20, fold_equity=0)["recommendation"] == "raise"
    assert analyze(0.1, 100, 0, fold_equity=0)["recommendation"] == "check"
    # bluff rentable avec beaucoup de fold equity
    assert analyze(0.1, 100, 20, fold_equity=0.8)["recommendation"] == "raise"


def test_check_never_fold():
    r = analyze(0.0, 100, 0, fold_equity=0)
    assert r["recommendation"] != "fold" and "check" in r["ev"]
