"""
Authentication routes: register, login, current user, update profile,
change password.
 
How JWT auth works in this app:
1. User registers or logs in -> we return an access token (a signed string)
2. The frontend stores that token and sends it on every request in the
   header:  Authorization: Bearer <token>
3. Any route decorated with @jwt_required() rejects requests without a
   valid token. get_jwt_identity() tells us WHICH user the token belongs to.
"""
 
import re
 
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
 
from extensions import db
from models import User
 
auth_bp = Blueprint("auth", __name__)
 
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
 
 
# ---------------------------------------------------------------- register
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
 
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
 
    # --- Validation ---
    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409
 
    # --- Create user ---
    user = User(name=name, email=email)
    user.set_password(password)  # hashes with bcrypt, never stores plain text
    db.session.add(user)
    db.session.commit()
 
    # Log them in immediately by issuing a token.
    # NOTE: identity must be a string in recent flask-jwt-extended versions.
    token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Registration successful",
                    "access_token": token,
                    "user": user.to_dict()}), 201
 
 
# ------------------------------------------------------------------- login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
 
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
 
    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
 
    user = User.query.filter_by(email=email).first()
 
    # Same error for "no such user" and "wrong password" — never reveal
    # which one it was (that would let attackers probe for valid emails).
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
 
    token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Login successful",
                    "access_token": token,
                    "user": user.to_dict()}), 200
 
 
# ---------------------------------------------------------------------- me
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
 
 
# ---------------------------------------------------------- update profile
@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify({"error": "User not found"}), 404
 
    data = request.get_json(silent=True) or {}
 
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
 
    if name:
        user.name = name
    if email:
        if not EMAIL_REGEX.match(email):
            return jsonify({"error": "Invalid email format"}), 400
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            return jsonify({"error": "Email already in use"}), 409
        user.email = email
 
    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200
 