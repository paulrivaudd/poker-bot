import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_analyze_ok(client):
    r = client.post("/api/analyze", json={
        "hand": ["As", "Kd"], "board": ["7h", "8c", "2s"],
        "n_opponents": 1, "pot": 100, "to_call": 20, "n_sims": 1000,
    })
    assert r.status_code == 200
    data = r.get_json()
    for key in ("equity", "win", "tie", "pot_odds", "ev", "recommendation"):
        assert key in data


@pytest.mark.parametrize("payload", [
    {"hand": ["As"]},
    {"hand": ["As", "Xx"]},
    {"hand": ["As", "As"]},
    {"hand": ["As", "Kd"], "board": ["7h"]},
    {"hand": ["As", "Kd"], "board": ["As", "8c", "2s"]},
    {"hand": ["As", "Kd"], "n_opponents": 0},
    {"hand": ["As", "Kd"], "pot": -5},
])
def test_analyze_errors(client, payload):
    r = client.post("/api/analyze", json=payload)
    assert r.status_code == 400 and "error" in r.get_json()
