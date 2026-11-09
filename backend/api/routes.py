"""Routes de l'API (pôle C)."""
from flask import Blueprint, jsonify, request

from api.validation import ValidationError, parse_analyze_request
from decision import analyze
from engine import equity

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
    eq_value = eq["win"] + eq["tie"] / 2
    decision = analyze(eq_value, req["pot"], req["to_call"])

    return jsonify({
        "equity": eq_value,
        "win": eq["win"],
        "tie": eq["tie"],
        **decision,
    })
