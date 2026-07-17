"""
Docs routes — Day 10: AI documentation generator.

POST /generate/<project_id> -> generate Markdown docs for every .py file
                               in the project, return them combined.
"""

import os

from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Project
from services.docs_service import generate_docs, DocsError

docs_bp = Blueprint("docs", __name__)


@docs_bp.route("/generate/<int:project_id>", methods=["POST"])
@jwt_required()
def generate(project_id):
    user_id = int(get_jwt_identity())

    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(user_id), str(project.id)
    )
    if not os.path.isdir(folder) or not os.listdir(folder):
        return jsonify({"error": "Project has no files to document"}), 400

    py_files = sorted(
        f for f in os.listdir(folder)
        if f.endswith(".py") and os.path.isfile(os.path.join(folder, f))
    )

    sections = []
    for name in py_files:
        with open(os.path.join(folder, name), encoding="utf-8") as fh:
            code = fh.read()
        try:
            md = generate_docs(code, name)
        except DocsError as exc:
            return jsonify({"error": f"Documentation generation failed: {exc}"}), 502
        sections.append(f"# {name}\n\n{md}")

    return jsonify({
        "project_id": project.id,
        "documentation": "\n\n---\n\n".join(sections),
    })