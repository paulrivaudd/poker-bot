from engine import equity


def test_probabilities_sum_to_one():
    r = equity(["As", "Kd"], [], 1, 1000, seed=0)
    assert abs(r["win"] + r["tie"] + r["lose"] - 1) < 1e-9


def test_aces_vs_random():
    r = equity(["As", "Ah"], [], 1, 20000, seed=1)
    assert 0.83 < r["share"] < 0.87


def test_seventy_two_vs_random():
    r = equity(["7c", "2d"], [], 1, 20000, seed=2)
    assert 0.32 < r["share"] < 0.37


def test_nuts_on_river():
    r = equity(["As", "Ks"], ["Qs", "Js", "Ts", "2d", "3c"], 1, 500, seed=3)
    assert r["win"] == 1.0


def test_board_plays():
    # board = quinte flush royale : partage systématique
    r = equity(["2c", "3d"], ["Ts", "Js", "Qs", "Ks", "As"], 1, 500, seed=4)
    assert r["tie"] == 1.0 and abs(r["share"] - 0.5) < 1e-9


def test_more_opponents_lower_equity():
    one = equity(["As", "Ah"], [], 1, 5000, seed=5)["share"]
    four = equity(["As", "Ah"], [], 4, 5000, seed=5)["share"]
    assert four < one
