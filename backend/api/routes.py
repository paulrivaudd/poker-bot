"""Routes de l'API (pôle C)."""
from flask import Blueprint, jsonify, request

from api.validation import ValidationError, parse_analyze_request
from decision import analyze
from engine import equity, equity_curve, hand_name

bp = Blueprint("api", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/analyze")
def analyze_route():
    try:
        req = parse_analyze_request(request.get_json(silent=True))
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    eq = equity(req["hand"], req["board"], req["n_opponents"], req["n_sims"])
    n = req["n_opponents"]
    # équité contre 1..n adversaires (pour le nombre de payeurs d'une relance)
    curve = equity_curve(req["hand"], req["board"], n, max(500, req["n_sims"] // 2)) if n > 1 else [eq["share"]]
    curve[-1] = eq["share"]
    decision = analyze(eq["share"], req["pot"], req["to_call"], req["raise_size"], req["fold_equity"],
                       n_opponents=n, players_behind=req["players_behind"],
                       effective_stack=req["effective_stack"], implied_fraction=req["implied_fraction"],
                       hand=req["hand"], board=req["board"], equity_curve=curve)

    current = req["hand"] + req["board"]
    return jsonify({
        "equity": eq["share"],
        "equity_ci": eq["share_ci"],
        "win": eq["win"],
        "tie": eq["tie"],
        "lose": eq["lose"],
        "hand_name": hand_name(current) if len(current) >= 5 else None,
        **decision,
    })
