from flask import Blueprint, request, jsonify
import jwt
from db import cursor, db

jobs_bp = Blueprint("jobs", __name__)

JWT_SECRET = "jobtracker_secret_key"


# ================= JWT VERIFY =================
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


# ================= ADD JOB =================
@jobs_bp.route("/jobs", methods=["POST"])
def add_job():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    cursor.execute(
        """
        INSERT INTO job_applications
        (user_id, company, role, location, status, applied_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            user["user_id"],
            data.get("company"),
            data.get("role"),
            data.get("location"),      # ✅ location fixed
            data.get("status", "Applied"),
            data.get("applied_date"),
        ),
    )

    db.commit()
    return jsonify({"message": "Job added"}), 201


# ================= GET JOBS =================
@jobs_bp.route("/jobs", methods=["GET"])
def get_jobs():
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    company = request.args.get("company")
    status = request.args.get("status")

    query = "SELECT * FROM job_applications WHERE user_id=%s"
    params = [user["user_id"]]

    if company:
        query += " AND company LIKE %s"
        params.append(f"%{company}%")

    if status:
        query += " AND status=%s"
        params.append(status)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, tuple(params))
    jobs = cursor.fetchall()

    return jsonify(jobs)


# ================= UPDATE JOB (STATUS ONLY) =================
@jobs_bp.route("/jobs/<int:job_id>", methods=["PUT"])
def update_job(job_id):
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    # Fetch existing job
    cursor.execute(
        """
        SELECT company, role, location, status, applied_date
        FROM job_applications
        WHERE id=%s AND user_id=%s
        """,
        (job_id, user["user_id"])
    )
    job = cursor.fetchone()

    if not job:
        return jsonify({"error": "Job not found"}), 404

    # 🔒 Lock final states
    if job["status"] in ["Rejected", "Offer"]:
        return jsonify({"message": "Final status locked"}), 200

    # Preserve existing values
    company = data.get("company", job["company"])
    role = data.get("role", job["role"])
    location = data.get("location", job["location"])
    status = data.get("status", job["status"])
    applied_date = data.get("applied_date", job["applied_date"])

    cursor.execute(
        """
        UPDATE job_applications
        SET company=%s,
            role=%s,
            location=%s,
            status=%s,
            applied_date=%s
        WHERE id=%s AND user_id=%s
        """,
        (company, role, location, status, applied_date, job_id, user["user_id"])
    )

    db.commit()
    return jsonify({"message": "Job updated"}), 200


# ================= DELETE JOB =================
@jobs_bp.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    user = verify_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    cursor.execute(
        "DELETE FROM job_applications WHERE id=%s AND user_id=%s",
        (job_id, user["user_id"])
    )

    db.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"message": "Job deleted"}), 200
