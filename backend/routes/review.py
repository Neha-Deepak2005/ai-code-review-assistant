"""
Review routes — where analysis actually happens.

POST /run/<project_id>  -> run static analysis, store results, return them
GET  /<review_id>       -> fetch one review with all findings
GET  /                  -> list all my reviews (newest first)
"""

import os

from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Project, Review, ReviewFinding
from services.analyzer import analyze_project

review_bp = Blueprint("review", __name__)


@review_bp.route("/run/<int:project_id>", methods=["POST"])
@jwt_required()
def run_review(project_id):
    user_id = int(get_jwt_identity())

    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(user_id), str(project.id)
    )
    if not os.path.isdir(folder) or not os.listdir(folder):
        return jsonify({"error": "Project has no files to analyze"}), 400

    review = Review(project_id=project.id, status="running")
    db.session.add(review)
    db.session.commit()

    try:
        result = analyze_project(folder)
    except Exception as exc:  # noqa: BLE001 - mark failed instead of crashing
        review.status = "failed"
        review.summary = f"Analysis failed: {str(exc)[:300]}"
        db.session.commit()
        return jsonify({"error": "Analysis failed", "review": review.to_dict()}), 500

    review.review_score = result["score"]
    review.summary = result["summary"]
    review.status = "completed"

    for f in result["findings"]:
        db.session.add(ReviewFinding(
            review_id=review.id,
            source=f["source"],
            severity=f["severity"],
            issue=f["issue"],
            explanation=f.get("explanation"),
            suggestion=f.get("suggestion"),
            file_name=f.get("file_name"),
            line_number=f.get("line_number"),
        ))
    db.session.commit()

    return jsonify({
        "review": review.to_dict(include_findings=True),
        "metrics": result["metrics"],
    }), 200


@review_bp.route("/<int:review_id>", methods=["GET"])
@jwt_required()
def get_review(review_id):
    user_id = int(get_jwt_identity())

    # Join through Project to enforce ownership
    review = (
        Review.query.join(Project)
        .filter(Review.id == review_id, Project.user_id == user_id)
        .first()
    )
    if review is None:
        return jsonify({"error": "Review not found"}), 404

    return jsonify({"review": review.to_dict(include_findings=True)}), 200


@review_bp.route("/", methods=["GET"])
@jwt_required()
def list_reviews():
    user_id = int(get_jwt_identity())
    reviews = (
        Review.query.join(Project)
        .filter(Project.user_id == user_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    print("Number of reviews:", len(reviews))
    data = [r.to_dict() for r in reviews]
    print(data)
    return jsonify({"reviews": data}), 200
