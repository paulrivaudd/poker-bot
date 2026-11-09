"""Calcul d'équité par Monte Carlo (pôle A)."""
import math
import random

from engine.cards import parse, remaining_deck
from engine.evaluator import evaluate_parsed


def equity(hand: list[str], board: list[str], n_opponents: int,
           n_sims: int = 10000, seed: int | None = None) -> dict:
    """Probabilités win / tie / lose du héros contre n adversaires à mains aléatoires.

    `share` = part moyenne du pot gagnée (gère les partages à plusieurs).
    `share_ci` = demi-largeur de l'intervalle de confiance à 95 % sur `share`.
    """
    rng = random.Random(seed)
    hero = [parse(c) for c in hand]
    known_board = [parse(c) for c in board]
    deck = [parse(c) for c in remaining_deck(hand + board)]
    n_board = 5 - len(board)
    n_draw = 2 * n_opponents + n_board

    win = tie = 0
    share = 0.0
    share_sq = 0.0
    for _ in range(n_sims):
        drawn = rng.sample(deck, n_draw)
        full_board = known_board + drawn[:n_board]
        hero_score = evaluate_parsed(hero + full_board)

        best_opp = -1
        n_best = 0
        for i in range(n_opponents):
            j = n_board + 2 * i
            s = evaluate_parsed(drawn[j:j + 2] + full_board)
            if s > best_opp:
                best_opp, n_best = s, 1
            elif s == best_opp:
                n_best += 1

        if hero_score > best_opp:
            win += 1
            share += 1
            share_sq += 1
        elif hero_score == best_opp:
            tie += 1
            x = 1 / (n_best + 1)
            share += x
            share_sq += x * x

    mean = share / n_sims
    var = max(share_sq / n_sims - mean * mean, 0.0)
    return {
        "win": win / n_sims,
        "tie": tie / n_sims,
        "lose": (n_sims - win - tie) / n_sims,
        "share": mean,
        "share_ci": 1.96 * math.sqrt(var / n_sims),
    }


def equity_curve(hand: list[str], board: list[str], n_opponents: int,
                 n_sims: int = 5000, seed: int | None = None) -> list[float]:
    """Équité (part du pot) contre m adversaires, pour m = 1..n, en une seule passe.

    À chaque tirage on compare le héros aux m premiers adversaires tirés :
    les m premières mains d'un tirage de n mains forment un tirage de m mains.
    Renvoie une liste `curve` avec curve[m - 1] = équité contre m adversaires.
    """
    rng = random.Random(seed)
    hero = [parse(c) for c in hand]
    known_board = [parse(c) for c in board]
    deck = [parse(c) for c in remaining_deck(hand + board)]
    n_board = 5 - len(board)
    n_draw = 2 * n_opponents + n_board
    totals = [0.0] * n_opponents

    for _ in range(n_sims):
        drawn = rng.sample(deck, n_draw)
        full_board = known_board + drawn[:n_board]
        hero_score = evaluate_parsed(hero + full_board)
        best, n_best = -1, 0
        for i in range(n_opponents):
            j = n_board + 2 * i
            s = evaluate_parsed(drawn[j:j + 2] + full_board)
            if s > best:
                best, n_best = s, 1
            elif s == best:
                n_best += 1
            if hero_score > best:
                totals[i] += 1
            elif hero_score == best:
                totals[i] += 1 / (n_best + 1)
            else:  # battu par l'un des i+1 premiers : battu aussi pour tout m > i
                break
    return [t / n_sims for t in totals]
