import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_index(client):
    assert client.get("/").status_code == 200


def test_analyze_ok(client):
    r = client.post("/api/analyze", json={
        "hand": ["As", "Kd"], "board": ["7h", "8c", "2s"],
        "n_opponents": 1, "pot": 100, "to_call": 20, "n_sims": 1000,
    })
    assert r.status_code == 200
    data = r.get_json()
    for key in ("equity", "equity_ci", "win", "tie", "lose", "pot_odds", "ev",
                "raise_size", "recommendation", "hand_name"):
        assert key in data
    assert data["hand_name"] == "Carte haute"


def test_preflop_no_hand_name(client):
    r = client.post("/api/analyze", json={"hand": ["As", "Kd"], "n_sims": 100})
    assert r.get_json()["hand_name"] is None


@pytest.mark.parametrize("payload", [
    None,
    {"hand": ["As"]},
    {"hand": ["As", "Xx"]},
    {"hand": ["As", "As"]},
    {"hand": ["As", "Kd"], "board": ["7h"]},
    {"hand": ["As", "Kd"], "board": ["As", "8c", "2s"]},
    {"hand": ["As", "Kd"], "n_opponents": 0},
    {"hand": ["As", "Kd"], "pot": -5},
    {"hand": ["As", "Kd"], "pot": "abc"},
    {"hand": ["As", "Kd"], "fold_equity": 1.5},
    {"hand": ["As", "Kd"], "to_call": 50, "raise_size": 40},
])
def test_analyze_errors(client, payload):
    r = client.post("/api/analyze", json=payload)
    assert r.status_code == 400 and "error" in r.get_json()


def test_custom_raise(client):
    r = client.post("/api/analyze", json={
        "hand": ["As", "Ah"], "pot": 100, "to_call": 20, "raise_size": 60,
        "fold_equity": 0.2, "n_sims": 500,
    }).get_json()
    assert r["raise_size"] == 60 and "raise" in r["ev"]
