import pytest

from engine import evaluate


def test_wrong_size():
    with pytest.raises(ValueError):
        evaluate(["As", "Kd"])


@pytest.mark.skip(reason="TODO pôle A : évaluateur non implémenté")
def test_flush_beats_straight():
    flush = ["2h", "5h", "8h", "Jh", "Kh"]
    straight = ["5c", "6d", "7h", "8s", "9c"]
    assert evaluate(flush) > evaluate(straight)


@pytest.mark.skip(reason="TODO pôle A : évaluateur non implémenté")
def test_wheel_is_straight():
    wheel = ["As", "2d", "3h", "4s", "5c"]
    high_card = ["Ks", "Qd", "9h", "4s", "2c"]
    assert evaluate(wheel) > evaluate(high_card)
