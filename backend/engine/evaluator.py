"""Évaluateur de mains 5 à 7 cartes (pôle A).

TODO (A) : meilleure main de 5 parmi n (itertools.combinations),
catégorie (carte haute ... quinte flush) + kickers, encodés en un int comparable.
Penser à la quinte A-2-3-4-5.
"""


def evaluate(cards: list[str]) -> int:
    if not 5 <= len(cards) <= 7:
        raise ValueError("evaluate attend 5 à 7 cartes")
    # STUB : à remplacer
    return 0
