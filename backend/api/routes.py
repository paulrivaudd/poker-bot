"""Routes de l'API (pôle C)."""
from flask import Blueprint, jsonify, request

from api.validation import ValidationError, parse_analyze_request
from decision import analyze
from engine import equity, hand_name

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
    decision = analyze(eq["share"], req["pot"], req["to_call"])

    current = req["hand"] + req["board"]
    return jsonify({
        "equity": eq["share"],
        "win": eq["win"],
        "tie": eq["tie"],
        "lose": eq["lose"],
        "hand_name": hand_name(current) if len(current) >= 5 else None,
        **decision,
    })
