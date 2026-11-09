import pytest

from engine import evaluate, hand_name


def test_wrong_size():
    with pytest.raises(ValueError):
        evaluate(["As", "Kd"])


ORDERED = [
    ["2h", "5d", "8c", "Js", "Kh"],          # carte haute
    ["2h", "2d", "8c", "Js", "Kh"],          # paire
    ["2h", "2d", "8c", "8s", "Kh"],          # double paire
    ["2h", "2d", "2c", "8s", "Kh"],          # brelan
    ["As", "2d", "3h", "4s", "5c"],          # roue
    ["5c", "6d", "7h", "8s", "9c"],          # quinte
    ["2h", "5h", "8h", "Jh", "Kh"],          # couleur
    ["2h", "2d", "2c", "8s", "8h"],          # full
    ["2h", "2d", "2c", "2s", "Kh"],          # carré
    ["As", "2s", "3s", "4s", "5s"],          # quinte flush roue
    ["Ts", "Js", "Qs", "Ks", "As"],          # quinte flush royale
]


def test_category_order():
    scores = [evaluate(h) for h in ORDERED]
    assert scores == sorted(scores)
    assert len(set(scores)) == len(scores)


def test_kickers():
    assert evaluate(["Ah", "Ad", "Kc", "8s", "3h"]) > evaluate(["As", "Ac", "Qc", "8s", "3h"])
    assert evaluate(["Ah", "Kd", "Qc", "Js", "9h"]) > evaluate(["As", "Kc", "Qd", "Jh", "8h"])


def test_tie():
    assert evaluate(["Ah", "Kd", "Qc", "Js", "9h"]) == evaluate(["As", "Kc", "Qd", "Jh", "9s"])


def test_seven_cards_best_five():
    # brelan + 2 paires -> full avec la meilleure paire
    assert hand_name(["Ks", "Kd", "Kh", "Qs", "Qd", "2s", "2d"]) == "Full"
    assert evaluate(["Ks", "Kd", "Kh", "Qs", "Qd", "2s", "2d"]) == evaluate(["Ks", "Kd", "Kh", "Qs", "Qd"])
    # 6 cartes en quinte -> la plus haute
    assert evaluate(["4c", "5d", "6h", "7s", "8c", "9d", "2h"]) == evaluate(["5d", "6h", "7s", "8c", "9d"])
    # couleur à 6 cartes : les 5 meilleures
    assert hand_name(["2h", "5h", "8h", "Jh", "Kh", "3h", "As"]) == "Couleur"


def test_names():
    assert hand_name(ORDERED[4]) == "Quinte"
    assert hand_name(ORDERED[-1]) == "Quinte flush"
