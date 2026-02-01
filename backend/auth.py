from flask import Blueprint, request, jsonify
import jwt
import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from db import cursor, db

auth_bp = Blueprint("auth", __name__)

JWT_SECRET = "jobtracker_secret_key"
JWT_EXP_DAYS = 7

GOOGLE_CLIENT_ID = "839239103228-570jfidbdm9j9hu636mrc6tnh65d4gjf.apps.googleusercontent.com"


@auth_bp.route("/auth/google", methods=["POST"])
def google_login():
    data = request.get_json()
    token = data.get("token")

    if not token:
        return jsonify({"error": "Token missing"}), 400

    try:
        # ✅ Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = idinfo["email"]
        name = idinfo.get("name")
        google_id = idinfo["sub"]

    except Exception as e:
        return jsonify({"error": "Invalid Google token"}), 401

    # ✅ Check user in DB
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            """
            INSERT INTO users (name, email, google_id, auth_provider)
            VALUES (%s, %s, %s, 'google')
            """,
            (name, email, google_id)
        )
        db.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user["id"]

    # ✅ Create JWT
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DAYS)
    }

    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    # ✅ Send response
    return jsonify({
        "message": "Login successful",
        "token": jwt_token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    })
