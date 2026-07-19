import os
 
from flask import Flask, jsonify, send_from_directory
from config import Config
from extensions import db, jwt, bcrypt, cors
 
# Where the built React app lives (created by `npm run build` in frontend/)
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
 
 
def create_app(config_class=Config) -> Flask:
    """
    Application factory. Keeping app creation inside a function (instead of
    at module top-level) makes testing and deployment much cleaner.
 
    In production this app serves BOTH the API (under /api/*) and the built
    React frontend (everything else) — one process, one URL, no CORS.
    """
    app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path="")
    app.config.from_object(config_class)
 
    # Initialise extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)  # same-origin in production, so CORS barely matters now
 
    # Make sure the uploads folder exists (fresh servers start without it)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
 
    # Import models so SQLAlchemy knows about them, then create tables.
    # (For the internship project create_all() is fine; a real production
    # app would use Flask-Migrate/Alembic migrations instead.)
    with app.app_context():
        import models  # noqa: F401
        db.create_all()
 
    # --- Blueprints ---
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    from routes.upload import upload_bp
    app.register_blueprint(upload_bp, url_prefix="/api/upload")
    from routes.review import review_bp
    app.register_blueprint(review_bp, url_prefix="/api/reviews")
    from routes.docs import docs_bp
    app.register_blueprint(docs_bp, url_prefix="/api/docs")
 
    # --- Health check: your first working endpoint ---
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "AI Code Review Assistant API"})
 
    # --- Serve the built React frontend ---
    # Any path that isn't /api/* returns either a real built file (JS/CSS/
    # images) or index.html, which lets React Router handle routes like
    # /projects/4 on the client side.
    @app.route("/")
    @app.route("/<path:path>")
    def serve_frontend(path=""):
        if path.startswith("api/"):
            return jsonify({"error": "Resource not found"}), 404
        full_path = os.path.join(app.static_folder, path)
        if path and os.path.isfile(full_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")
 
    # --- Consistent JSON error responses ---
    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Resource not found"}), 404
 
    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Internal server error"}), 500
 
    return app
 
 
app = create_app()
 
if __name__ == "__main__":
    app.run(debug=True, port=5000)