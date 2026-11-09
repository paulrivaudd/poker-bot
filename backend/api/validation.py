"""Validation des entrées de l'API (pôle C)."""
from engine.cards import is_valid_card


class ValidationError(ValueError):
    pass


def parse_analyze_request(data) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("Corps JSON attendu")

    hand = data.get("hand")
    board = data.get("board", [])
    if not isinstance(hand, list) or len(hand) != 2:
        raise ValidationError("La main doit contenir 2 cartes")
    if not isinstance(board, list) or len(board) not in (0, 3, 4, 5):
        raise ValidationError("Le board doit contenir 0, 3, 4 ou 5 cartes")

    for c in hand + board:
        if not is_valid_card(c):
            raise ValidationError(f"Carte invalide : {c!r}")
    if len(set(hand + board)) != len(hand) + len(board):
        raise ValidationError("Carte en double")

    try:
        n_opponents = int(data.get("n_opponents", 1))
        pot = float(data.get("pot", 0))
        to_call = float(data.get("to_call", 0))
        n_sims = int(data.get("n_sims", 10000))
        fold_equity = float(data.get("fold_equity", 0.3))
        raise_size = data.get("raise_size")
        raise_size = None if raise_size in (None, "") else float(raise_size)
        players_behind = int(data.get("players_behind", 0))
        effective_stack = data.get("effective_stack")
        effective_stack = None if effective_stack in (None, "") else float(effective_stack)
        implied_fraction = float(data.get("implied_fraction", 0.5))
    except (TypeError, ValueError):
        raise ValidationError("Paramètres numériques invalides")

    if not 1 <= n_opponents <= 9:
        raise ValidationError("n_opponents doit être entre 1 et 9")
    if pot < 0 or to_call < 0:
        raise ValidationError("pot et to_call doivent être positifs")
    if not 1 <= n_sims <= 200_000:
        raise ValidationError("n_sims doit être entre 1 et 200000")

    if not 0 <= fold_equity <= 1:
        raise ValidationError("fold_equity doit être entre 0 et 1")
    if raise_size is not None and raise_size <= to_call:
        raise ValidationError("raise_size doit être supérieur à to_call")
    if not 0 <= players_behind <= n_opponents:
        raise ValidationError("players_behind doit être entre 0 et n_opponents")
    if effective_stack is not None and effective_stack < 0:
        raise ValidationError("effective_stack doit être positif")
    if not 0 <= implied_fraction <= 1:
        raise ValidationError("implied_fraction doit être entre 0 et 1")

    return {"hand": hand, "board": board, "n_opponents": n_opponents,
            "pot": pot, "to_call": to_call, "n_sims": n_sims,
            "raise_size": raise_size, "fold_equity": fold_equity,
            "players_behind": players_behind, "effective_stack": effective_stack,
            "implied_fraction": implied_fraction}
