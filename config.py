import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env into the environment


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # Database
    # Locally this falls back to SQLite (zero setup).
    # In production, set DATABASE_URL to your Supabase/Postgres connection string.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB max upload size
    ALLOWED_EXTENSIONS = {"py"}  # add "js" later if you do the optional JS support
