from flask import Flask, jsonify
from config import Config
from extensions import db, jwt, bcrypt, cors
 
 
def create_app(config_class=Config) -> Flask:
    """
    Application factory. Keeping app creation inside a function (instead of
    at module top-level) makes testing and deployment much cleaner.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
 
    # Initialise extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)  # later, restrict origins to your Vercel URL
 
    # Import models so SQLAlchemy knows about them, then create tables.
    # (For the internship project create_all() is fine; a real production
    # app would use Flask-Migrate/Alembic migrations instead.)
    with app.app_context():
        import models  # noqa: F401
        db.create_all()
 
    # --- Blueprints ---
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    # from routes.upload import upload_bp
    # app.register_blueprint(upload_bp, url_prefix="/api/upload")
 
    # --- Health check: your first working endpoint ---
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "AI Code Review Assistant API"})
 
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
 