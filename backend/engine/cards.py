"""Représentation des cartes (pôle A)."""
RANKS = "23456789TJQKA"
SUITS = "shdc"
FULL_DECK = [r + s for r in RANKS for s in SUITS]


def is_valid_card(card) -> bool:
    return isinstance(card, str) and len(card) == 2 and card[0] in RANKS and card[1] in SUITS


def parse(card: str) -> tuple[int, int]:
    """'As' -> (12, 0). Rang 0 (2) à 12 (A), couleur 0 à 3."""
    return RANKS.index(card[0]), SUITS.index(card[1])


def remaining_deck(excluded: list[str]) -> list[str]:
    ex = set(excluded)
    return [c for c in FULL_DECK if c not in ex]
