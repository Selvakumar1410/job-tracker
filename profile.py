from flask import Blueprint, request, jsonify
import jwt
from db import cursor, db

profile_bp = Blueprint("profile", __name__)

JWT_SECRET = "jobtracker_secret_key"


# 🔐 JWT verify helper
def verify_token(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        return None


# 👤 VIEW PROFILE
@profile_bp.route("/profile", methods=["GET"])
def view_profile():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    cursor.execute(
        "SELECT id, name, email, auth_provider, created_at FROM users WHERE id=%s",
        (user["user_id"],),
    )
    profile = cursor.fetchone()

    return jsonify(profile)


# ✏️ UPDATE PROFILE (NAME ONLY)
@profile_bp.route("/profile", methods=["PUT"])
def update_profile():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"error": "Name is required"}), 400

    cursor.execute(
        "UPDATE users SET name=%s WHERE id=%s",
        (name, user["user_id"]),
    )
    db.commit()

    return jsonify({"message": "Profile updated successfully"})
