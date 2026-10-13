import os
import secrets
from functools import wraps
from datetime import datetime, date
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from db import (
    get_db_connection, 
    test_connection, 
    init_admin_tables, 
    verify_admin_credentials
)

# Initialize Flask app
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# Secret key for session management
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Allow CORS with credentials support
CORS(app, supports_credentials=True)

# Active administrative tokens storage for API clients (Postman, Bruno, mobile/curl)
# Format: { token: { "username": str, "created_at": datetime } }
active_tokens = {}

# Ensure tables and default admin account exist on startup
init_admin_tables()

def serialize_row(row):
    """Formats database date objects into ISO strings for JSON serialization."""
    if not row:
        return row
    res = dict(row)
    if isinstance(res.get("deadline"), (date, datetime)):
        res["deadline"] = res["deadline"].strftime("%Y-%m-%d")
    if isinstance(res.get("created_at"), (date, datetime)):
        res["created_at"] = res["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(res.get("updated_at"), (date, datetime)):
        res["updated_at"] = res["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
    return res

# -------------------------------------------------------------
# AUTHENTICATION & AUTHORIZATION MIDDLEWARE
# -------------------------------------------------------------
def get_current_admin():
    """
    Checks whether the current request is from an authenticated admin.
    Supports:
    1. Flask Session Cookie (session['is_admin'])
    2. Authorization: Bearer <token>
    3. X-Admin-Token: <token>
    """
    # 1. Check Flask session cookie
    if session.get("is_admin"):
        return {
            "username": session.get("admin_username", "admin"),
            "source": "session"
        }

    # 2. Check Authorization Bearer header
    auth_header = request.headers.get("Authorization", "").strip()
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    elif request.headers.get("X-Admin-Token"):
        token = request.headers.get("X-Admin-Token").strip()

    if token and token in active_tokens:
        return {
            "username": active_tokens[token]["username"],
            "source": "token",
            "token": token
        }

    return None

def admin_required(f):
    """
    Decorator to protect administrative endpoints.
    Rejects unauthenticated requests with HTTP 401 Unauthorized.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin = get_current_admin()
        if not admin:
            return jsonify({
                "error": "Unauthorized",
                "message": "Authentication required. Administrator access only."
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------
# FRONTEND ROUTES
# -------------------------------------------------------------
@app.route("/")
def serve_frontend():
    """Serves the public research portal (read-only for visitors, admin controls when authenticated)."""
    return send_from_directory(app.static_folder, "index.html")

@app.route("/admin/login")
@app.route("/login")
def serve_admin_login():
    """Serves the dedicated administrative login page."""
    return send_from_directory(app.static_folder, "admin-login.html")

# -------------------------------------------------------------
# HEALTHCHECK & SYSTEM STATUS
# -------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    db_ok, msg = test_connection()
    return jsonify({
        "status": "online" if db_ok else "database_disconnected",
        "database": msg
    }), 200 if db_ok else 500

# -------------------------------------------------------------
# ADMIN AUTHENTICATION API ENDPOINTS
# -------------------------------------------------------------
@app.route("/api/auth/login", methods=["POST"])
def admin_login():
    """
    Authenticates the administrator.
    Accepts: { "username": "admin", "password": "..." }
    Returns: 200 OK with session token, or 401 Unauthorized.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "error": "Bad Request",
                "message": "Request body must contain valid JSON credentials."
            }), 400

        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))

        if not username or not password:
            return jsonify({
                "error": "Bad Request",
                "message": "Both username and password are required."
            }), 400

        is_valid, admin_info = verify_admin_credentials(username, password)
        if not is_valid:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid username or password."
            }), 401

        # Generate secure random token
        token = secrets.token_hex(32)
        active_tokens[token] = {
            "username": admin_info["username"],
            "user_id": admin_info["id"],
            "created_at": datetime.now().isoformat()
        }

        # Set secure Flask session
        session["is_admin"] = True
        session["admin_username"] = admin_info["username"]
        session["admin_id"] = admin_info["id"]
        session["token"] = token
        session.permanent = True

        return jsonify({
            "success": True,
            "message": "Administrator authenticated successfully.",
            "token": token,
            "admin": {
                "username": admin_info["username"],
                "full_name": admin_info.get("full_name") or "Portal Administrator"
            }
        }), 200

    except Exception as e:
        print(f"[Error] POST /api/auth/login: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

@app.route("/api/auth/logout", methods=["POST"])
def admin_logout():
    """
    Terminates the administrative session and invalidates the session token.
    """
    try:
        # Invalidate active token if present
        auth_header = request.headers.get("Authorization", "").strip()
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            if token in active_tokens:
                del active_tokens[token]

        session_token = session.get("token")
        if session_token and session_token in active_tokens:
            del active_tokens[session_token]

        # Invalidate Flask session
        session.clear()

        return jsonify({
            "success": True,
            "message": "Administrator logged out successfully. Session invalidated."
        }), 200

    except Exception as e:
        print(f"[Error] POST /api/auth/logout: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    """
    Returns current authentication status (publicly queryable).
    """
    admin = get_current_admin()
    if admin:
        return jsonify({
            "authenticated": True,
            "role": "administrator",
            "username": admin["username"]
        }), 200
    else:
        return jsonify({
            "authenticated": False,
            "role": "visitor"
        }), 200

# -------------------------------------------------------------
# 1. PUBLIC: RETRIEVE ALL RESEARCH OPPORTUNITIES (GET /api/opportunities)
# -------------------------------------------------------------
@app.route("/api/opportunities", methods=["GET"])
def get_all_opportunities():
    """Publicly accessible to all visitors and administrator."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM research_opportunities ORDER BY id DESC;")
            rows = cursor.fetchall()
        conn.close()

        opportunities = [serialize_row(r) for r in rows]
        return jsonify({
            "success": True,
            "count": len(opportunities),
            "data": opportunities
        }), 200

    except Exception as e:
        print(f"[Error] GET /api/opportunities: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

# -------------------------------------------------------------
# 2. PUBLIC: RETRIEVE ONE RESEARCH OPPORTUNITY (GET /api/opportunities/:id)
# -------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["GET"])
def get_opportunity(opp_id):
    """Publicly accessible to all visitors and administrator."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (opp_id,))
            opportunity = cursor.fetchone()
        conn.close()

        if not opportunity:
            return jsonify({
                "error": "Not Found",
                "message": f"Research opportunity with ID {opp_id} does not exist."
            }), 404

        return jsonify({
            "success": True,
            "data": serialize_row(opportunity)
        }), 200

    except Exception as e:
        print(f"[Error] GET /api/opportunities/{opp_id}: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

# -------------------------------------------------------------
# 3. PROTECTED: CREATE A RESEARCH OPPORTUNITY (POST /api/opportunities)
# -------------------------------------------------------------
@app.route("/api/opportunities", methods=["POST"])
@admin_required
def create_opportunity():
    """Protected: Only authenticated administrators can create opportunities."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "error": "Bad Request",
                "message": "Invalid JSON or request body missing."
            }), 400

        # Required fields validation
        required_fields = [
            "title", "description", "research_area", 
            "faculty_name", "department", "required_skills", 
            "available_positions", "deadline"
        ]

        missing = [field for field in required_fields if field not in data or str(data[field]).strip() == ""]
        if missing:
            return jsonify({
                "error": "Bad Request",
                "message": f"Missing required fields: {', '.join(missing)}"
            }), 400

        title = str(data["title"]).strip()
        description = str(data["description"]).strip()
        research_area = str(data["research_area"]).strip()
        faculty_name = str(data["faculty_name"]).strip()
        department = str(data["department"]).strip()
        required_skills = str(data["required_skills"]).strip()

        # Validate available_positions
        try:
            available_positions = int(data["available_positions"])
            if available_positions <= 0:
                return jsonify({
                    "error": "Bad Request",
                    "message": "available_positions must be a positive integer greater than 0."
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "error": "Bad Request",
                "message": "available_positions must be a valid integer."
            }), 400

        # Validate deadline format (YYYY-MM-DD)
        deadline_str = str(data["deadline"]).strip()
        try:
            datetime.strptime(deadline_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "error": "Bad Request",
                "message": "deadline must be formatted as YYYY-MM-DD."
            }), 400

        # Validate status (Optional, defaults to Open)
        status = data.get("status", "Open")
        if status not in ["Open", "Closed"]:
            return jsonify({
                "error": "Bad Request",
                "message": "status must be either 'Open' or 'Closed'."
            }), 400

        # Insert into database
        conn = get_db_connection()
        with conn.cursor() as cursor:
            insert_query = """
                INSERT INTO research_opportunities 
                (title, description, research_area, faculty_name, department, required_skills, available_positions, deadline, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (
                title, description, research_area, faculty_name, 
                department, required_skills, available_positions, deadline_str, status
            ))
            new_id = cursor.lastrowid

            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (new_id,))
            created_opportunity = cursor.fetchone()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Research opportunity created successfully.",
            "data": serialize_row(created_opportunity)
        }), 201

    except Exception as e:
        print(f"[Error] POST /api/opportunities: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

# -------------------------------------------------------------
# 4. PROTECTED: UPDATE A RESEARCH OPPORTUNITY (PUT /api/opportunities/:id)
# -------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["PUT"])
@admin_required
def update_opportunity(opp_id):
    """Protected: Only authenticated administrators can update opportunities."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "error": "Bad Request",
                "message": "Request body must contain valid JSON."
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # First verify the resource exists
            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (opp_id,))
            existing = cursor.fetchone()
            if not existing:
                conn.close()
                return jsonify({
                    "error": "Not Found",
                    "message": f"Cannot update. Opportunity with ID {opp_id} not found."
                }), 404

            # Prepare update fields
            fields_to_update = {}
            allowed_fields = [
                "title", "description", "research_area", 
                "faculty_name", "department", "required_skills", 
                "available_positions", "deadline", "status"
            ]

            for key in allowed_fields:
                if key in data:
                    val = data[key]
                    if key in ["title", "description", "research_area", "faculty_name", "department", "required_skills"]:
                        if str(val).strip() == "":
                            conn.close()
                            return jsonify({
                                "error": "Bad Request",
                                "message": f"Field '{key}' cannot be empty."
                            }), 400
                        fields_to_update[key] = str(val).strip()

                    elif key == "available_positions":
                        try:
                            num = int(val)
                            if num <= 0:
                                conn.close()
                                return jsonify({
                                    "error": "Bad Request",
                                    "message": "available_positions must be greater than 0."
                                }), 400
                            fields_to_update[key] = num
                        except (ValueError, TypeError):
                            conn.close()
                            return jsonify({
                                "error": "Bad Request",
                                "message": "available_positions must be a valid integer."
                            }), 400

                    elif key == "deadline":
                        try:
                            datetime.strptime(str(val).strip(), "%Y-%m-%d")
                            fields_to_update[key] = str(val).strip()
                        except ValueError:
                            conn.close()
                            return jsonify({
                                "error": "Bad Request",
                                "message": "deadline must be formatted as YYYY-MM-DD."
                            }), 400

                    elif key == "status":
                        if val not in ["Open", "Closed"]:
                            conn.close()
                            return jsonify({
                                "error": "Bad Request",
                                "message": "status must be either 'Open' or 'Closed'."
                            }), 400
                        fields_to_update[key] = val

            if not fields_to_update:
                conn.close()
                return jsonify({
                    "error": "Bad Request",
                    "message": "No valid fields provided to update."
                }), 400

            set_clause = ", ".join([f"{k} = %s" for k in fields_to_update.keys()])
            values = list(fields_to_update.values()) + [opp_id]
            cursor.execute(f"UPDATE research_opportunities SET {set_clause} WHERE id = %s;", values)

            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (opp_id,))
            updated = cursor.fetchone()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Opportunity ID {opp_id} updated successfully.",
            "data": serialize_row(updated)
        }), 200

    except Exception as e:
        print(f"[Error] PUT /api/opportunities/{opp_id}: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

# -------------------------------------------------------------
# 5. PROTECTED: DELETE A RESEARCH OPPORTUNITY (DELETE /api/opportunities/:id)
# -------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["DELETE"])
@admin_required
def delete_opportunity(opp_id):
    """Protected: Only authenticated administrators can delete opportunities."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if exists
            cursor.execute("SELECT * FROM research_opportunities WHERE id = %s;", (opp_id,))
            existing = cursor.fetchone()
            if not existing:
                conn.close()
                return jsonify({
                    "error": "Not Found",
                    "message": f"Cannot delete. Opportunity with ID {opp_id} not found."
                }), 404

            cursor.execute("DELETE FROM research_opportunities WHERE id = %s;", (opp_id,))
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Research opportunity with ID {opp_id} deleted successfully."
        }), 200

    except Exception as e:
        print(f"[Error] DELETE /api/opportunities/{opp_id}: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

# -------------------------------------------------------------
# Error Handlers for 404 / 405
# -------------------------------------------------------------
@app.errorhandler(404)
def route_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "Not Found",
            "message": f"Endpoint '{request.path}' was not found."
        }), 404
    return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "error": "Method Not Allowed",
        "message": f"Method '{request.method}' is not allowed for this endpoint."
    }), 405

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 University Research Opportunity Portal API running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
