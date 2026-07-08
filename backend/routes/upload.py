"""
Upload & project routes.
 
Two ways code enters the system:
1. POST /file    -> multipart form upload of one or more .py files
2. POST /snippet -> JSON body with pasted code (saved as a .py file too)
 
Both create a Project row and store the code under:
    uploads/<user_id>/<project_id>/<filename>
 
Storing snippets as files too means the analysis engine (Day 5+) only ever
deals with files on disk — one code path instead of two.
"""
 
import os
 
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
 
from extensions import db
from models import Project
 
upload_bp = Blueprint("upload", __name__)
 
 
# ------------------------------------------------------------ helpers
def allowed_file(filename: str) -> bool:
    """True if the file has an extension we accept (e.g. .py)."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )
 
 
def project_dir(user_id: int, project_id: int) -> str:
    """Folder where this project's code lives; created if missing."""
    path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(user_id), str(project_id)
    )
    os.makedirs(path, exist_ok=True)
    return path
 
 
# ------------------------------------------------------- file upload
@upload_bp.route("/file", methods=["POST"])
@jwt_required()
def upload_file():
    user_id = int(get_jwt_identity())
 
    # Postman: Body -> form-data -> key "files" (type File), key "project_name" (type Text)
    files = request.files.getlist("files")
    project_name = (request.form.get("project_name") or "").strip()
 
    if not project_name:
        return jsonify({"error": "project_name is required"}), 400
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files provided"}), 400
 
    # Validate ALL files before saving ANY — no half-created projects.
    invalid = [f.filename for f in files if not allowed_file(f.filename)]
    if invalid:
        return jsonify({
            "error": f"Only .py files are allowed. Rejected: {', '.join(invalid)}"
        }), 400
 
    # Create the project row first so we get an ID for the folder name
    project = Project(user_id=user_id, project_name=project_name,
                      upload_type="file_upload")
    db.session.add(project)
    db.session.commit()
 
    saved = []
    folder = project_dir(user_id, project.id)
    for f in files:
        # secure_filename strips dangerous characters and path tricks
        # like "../../etc/passwd" — never trust user-supplied filenames.
        name = secure_filename(f.filename)
        f.save(os.path.join(folder, name))
        saved.append(name)
 
    return jsonify({
        "message": f"Uploaded {len(saved)} file(s)",
        "project": project.to_dict(),
        "files": saved,
    }), 201
 
 
# ---------------------------------------------------- snippet upload
@upload_bp.route("/snippet", methods=["POST"])
@jwt_required()
def upload_snippet():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
 
    project_name = (data.get("project_name") or "").strip()
    code = data.get("code") or ""
 
    if not project_name:
        return jsonify({"error": "project_name is required"}), 400
    if not code.strip():
        return jsonify({"error": "code cannot be empty"}), 400
    if len(code) > 100_000:  # ~100 KB of text is plenty for a snippet
        return jsonify({"error": "Snippet too large (max 100KB)"}), 400
 
    project = Project(user_id=user_id, project_name=project_name,
                      upload_type="snippet")
    db.session.add(project)
    db.session.commit()
 
    folder = project_dir(user_id, project.id)
    with open(os.path.join(folder, "snippet.py"), "w", encoding="utf-8") as fh:
        fh.write(code)
 
    return jsonify({
        "message": "Snippet saved",
        "project": project.to_dict(),
        "files": ["snippet.py"],
    }), 201
 
 
# ------------------------------------------------------ list projects
@upload_bp.route("/projects", methods=["GET"])
@jwt_required()
def list_projects():
    user_id = int(get_jwt_identity())
    projects = (
        Project.query.filter_by(user_id=user_id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return jsonify({"projects": [p.to_dict() for p in projects]}), 200
 
 
# ------------------------------------------------------ get one project
@upload_bp.route("/projects/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    user_id = int(get_jwt_identity())
 
    # Filtering by user_id too means users can NEVER see each other's
    # projects — even if they guess a valid ID. (Classic security bug
    # if you forget this: it's called an IDOR vulnerability.)
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if project is None:
        return jsonify({"error": "Project not found"}), 404
 
    folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(user_id), str(project.id)
    )
    files = os.listdir(folder) if os.path.isdir(folder) else []
 
    return jsonify({"project": project.to_dict(), "files": files}), 200
 
 
# ------------------------------------------------------ delete project
@upload_bp.route("/projects/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if project is None:
        return jsonify({"error": "Project not found"}), 404
 
    # Remove files from disk
    folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(user_id), str(project.id)
    )
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            os.remove(os.path.join(folder, name))
        os.rmdir(folder)
 
    # Deleting the project cascades to its reviews & findings (see models)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted"}), 200