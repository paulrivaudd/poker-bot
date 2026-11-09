"""Routes du mode JEU (pôle C). Les parties sont gardées en mémoire du serveur."""
import uuid

from flask import Blueprint, jsonify, request

from game import Game, IllegalAction, bot_action

game_bp = Blueprint("game", __name__)
GAMES: dict[str, Game] = {}
MAX_GAMES = 50


def _err(msg, code=400):
    return jsonify({"error": msg}), code


def _get(gid):
    g = GAMES.get(gid)
    if g is None:
        raise KeyError
    return g


def _view(gid, g):
    viewer = request.args.get("viewer", type=int)
    if viewer is None and request.is_json:
        viewer = (request.get_json(silent=True) or {}).get("viewer")
    return jsonify({"id": gid, **g.view(viewer)})


@game_bp.post("/new")
def new_game():
    data = request.get_json(silent=True) or {}
    players = data.get("players")
    if not isinstance(players, list) or not 2 <= len(players) <= 10:
        return _err("Il faut entre 2 et 10 joueurs")
    try:
        seats = [(str(p.get("name") or f"Joueur {i + 1}")[:16], bool(p.get("bot"))) for i, p in enumerate(players)]
        stack = int(data.get("stack", 1000))
        sb = int(data.get("small_blind", 5))
        bb = int(data.get("big_blind", 2 * sb))
    except (TypeError, ValueError, AttributeError):
        return _err("Paramètres invalides")
    if not (stack > 0 and 0 < sb <= bb < stack):
        return _err("Il faut 0 < petite blinde ≤ grosse blinde < tapis")

    if len(GAMES) >= MAX_GAMES:
        GAMES.pop(next(iter(GAMES)))
    gid = uuid.uuid4().hex[:8]
    g = Game(seats, stack, sb, bb)
    g.start_hand()
    GAMES[gid] = g
    return _view(gid, g)


@game_bp.get("/<gid>")
def state(gid):
    try:
        return _view(gid, _get(gid))
    except KeyError:
        return _err("Partie introuvable", 404)


@game_bp.post("/<gid>/action")
def action(gid):
    try:
        g = _get(gid)
    except KeyError:
        return _err("Partie introuvable", 404)
    data = request.get_json(silent=True) or {}
    if g.current is None:
        return _err("Ce n'est le tour de personne")
    if g.players[g.current].is_bot:
        return _err("C'est au tour d'un ordinateur")
    try:
        amount = data.get("amount")
        g.act(str(data.get("action")), int(amount) if amount is not None else None)
    except (IllegalAction, ValueError, TypeError) as e:
        return _err(str(e))
    return _view(gid, g)


@game_bp.post("/<gid>/bot")
def bot(gid):
    """Fait jouer UNE action à l'ordinateur dont c'est le tour (le front anime entre deux appels)."""
    try:
        g = _get(gid)
    except KeyError:
        return _err("Partie introuvable", 404)
    if g.current is None or not g.players[g.current].is_bot:
        return _err("Ce n'est pas au tour d'un ordinateur")
    g.act(*bot_action(g))
    return _view(gid, g)


@game_bp.post("/<gid>/next")
def next_hand(gid):
    try:
        g = _get(gid)
        g.start_hand()
    except KeyError:
        return _err("Partie introuvable", 404)
    except IllegalAction as e:
        return _err(str(e))
    return _view(gid, g)
