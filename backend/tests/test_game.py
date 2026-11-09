import random

import pytest

from game import Game, IllegalAction, bot_action


def heads_up(**kw):
    g = Game([("Alice", False), ("Bob", False)], seed=0, **kw)
    g.start_hand()
    return g


def test_heads_up_bouton_petite_blinde_et_parle_en_premier():
    g = heads_up()
    btn = g.players[g.button]
    assert btn.bet == 5 and g.current == g.button
    assert g.legal()["call_amount"] == 5


def test_fold_donne_le_pot():
    g = heads_up()
    other = 1 - g.button
    g.act("fold")
    assert g.hand_over and g.players[other].stack == 1005
    assert g.players[g.button].stack == 995


def test_option_grosse_blinde():
    g = heads_up()
    g.act("call")
    assert not g.hand_over and g.street == "preflop"  # la BB a encore la parole
    g.act("check")
    assert g.street == "flop" and len(g.board) == 3


def test_relance_minimum():
    g = heads_up()
    with pytest.raises(IllegalAction):
        g.act("raise", 15)  # min = 10 + 10
    g.act("raise", 30)
    assert g.legal()["raise"]["min"] == 50


def test_partie_complete_jusqu_au_showdown():
    g = heads_up()
    g.act("call"); g.act("check")
    for _ in range(3):
        g.act("check"); g.act("check")
    assert g.hand_over and len(g.board) == 5
    assert all(r["hand_name"] for r in g.results)
    assert sum(p.stack for p in g.players) == 2000


def test_pots_annexes():
    g = Game([("A", False), ("B", False), ("C", False)], seed=3)
    g.players[0].stack, g.players[1].stack, g.players[2].stack = 50, 200, 200
    g.button = 2  # bouton -> A (0) ; SB = B ; BB = C
    g.start_hand()
    g.players[0].hole = ["As", "Ah"]
    g.players[1].hole = ["Ks", "Kh"]
    g.players[2].hole = ["2c", "7d"]
    g.deck = ["3d", "8c", "9h", "Jd", "4c", "Qs", "5h", "6s"]  # pop() par la fin
    g.act("allin")            # A : 50
    g.act("allin")            # B : 200
    g.act("call")             # C : suit 200
    assert g.hand_over
    stacks = [p.stack for p in g.players]
    assert stacks[0] == 150                 # pot principal 3 x 50
    assert stacks[1] == 300                 # pot annexe 2 x 150
    assert stacks[2] == 0
    assert sum(stacks) == 450


def test_partage_jeton_impair():
    g = Game([("A", False), ("B", False), ("C", False)], seed=1)
    g.start_hand()
    for p in g.players:
        p.hole = []
    g.players[0].hole, g.players[1].hole, g.players[2].hole = ["2c", "3d"], ["2d", "3c"], ["4h", "5s"]
    g.deck = ["7h", "Ac", "8h", "Kd", "9h", "Qh", "Jh", "Tc"]
    while not g.hand_over:
        p = g.players[g.current]
        g.act("fold" if p.name == "C" and g.legal()["fold"] else ("call" if g.legal()["call"] else "check"))
    assert sum(p.stack for p in g.players) == 3000


def test_conservation_des_jetons_avec_bots():
    rng = random.Random(0)
    for seed in range(40):
        g = Game([(f"P{i}", True) for i in range(rng.randint(2, 6))], stack=200, seed=seed)
        total = sum(p.stack for p in g.players)
        for _ in range(20):
            if g.game_over:
                break
            g.start_hand()
            while not g.hand_over:
                g.act(*bot_action(g, n_sims=20, rng=rng))
            assert sum(p.stack for p in g.players) == total


def test_vue_cache_les_cartes_adverses():
    g = heads_up()
    v = g.view(viewer=0)
    assert v["players"][0]["hole"] and v["players"][1]["hole"] is None
    assert g.view()["players"][0]["hole"] is None
