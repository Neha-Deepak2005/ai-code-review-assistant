"""
Single place where Flask extensions are instantiated.

Why this file exists: if you create `db` inside app.py and models import it
from app.py, while app.py imports the models, you get a circular import.
Putting extensions here breaks that cycle — everything imports from
extensions.py instead.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()
