"""Point d'entrée Flask (pôle C)."""
from flask import Flask
from flask_cors import CORS

from api.routes import bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(bp, url_prefix="/api")
    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
