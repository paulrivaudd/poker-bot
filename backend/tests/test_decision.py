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


# ---------- cotes implicites, multiway, fold equity par adversaire ----------
from decision.decision import expected_pot_if_call, p_set_next  # noqa: E402


def test_p_set_preflop_et_flop():
    assert abs(p_set_next(["7s", "7h"], []) - 0.1176) < 1e-3          # ≈ 11,8 % au flop
    assert abs(p_set_next(["7s", "7h"], ["2c", "9d", "Kh"]) - 2 / 47) < 1e-12
    assert p_set_next(["7s", "7h"], ["7c", "9d", "Kh"]) is None        # déjà brelan
    assert p_set_next(["As", "Kh"], []) is None                        # pas une paire


def test_cotes_implicites_rendent_le_call_rentable():
    # 22 contre une relance : équité directe trop faible, mais gros tapis derrière
    sans = analyze(0.10, 30, 20, fold_equity=0.3, hand=["2c", "2d"], board=[])
    avec = analyze(0.10, 30, 20, fold_equity=0.3, hand=["2c", "2d"], board=[],
                   effective_stack=2000, implied_fraction=0.5)
    assert sans["recommendation"] == "fold"
    assert avec["ev_call_implied"] > 0 and avec["recommendation"] in ("call", "raise")
    # tapis effectif court : pas de cotes implicites
    court = analyze(0.10, 30, 20, fold_equity=0.3, hand=["2c", "2d"], board=[], effective_stack=60)
    assert court["ev_call_implied"] < 0


def test_multiway_le_pot_grossit():
    assert expected_pot_if_call(100, 20, players_behind=0) == 120
    assert expected_pot_if_call(100, 20, players_behind=4, fold_equity=0.5) == 160
    assert ev_call(0.2, 100, 20, 4, 0.5) > ev_call(0.2, 100, 20)


def test_fold_equity_puissance_n():
    r = analyze(0.1, 100, 20, fold_equity=0.3, n_opponents=9)
    assert abs(r["p_all_fold"] - 0.3 ** 9) < 1e-12
    # le bluff qui marchait en heads-up ne marche plus contre 9 joueurs
    assert analyze(0.1, 100, 20, fold_equity=0.8)["recommendation"] == "raise"
    assert analyze(0.1, 100, 20, fold_equity=0.8, n_opponents=9)["recommendation"] != "raise"


def test_ev_raise_heads_up_inchangee():
    assert abs(ev_raise(0.5, 100, 20, 80, 0.5, n_opponents=1) - 70) < 1e-9


def test_ev_raise_utilise_l_equite_contre_les_payeurs():
    # avec f = 0 tout le monde paie : seule l'équité contre n compte
    curve = [0.8, 0.6, 0.4]
    ev = ev_raise(0.4, 100, 0, 100, 0.0, n_opponents=3, equity_curve=curve)
    assert abs(ev - (0.4 * (100 + 100 + 3 * 100) - 100)) < 1e-9
