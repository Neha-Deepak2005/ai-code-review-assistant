"""
Importing models here does two things:
1. Lets you write `from models import User, Project, Review, ReviewFinding`
2. Ensures every model class is registered with SQLAlchemy BEFORE
   db.create_all() runs — otherwise tables silently don't get created.
"""

from models.user import User
from models.project import Project
from models.review import Review, ReviewFinding

__all__ = ["User", "Project", "Review", "ReviewFinding"]
