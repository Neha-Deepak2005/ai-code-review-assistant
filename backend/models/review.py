from datetime import datetime, timezone
from extensions import db


class Review(db.Model):
    """
    One analysis run for a project. Holds the overall score/summary;
    the individual issues live in ReviewFinding.
    """

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True
    )

    review_score = db.Column(db.Integer, nullable=True)  # 0–100, filled after analysis
    summary = db.Column(db.Text, nullable=True)

    # Status lets the frontend poll while analysis is running:
    # "pending" -> "running" -> "completed" / "failed"
    status = db.Column(db.String(20), nullable=False, default="pending")

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    findings = db.relationship(
        "ReviewFinding", backref="review", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self, include_findings: bool = False) -> dict:
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "review_score": self.review_score,
            "summary": self.summary,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "finding_count": len(self.findings),
        }
        if include_findings:
            data["findings"] = [f.to_dict() for f in self.findings]
        return data


class ReviewFinding(db.Model):
    """
    A single issue found in the code — by Pylint, Bandit, Radon, OR the AI.
    The `source` column tags where it came from, so static-analysis results
    and AI results live in ONE table and render in ONE UI component.
    """

    __tablename__ = "review_findings"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(
        db.Integer, db.ForeignKey("reviews.id"), nullable=False, index=True
    )

    source = db.Column(db.String(20), nullable=False, default="ai")  # pylint | bandit | radon | ai
    severity = db.Column(db.String(20), nullable=False, default="info")  # critical | high | medium | low | info
    issue = db.Column(db.String(300), nullable=False)        # short title
    explanation = db.Column(db.Text, nullable=True)          # what & why
    suggestion = db.Column(db.Text, nullable=True)           # how to fix
    file_name = db.Column(db.String(255), nullable=True)
    line_number = db.Column(db.Integer, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "review_id": self.review_id,
            "source": self.source,
            "severity": self.severity,
            "issue": self.issue,
            "explanation": self.explanation,
            "suggestion": self.suggestion,
            "file_name": self.file_name,
            "line_number": self.line_number,
        }
