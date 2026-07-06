from datetime import datetime, timezone
from extensions import db


class Project(db.Model):
    """
    One 'submission' by a user — either uploaded file(s) or a pasted snippet.
    """

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    project_name = db.Column(db.String(200), nullable=False)

    # How the code arrived: "file_upload" or "snippet"
    upload_type = db.Column(db.String(20), nullable=False, default="file_upload")

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # One project -> many reviews (you can re-run analysis on the same project)
    reviews = db.relationship(
        "Review", backref="project", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_name": self.project_name,
            "upload_type": self.upload_type,
            "created_at": self.created_at.isoformat(),
            "review_count": len(self.reviews),
        }
