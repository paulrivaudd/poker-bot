from engine.cards import FULL_DECK, is_valid_card, remaining_deck


def test_deck_size():
    assert len(FULL_DECK) == 52 and len(set(FULL_DECK)) == 52


def test_valid_cards():
    assert is_valid_card("As") and is_valid_card("2c")
    assert not is_valid_card("1s") and not is_valid_card("Ax") and not is_valid_card("10h")


def test_remaining_deck():
    assert len(remaining_deck(["As", "Kd"])) == 50
