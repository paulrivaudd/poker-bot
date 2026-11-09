"""Point d'entrée Flask (pôle C). Sert l'API et le front-end."""
import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from api.game_routes import game_bp
from api.routes import bp

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    CORS(app)
    app.register_blueprint(bp, url_prefix="/api")
    app.register_blueprint(game_bp, url_prefix="/api/game")

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:path>")
    def static_files(path):
        return send_from_directory(FRONTEND_DIR, path)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
