import os
import secrets
import re
from functools import wraps
from datetime import datetime, date
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from db import (
    get_db_connection,
    test_connection,
    init_admin_tables,
    verify_admin_credentials,
    register_faculty,
    verify_faculty_credentials,
    get_faculty_by_email
)

# ---------------------------------------------------------------------------
# App Bootstrap
# ---------------------------------------------------------------------------
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

CORS(app, supports_credentials=True)

# In-memory token store for API clients (Postman / curl)
# Format: { token: { "role": "admin"|"faculty", "username": str, "id": int, ... } }
active_tokens: dict = {}

# Run table migrations on startup
init_admin_tables()

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def serialize_row(row):
    """Converts date/datetime fields to ISO strings for JSON output."""
    if not row:
        return row
    res = dict(row)
    for field in ("deadline", "created_at", "updated_at"):
        if isinstance(res.get(field), (date, datetime)):
            fmt = "%Y-%m-%d" if field == "deadline" else "%Y-%m-%d %H:%M:%S"
            res[field] = res[field].strftime(fmt)
    return res

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))

# ---------------------------------------------------------------------------
# Authentication helpers — support cookie session OR Bearer token
# ---------------------------------------------------------------------------
def _token_from_request() -> str | None:
    auth = request.headers.get("Authorization", "").strip()
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.headers.get("X-Admin-Token", "").strip() or None

def get_current_user():
    """
    Returns a dict describing the authenticated user, or None.
    Dict keys: role ("admin" | "faculty"), id, username/email, full_name
    """
    # 1. Check Flask session
    role = session.get("role")
    if role == "admin" and session.get("is_admin"):
        return {
            "role":      "admin",
            "id":        session.get("admin_id"),
            "username":  session.get("admin_username", "admin"),
            "full_name": session.get("admin_full_name", "Portal Administrator"),
            "source":    "session"
        }
    if role == "faculty" and session.get("faculty_id"):
        return {
            "role":       "faculty",
            "id":         session.get("faculty_id"),
            "email":      session.get("faculty_email"),
            "full_name":  session.get("faculty_full_name"),
            "department": session.get("faculty_department"),
            "source":     "session"
        }

    # 2. Check Bearer / X-Admin-Token header
    token = _token_from_request()
    if token and token in active_tokens:
        return active_tokens[token]

    return None

def admin_required(f):
    """Decorator: requires admin role."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user["role"] != "admin":
            return jsonify({"error": "Unauthorized",
                            "message": "Administrator access only."}), 401
        return f(*args, **kwargs)
    return wrapper

def faculty_or_admin_required(f):
    """Decorator: requires faculty or admin role."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user["role"] not in ("admin", "faculty"):
            return jsonify({"error": "Unauthorized",
                            "message": "Authentication required. Please log in as faculty or admin."}), 401
        return f(*args, **kwargs)
    return wrapper

# ---------------------------------------------------------------------------
# Static Frontend Routes
# ---------------------------------------------------------------------------
@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/admin/login")
@app.route("/login")
def serve_admin_login():
    return send_from_directory(app.static_folder, "admin-login.html")

@app.route("/faculty/register")
def serve_faculty_register():
    return send_from_directory(app.static_folder, "faculty-register.html")

@app.route("/faculty/login")
def serve_faculty_login():
    return send_from_directory(app.static_folder, "faculty-login.html")

@app.route("/faculty/dashboard")
def serve_faculty_dashboard():
    return send_from_directory(app.static_folder, "faculty-dashboard.html")

@app.route("/admin/<path:filename>")
def serve_admin_assets(filename):
    fp = os.path.join(app.static_folder, filename)
    if os.path.exists(fp):
        return send_from_directory(app.static_folder, filename)
    return send_from_directory(app.static_folder, "admin-login.html")

# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    db_ok, msg = test_connection()
    return jsonify({"status": "online" if db_ok else "database_disconnected", "database": msg}), \
           200 if db_ok else 500

# ---------------------------------------------------------------------------
# AUTH: Status (publicly queryable)
# ---------------------------------------------------------------------------
@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False, "role": "visitor"}), 200
    if user["role"] == "admin":
        return jsonify({"authenticated": True, "role": "admin",
                        "username": user["username"],
                        "full_name": user.get("full_name")}), 200
    return jsonify({"authenticated": True, "role": "faculty",
                    "id":         user["id"],
                    "email":      user["email"],
                    "full_name":  user["full_name"],
                    "department": user.get("department")}), 200

# ---------------------------------------------------------------------------
# AUTH: Admin Login
# ---------------------------------------------------------------------------
@app.route("/api/auth/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Bad Request", "message": "JSON body required."}), 400

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    if not username or not password:
        return jsonify({"error": "Bad Request", "message": "Username and password are required."}), 400

    is_valid, admin_info = verify_admin_credentials(username, password)
    if not is_valid:
        return jsonify({"error": "Unauthorized", "message": "Invalid username or password."}), 401

    token = secrets.token_hex(32)
    active_tokens[token] = {
        "role":      "admin",
        "id":        admin_info["id"],
        "username":  admin_info["username"],
        "full_name": admin_info.get("full_name", "Portal Administrator"),
        "source":    "token"
    }

    session["role"]             = "admin"
    session["is_admin"]         = True
    session["admin_id"]         = admin_info["id"]
    session["admin_username"]   = admin_info["username"]
    session["admin_full_name"]  = admin_info.get("full_name", "Portal Administrator")
    session["token"]            = token
    session.permanent           = True

    return jsonify({
        "success": True,
        "message": "Administrator authenticated successfully.",
        "token":   token,
        "role":    "admin",
        "admin":   {"username": admin_info["username"],
                    "full_name": admin_info.get("full_name")}
    }), 200

# ---------------------------------------------------------------------------
# AUTH: Admin Logout
# ---------------------------------------------------------------------------
@app.route("/api/auth/logout", methods=["POST"])
def admin_logout():
    token = _token_from_request() or session.get("token")
    if token and token in active_tokens:
        del active_tokens[token]
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."}), 200

# ---------------------------------------------------------------------------
# AUTH: Faculty Register
# ---------------------------------------------------------------------------
@app.route("/api/faculty/register", methods=["POST"])
def faculty_register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Bad Request", "message": "JSON body required."}), 400

    full_name  = str(data.get("full_name", "")).strip()
    email      = str(data.get("email", "")).strip().lower()
    department = str(data.get("department", "")).strip()
    password   = str(data.get("password", ""))
    confirm    = str(data.get("confirm_password", ""))

    # Validation
    errors = {}
    if not full_name:
        errors["full_name"] = "Full name is required."
    if not email or not valid_email(email):
        errors["email"] = "A valid university email address is required."
    if not department:
        errors["department"] = "Department is required."
    if len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."
    if password != confirm:
        errors["confirm_password"] = "Passwords do not match."

    if errors:
        return jsonify({"error": "Validation Error", "fields": errors}), 422

    success, result = register_faculty(full_name, email, department, password)
    if not success:
        return jsonify({"error": "Conflict", "message": result}), 409

    return jsonify({
        "success": True,
        "message": "Faculty account created successfully. You can now log in.",
        "data":    result
    }), 201

# ---------------------------------------------------------------------------
# AUTH: Faculty Login
# ---------------------------------------------------------------------------
@app.route("/api/faculty/login", methods=["POST"])
def faculty_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Bad Request", "message": "JSON body required."}), 400

    email    = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not email or not password:
        return jsonify({"error": "Bad Request", "message": "Email and password are required."}), 400

    is_valid, faculty_info = verify_faculty_credentials(email, password)
    if not is_valid:
        return jsonify({"error": "Unauthorized", "message": "Invalid email or password."}), 401

    token = secrets.token_hex(32)
    active_tokens[token] = {
        "role":       "faculty",
        "id":         faculty_info["id"],
        "email":      faculty_info["email"],
        "full_name":  faculty_info["full_name"],
        "department": faculty_info["department"],
        "source":     "token"
    }

    session["role"]               = "faculty"
    session["faculty_id"]         = faculty_info["id"]
    session["faculty_email"]      = faculty_info["email"]
    session["faculty_full_name"]  = faculty_info["full_name"]
    session["faculty_department"] = faculty_info["department"]
    session["token"]              = token
    session.permanent             = True

    return jsonify({
        "success":  True,
        "message":  "Faculty authenticated successfully.",
        "token":    token,
        "role":     "faculty",
        "faculty":  {
            "id":         faculty_info["id"],
            "full_name":  faculty_info["full_name"],
            "email":      faculty_info["email"],
            "department": faculty_info["department"]
        }
    }), 200

# ---------------------------------------------------------------------------
# AUTH: Faculty Logout
# ---------------------------------------------------------------------------
@app.route("/api/faculty/logout", methods=["POST"])
def faculty_logout():
    token = _token_from_request() or session.get("token")
    if token and token in active_tokens:
        del active_tokens[token]
    session.clear()
    return jsonify({"success": True, "message": "Faculty logged out successfully."}), 200

# ---------------------------------------------------------------------------
# OPPORTUNITIES: GET all (PUBLIC)
# ---------------------------------------------------------------------------
@app.route("/api/opportunities", methods=["GET"])
def get_all_opportunities():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT ro.*, f.email AS faculty_email, f.full_name AS faculty_account_name
                FROM research_opportunities ro
                LEFT JOIN faculty f ON ro.faculty_id = f.id
                ORDER BY ro.id DESC;
            """)
            rows = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "count": len(rows),
                        "data": [serialize_row(r) for r in rows]}), 200
    except Exception as e:
        print(f"[Error] GET /api/opportunities: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# ---------------------------------------------------------------------------
# OPPORTUNITIES: GET one (PUBLIC)
# ---------------------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["GET"])
def get_opportunity(opp_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT ro.*, f.email AS faculty_email
                FROM research_opportunities ro
                LEFT JOIN faculty f ON ro.faculty_id = f.id
                WHERE ro.id = %s;
            """, (opp_id,))
            opp = cursor.fetchone()
        conn.close()
        if not opp:
            return jsonify({"error": "Not Found",
                            "message": f"Opportunity ID {opp_id} not found."}), 404
        return jsonify({"success": True, "data": serialize_row(opp)}), 200
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# ---------------------------------------------------------------------------
# OPPORTUNITIES: GET my posts (FACULTY only)
# ---------------------------------------------------------------------------
@app.route("/api/faculty/opportunities", methods=["GET"])
@faculty_or_admin_required
def get_my_opportunities():
    user = get_current_user()
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if user["role"] == "admin":
                cursor.execute("SELECT * FROM research_opportunities ORDER BY id DESC;")
            else:
                cursor.execute(
                    "SELECT * FROM research_opportunities WHERE faculty_id = %s ORDER BY id DESC;",
                    (user["id"],)
                )
            rows = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "count": len(rows),
                        "data": [serialize_row(r) for r in rows]}), 200
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# ---------------------------------------------------------------------------
# OPPORTUNITIES: CREATE (Faculty or Admin)
# ---------------------------------------------------------------------------
@app.route("/api/opportunities", methods=["POST"])
@faculty_or_admin_required
def create_opportunity():
    user = get_current_user()
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Bad Request", "message": "JSON body required."}), 400

        required_fields = ["title", "description", "research_area",
                           "faculty_name", "department", "required_skills",
                           "available_positions", "deadline"]
        missing = [f for f in required_fields if not str(data.get(f, "")).strip()]
        if missing:
            return jsonify({"error": "Bad Request",
                            "message": f"Missing required fields: {', '.join(missing)}"}), 400

        try:
            positions = int(data["available_positions"])
            if positions <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"error": "Bad Request",
                            "message": "available_positions must be a positive integer."}), 400

        deadline_str = str(data["deadline"]).strip()
        try:
            datetime.strptime(deadline_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Bad Request",
                            "message": "deadline must be YYYY-MM-DD."}), 400

        status = data.get("status", "Open")
        if status not in ("Open", "Closed"):
            return jsonify({"error": "Bad Request",
                            "message": "status must be 'Open' or 'Closed'."}), 400

        # Link to faculty account if posted by faculty
        faculty_id = user["id"] if user["role"] == "faculty" else None

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO research_opportunities
                (title, description, research_area, faculty_name, department,
                 required_skills, available_positions, deadline, status, faculty_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                str(data["title"]).strip(),
                str(data["description"]).strip(),
                str(data["research_area"]).strip(),
                str(data["faculty_name"]).strip(),
                str(data["department"]).strip(),
                str(data["required_skills"]).strip(),
                positions, deadline_str, status, faculty_id
            ))
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (new_id,))
            created = cursor.fetchone()
        conn.close()

        return jsonify({"success": True,
                        "message": "Research opportunity created successfully.",
                        "data": serialize_row(created)}), 201
    except Exception as e:
        print(f"[Error] POST /api/opportunities: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# ---------------------------------------------------------------------------
# OPPORTUNITIES: UPDATE (Admin = any | Faculty = own only)
# ---------------------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["PUT"])
@faculty_or_admin_required
def update_opportunity(opp_id):
    user = get_current_user()
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Bad Request", "message": "JSON body required."}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (opp_id,))
            existing = cursor.fetchone()

        if not existing:
            conn.close()
            return jsonify({"error": "Not Found",
                            "message": f"Opportunity ID {opp_id} not found."}), 404

        # Ownership check — faculty can only edit their own posts
        if user["role"] == "faculty":
            if existing.get("faculty_id") != user["id"]:
                conn.close()
                return jsonify({"error": "Forbidden",
                                "message": "You are not authorised to edit this opportunity. You can only edit your own posts."}), 403

        allowed = ["title", "description", "research_area", "faculty_name",
                   "department", "required_skills", "available_positions", "deadline", "status"]
        fields_to_update = {}

        with conn.cursor() as cursor:
            for key in allowed:
                if key not in data:
                    continue
                val = data[key]
                if key in ("title", "description", "research_area",
                           "faculty_name", "department", "required_skills"):
                    if not str(val).strip():
                        conn.close()
                        return jsonify({"error": "Bad Request",
                                        "message": f"'{key}' cannot be empty."}), 400
                    fields_to_update[key] = str(val).strip()
                elif key == "available_positions":
                    try:
                        n = int(val)
                        if n <= 0:
                            raise ValueError
                        fields_to_update[key] = n
                    except (ValueError, TypeError):
                        conn.close()
                        return jsonify({"error": "Bad Request",
                                        "message": "available_positions must be a positive integer."}), 400
                elif key == "deadline":
                    try:
                        datetime.strptime(str(val).strip(), "%Y-%m-%d")
                        fields_to_update[key] = str(val).strip()
                    except ValueError:
                        conn.close()
                        return jsonify({"error": "Bad Request",
                                        "message": "deadline must be YYYY-MM-DD."}), 400
                elif key == "status":
                    if val not in ("Open", "Closed"):
                        conn.close()
                        return jsonify({"error": "Bad Request",
                                        "message": "status must be 'Open' or 'Closed'."}), 400
                    fields_to_update[key] = val

            if not fields_to_update:
                conn.close()
                return jsonify({"error": "Bad Request",
                                "message": "No valid fields provided."}), 400

            set_clause = ", ".join([f"{k} = %s" for k in fields_to_update])
            values = list(fields_to_update.values()) + [opp_id]
            cursor.execute(f"UPDATE research_opportunities SET {set_clause} WHERE id = %s;", values)

            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (opp_id,))
            updated = cursor.fetchone()
        conn.close()

        return jsonify({"success": True,
                        "message": f"Opportunity ID {opp_id} updated successfully.",
                        "data": serialize_row(updated)}), 200
    except Exception as e:
        print(f"[Error] PUT /api/opportunities/{opp_id}: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# ---------------------------------------------------------------------------
# OPPORTUNITIES: DELETE (Admin = any | Faculty = own only)
# ---------------------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["DELETE"])
@faculty_or_admin_required
def delete_opportunity(opp_id):
    user = get_current_user()
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (opp_id,))
            existing = cursor.fetchone()

        if not existing:
            conn.close()
            return jsonify({"error": "Not Found",
                            "message": f"Opportunity ID {opp_id} not found."}), 404

        # Ownership check
        if user["role"] == "faculty":
            if existing.get("faculty_id") != user["id"]:
                conn.close()
                return jsonify({"error": "Forbidden",
                                "message": "You are not authorised to delete this opportunity. You can only delete your own posts."}), 403

        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM research_opportunities WHERE id = %s;", (opp_id,))
        conn.close()

        return jsonify({"success": True,
                        "message": f"Opportunity ID {opp_id} deleted successfully."}), 200
    except Exception as e:
        print(f"[Error] DELETE /api/opportunities/{opp_id}: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def route_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not Found",
                        "message": f"Endpoint '{request.path}' not found."}), 404
    return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method Not Allowed",
                    "message": f"Method '{request.method}' is not allowed here."}), 405

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Research Portal running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
