from __future__ import annotations

import warnings

from flask import Flask, jsonify
from flask_cors import CORS

try:
    from jwt.warnings import InsecureKeyLengthWarning

    warnings.filterwarnings("ignore", category=InsecureKeyLengthWarning)
except Exception:
    pass

from config import CORS_ORIGINS, PORT
from database.db import initialize_database
from ml.predictor import load_model
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from routes.task_routes import task_bp
from routes.assignment_routes import assignment_bp


def create_app() -> Flask:
    app = Flask(__name__)
    # Avoid 308 redirects on trailing slashes (e.g., POST /api/tasks vs /api/tasks/)
    app.url_map.strict_slashes = False

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": CORS_ORIGINS,
                "supports_credentials": True,
            }
        },
    )

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(task_bp, url_prefix="/api/tasks")
    app.register_blueprint(assignment_bp, url_prefix="/api/assignments")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    initialize_database()
    # Load ML model at startup
    load_model()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=PORT, debug=True)

