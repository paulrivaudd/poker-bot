import pytest

from engine import equity


def test_probabilities_sum_to_one():
    r = equity(["As", "Kd"], [], 1, 1000)
    assert abs(r["win"] + r["tie"] + r["lose"] - 1) < 1e-9


@pytest.mark.skip(reason="TODO pôle A : Monte Carlo non implémenté")
def test_aces_vs_random():
    r = equity(["As", "Ah"], [], 1, 20000)
    assert 0.83 < r["win"] + r["tie"] / 2 < 0.87
