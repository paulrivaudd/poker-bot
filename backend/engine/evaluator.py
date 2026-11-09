"""Évaluateur de mains 5 à 7 cartes (pôle A).

Évaluation directe (sans énumérer les 21 combinaisons) : comptage des rangs
et des couleurs. Le score est un int comparable :
    catégorie * 16^5 + kickers (5 rangs, 4 bits chacun).
"""
from engine.cards import parse

HIGH_CARD, PAIR, TWO_PAIR, TRIPS, STRAIGHT, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH = range(9)
CATEGORY_NAMES = [
    "Carte haute", "Paire", "Double paire", "Brelan", "Quinte",
    "Couleur", "Full", "Carré", "Quinte flush",
]


def _score(category: int, kickers: list[int]) -> int:
    s = category
    for i in range(5):
        s = s * 16 + (kickers[i] if i < len(kickers) else 0)
    return s


def _straight_high(ranks: set[int]) -> int:
    """Rang de la carte haute de la meilleure quinte, -1 si aucune."""
    for high in range(12, 3, -1):
        if all((high - k) in ranks for k in range(5)):
            return high
    if {12, 0, 1, 2, 3} <= ranks:      # roue A-2-3-4-5
        return 3
    return -1


def evaluate_parsed(cards: list[tuple[int, int]]) -> int:
    rank_count = [0] * 13
    suit_cards: list[list[int]] = [[], [], [], []]
    for r, s in cards:
        rank_count[r] += 1
        suit_cards[s].append(r)

    # Couleur / quinte flush
    for sc in suit_cards:
        if len(sc) >= 5:
            sf = _straight_high(set(sc))
            if sf >= 0:
                return _score(STRAIGHT_FLUSH, [sf])
            flush = sorted(sc, reverse=True)[:5]
            flush_score = _score(FLUSH, flush)
            break
    else:
        flush_score = -1

    quads, trips, pairs, singles = [], [], [], []
    for r in range(12, -1, -1):
        c = rank_count[r]
        if c == 4:
            quads.append(r)
        elif c == 3:
            trips.append(r)
        elif c == 2:
            pairs.append(r)
        elif c == 1:
            singles.append(r)

    if quads:
        q = quads[0]
        kicker = max(r for r in range(13) if rank_count[r] and r != q)
        return _score(QUADS, [q, kicker])

    if trips and (len(trips) >= 2 or pairs):
        t = trips[0]
        p = max(trips[1:] + pairs)
        return _score(FULL_HOUSE, [t, p])

    if flush_score >= 0:
        return flush_score

    st = _straight_high({r for r in range(13) if rank_count[r]})
    if st >= 0:
        return _score(STRAIGHT, [st])

    if trips:
        return _score(TRIPS, [trips[0]] + singles[:2])

    if len(pairs) >= 2:
        hi, lo = pairs[0], pairs[1]
        kicker = max(pairs[2:] + singles[:1])
        return _score(TWO_PAIR, [hi, lo, kicker])

    if pairs:
        return _score(PAIR, [pairs[0]] + singles[:3])

    return _score(HIGH_CARD, singles[:5])


def evaluate(cards: list[str]) -> int:
    if not 5 <= len(cards) <= 7:
        raise ValueError("evaluate attend 5 à 7 cartes")
    return evaluate_parsed([parse(c) for c in cards])


def category(score: int) -> int:
    return score // 16 ** 5


def hand_name(cards: list[str]) -> str:
    return CATEGORY_NAMES[category(evaluate(cards))]
