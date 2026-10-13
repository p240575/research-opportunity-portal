import os
from datetime import datetime, date
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db import get_db_connection, test_connection

# Initialize Flask app
# Static folder points to frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app)

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
# Frontend Route
# -------------------------------------------------------------
@app.route("/")
def serve_frontend():
    return send_from_directory(app.static_folder, "index.html")

# -------------------------------------------------------------
# Healthcheck / Status Endpoint
# -------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    db_ok, msg = test_connection()
    return jsonify({
        "status": "online" if db_ok else "database_disconnected",
        "database": msg
    }), 200 if db_ok else 500

# -------------------------------------------------------------
# 1. CREATE A RESEARCH OPPORTUNITY (POST /api/opportunities)
# -------------------------------------------------------------
@app.route("/api/opportunities", methods=["POST"])
def create_opportunity():
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
# 2. RETRIEVE ALL RESEARCH OPPORTUNITIES (GET /api/opportunities)
# -------------------------------------------------------------
@app.route("/api/opportunities", methods=["GET"])
def get_all_opportunities():
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
# 3. RETRIEVE ONE RESEARCH OPPORTUNITY (GET /api/opportunities/:id)
# -------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["GET"])
def get_opportunity(opp_id):
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
# 4. UPDATE A RESEARCH OPPORTUNITY (PUT /api/opportunities/:id)
# -------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["PUT"])
def update_opportunity(opp_id):
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
# 5. DELETE A RESEARCH OPPORTUNITY (DELETE /api/opportunities/:id)
# -------------------------------------------------------------
@app.route("/api/opportunities/<int:opp_id>", methods=["DELETE"])
def delete_opportunity(opp_id):
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
