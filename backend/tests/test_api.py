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


# ---------- mode JEU ----------
def _new(client, players=None):
    players = players or [{"name": "Moi"}, {"name": "Bot", "bot": True}]
    return client.post("/api/game/new", json={"players": players, "stack": 500})


def test_game_new_et_vue(client):
    r = _new(client)
    assert r.status_code == 200
    d = r.get_json()
    assert d["pot"] == 15 and len(d["players"]) == 2
    assert all(p["hole"] is None for p in d["players"])  # pas de viewer : rien de visible
    v = client.get(f"/api/game/{d['id']}?viewer=0").get_json()
    assert len(v["players"][0]["hole"]) == 2 and v["players"][1]["hole"] is None


def test_game_main_complete_contre_bot(client):
    gid = _new(client).get_json()["id"]
    for _ in range(100):
        d = client.get(f"/api/game/{gid}").get_json()
        if d["hand_over"]:
            break
        if d["players"][d["current"]]["bot"]:
            assert client.post(f"/api/game/{gid}/bot").status_code == 200
        else:
            act = "check" if d["legal"]["check"] else "call"
            assert client.post(f"/api/game/{gid}/action", json={"action": act}).status_code == 200
    d = client.get(f"/api/game/{gid}").get_json()
    assert d["hand_over"] and sum(p["stack"] for p in d["players"]) == 1000
    nxt = client.post(f"/api/game/{gid}/next")
    if d["game_over"]:  # un joueur a tout perdu : plus de main suivante
        assert nxt.status_code == 400
    else:
        assert nxt.get_json()["hand_no"] == 2


def test_game_erreurs(client):
    assert client.post("/api/game/new", json={"players": [{"name": "Seul"}]}).status_code == 400
    assert client.get("/api/game/inconnu").status_code == 404
    gid = _new(client, [{"name": "A"}, {"name": "B"}]).get_json()["id"]
    assert client.post(f"/api/game/{gid}/action", json={"action": "raise", "amount": 1}).status_code == 400
    assert client.post(f"/api/game/{gid}/bot").status_code == 400


def test_analyze_cotes_implicites_et_multiway(client):
    r = client.post("/api/analyze", json={
        "hand": ["5c", "5d"], "board": [], "n_opponents": 3, "pot": 30, "to_call": 20,
        "n_sims": 2000, "players_behind": 2, "effective_stack": 1500, "fold_equity": 0.3})
    d = r.get_json()
    assert r.status_code == 200
    assert abs(d["p_set"] - 0.1176) < 1e-3 and d["ev_call_implied"] is not None
    assert d["expected_pot"] > 50 and abs(d["p_all_fold"] - 0.027) < 1e-3
    bad = client.post("/api/analyze", json={"hand": ["5c", "5d"], "n_opponents": 1, "players_behind": 3})
    assert bad.status_code == 400
