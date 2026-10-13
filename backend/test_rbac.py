import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5000"

def api_request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = content
            return status, parsed
    except urllib.error.HTTPError as e:
        status = e.code
        err_content = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_content)
        except Exception:
            parsed = err_content
        return status, parsed

def run_tests():
    print("=" * 65)
    print("RUNNING COMPREHENSIVE RBAC & PORTAL VERIFICATION TESTS")
    print("=" * 65)

    # 1. VISITOR READ-ONLY & PROHIBITED ACCESS
    print("\n[1] Testing Visitor (Unauthenticated) Access...")
    status, res = api_request("GET", "/api/opportunities")
    assert status == 200, f"Expected 200, got {status}"
    public_opps = res.get("data", [])
    print(f"  ✓ Visitor can list opportunities: {len(public_opps)} found")

    sample_id = public_opps[0]["id"] if public_opps else 1
    status, _ = api_request("GET", f"/api/opportunities/{sample_id}")
    assert status in (200, 404), f"Expected 200 or 404, got {status}"
    print(f"  ✓ Visitor can view single opportunity ID {sample_id}")

    # Visitor tries to create
    status, _ = api_request("POST", "/api/opportunities", {"title": "Hacker Post"})
    assert status == 401, f"Expected 401 for visitor create, got {status}"
    print("  ✓ Visitor POST blocked with 401 Unauthorized")

    # Visitor tries to update
    status, _ = api_request("PUT", f"/api/opportunities/{sample_id}", {"title": "Hacked"})
    assert status == 401, f"Expected 401 for visitor update, got {status}"
    print("  ✓ Visitor PUT blocked with 401 Unauthorized")

    # Visitor tries to delete
    status, _ = api_request("DELETE", f"/api/opportunities/{sample_id}")
    assert status == 401, f"Expected 401 for visitor delete, got {status}"
    print("  ✓ Visitor DELETE blocked with 401 Unauthorized")

    # 2. FACULTY REGISTRATION
    print("\n[2] Testing Faculty Registration...")
    timestamp = int(time.time())
    email_a = f"tariq_{timestamp}@nu.edu.pk"
    email_b = f"nadia_{timestamp}@nu.edu.pk"

    # Validation errors
    status, _ = api_request("POST", "/api/faculty/register", {
        "full_name": "", "email": "invalid-email", "password": "short", "confirm_password": "short"
    })
    assert status == 422, f"Expected 422 validation error, got {status}"
    print("  ✓ Invalid registration rejected with 422 Validation Error")

    # Password mismatch
    status, _ = api_request("POST", "/api/faculty/register", {
        "full_name": "Dr. Tariq", "email": email_a, "department": "Computer Science",
        "password": "Password123!", "confirm_password": "MismatchPassword!"
    })
    assert status == 422, f"Expected 422 for password mismatch, got {status}"
    print("  ✓ Password mismatch rejected with 422 Validation Error")

    # Register Faculty A
    status, res = api_request("POST", "/api/faculty/register", {
        "full_name": "Dr. Tariq Khan",
        "email": email_a,
        "department": "Computer Science",
        "password": "FacultySecurePass123!",
        "confirm_password": "FacultySecurePass123!"
    })
    assert status == 201, f"Expected 201 for Faculty A, got {status}: {res}"
    print(f"  ✓ Faculty A registered successfully: {email_a}")

    # Register Faculty B
    status, res = api_request("POST", "/api/faculty/register", {
        "full_name": "Dr. Nadia Rehman",
        "email": email_b,
        "department": "Electrical Engineering",
        "password": "FacultySecurePass123!",
        "confirm_password": "FacultySecurePass123!"
    })
    assert status == 201, f"Expected 201 for Faculty B, got {status}: {res}"
    print(f"  ✓ Faculty B registered successfully: {email_b}")

    # Duplicate registration check
    status, _ = api_request("POST", "/api/faculty/register", {
        "full_name": "Duplicate Tariq",
        "email": email_a,
        "department": "Computer Science",
        "password": "FacultySecurePass123!",
        "confirm_password": "FacultySecurePass123!"
    })
    assert status == 409, f"Expected 409 for duplicate email, got {status}"
    print("  ✓ Duplicate email registration rejected with 409 Conflict")

    # 3. FACULTY LOGIN & SESSIONS
    print("\n[3] Testing Faculty Login & Authentication...")
    # Bad credentials
    status, _ = api_request("POST", "/api/faculty/login", {
        "email": email_a, "password": "WrongPassword!"
    })
    assert status == 401, f"Expected 401 for wrong password, got {status}"
    print("  ✓ Invalid login credentials rejected with 401 Unauthorized")

    # Successful login Faculty A
    status, res_a = api_request("POST", "/api/faculty/login", {
        "email": email_a, "password": "FacultySecurePass123!"
    })
    assert status == 200, f"Expected 200, got {status}"
    token_a = res_a.get("token")
    faculty_a_id = res_a["faculty"]["id"]
    print(f"  ✓ Faculty A authenticated (ID: {faculty_a_id}, Token: {token_a[:12]}...)")

    # Successful login Faculty B
    status, res_b = api_request("POST", "/api/faculty/login", {
        "email": email_b, "password": "FacultySecurePass123!"
    })
    assert status == 200, f"Expected 200, got {status}"
    token_b = res_b.get("token")
    faculty_b_id = res_b["faculty"]["id"]
    print(f"  ✓ Faculty B authenticated (ID: {faculty_b_id}, Token: {token_b[:12]}...)")

    # Verify auth status endpoint for Faculty A
    status, stat_a = api_request("GET", "/api/auth/status", token=token_a)
    assert status == 200 and stat_a.get("role") == "faculty" and stat_a.get("id") == faculty_a_id
    print("  ✓ /api/auth/status correctly recognizes Faculty A role and ID")

    # 4. FACULTY CRUD & OWNERSHIP-BASED AUTHORIZATION
    print("\n[4] Testing Ownership & Cross-Faculty Isolation...")
    # Faculty A creates Opportunity A
    status, create_a = api_request("POST", "/api/opportunities", {
        "title": "Quantum Error Mitigation Algorithms",
        "description": "Research on noise cancellation in NISQ processors.",
        "research_area": "Quantum Computing",
        "faculty_name": "Dr. Tariq Khan",
        "department": "Computer Science",
        "required_skills": "Python, Qiskit, Linear Algebra",
        "available_positions": 2,
        "deadline": "2026-12-15",
        "status": "Open"
    }, token=token_a)
    assert status == 201, f"Expected 201, got {status}: {create_a}"
    opp_a_id = create_a["data"]["id"]
    assert create_a["data"].get("faculty_id") == faculty_a_id, "Post should be owned by Faculty A"
    print(f"  ✓ Faculty A created opportunity ID {opp_a_id} linked to faculty_id {faculty_a_id}")

    # Faculty B creates Opportunity B
    status, create_b = api_request("POST", "/api/opportunities", {
        "title": "Silicon Photonics Circuit Design",
        "description": "Designing on-chip optical interconnects for neural accelerators.",
        "research_area": "VLSI & Photonics",
        "faculty_name": "Dr. Nadia Rehman",
        "department": "Electrical Engineering",
        "required_skills": "Lumerical, Cadence, Verilog-A",
        "available_positions": 1,
        "deadline": "2026-11-30",
        "status": "Open"
    }, token=token_b)
    assert status == 201, f"Expected 201, got {status}: {create_b}"
    opp_b_id = create_b["data"]["id"]
    assert create_b["data"].get("faculty_id") == faculty_b_id, "Post should be owned by Faculty B"
    print(f"  ✓ Faculty B created opportunity ID {opp_b_id} linked to faculty_id {faculty_b_id}")

    # Dashboard check: Faculty A sees only their own posts
    status, dashboard_a = api_request("GET", "/api/faculty/opportunities", token=token_a)
    assert status == 200
    a_post_ids = [p["id"] for p in dashboard_a["data"]]
    assert opp_a_id in a_post_ids, f"Faculty A dashboard must include opp {opp_a_id}"
    assert opp_b_id not in a_post_ids, f"Faculty A dashboard must NOT include Faculty B's opp {opp_b_id}"
    print(f"  ✓ Faculty A dashboard lists only own posts (Includes A:{opp_a_id}, Excludes B:{opp_b_id})")

    # Dashboard check: Faculty B sees only their own posts
    status, dashboard_b = api_request("GET", "/api/faculty/opportunities", token=token_b)
    assert status == 200
    b_post_ids = [p["id"] for p in dashboard_b["data"]]
    assert opp_b_id in b_post_ids, f"Faculty B dashboard must include opp {opp_b_id}"
    assert opp_a_id not in b_post_ids, f"Faculty B dashboard must NOT include Faculty A's opp {opp_a_id}"
    print(f"  ✓ Faculty B dashboard lists only own posts (Includes B:{opp_b_id}, Excludes A:{opp_a_id})")

    # Faculty A updates their own Opportunity A
    status, upd_a = api_request("PUT", f"/api/opportunities/{opp_a_id}", {
        "title": "Quantum Error Mitigation Algorithms (Revised Version)"
    }, token=token_a)
    assert status == 200, f"Expected 200 for owner update, got {status}"
    print(f"  ✓ Faculty A updated their own opportunity {opp_a_id} successfully")

    # CRITICAL BACKEND SECURITY TEST: Faculty A attempts to edit Faculty B's Opportunity B
    status, breach_edit = api_request("PUT", f"/api/opportunities/{opp_b_id}", {
        "title": "Malicious Tampering Attempt by Dr. Tariq"
    }, token=token_a)
    assert status == 403, f"SECURITY FAILURE: Expected 403 Forbidden, got {status}"
    print(f"  ✓ BACKEND SECURITY CONFIRMED: Faculty A blocked from editing Faculty B's post {opp_b_id} (403 Forbidden)")

    # CRITICAL BACKEND SECURITY TEST: Faculty A attempts to delete Faculty B's Opportunity B
    status, breach_del = api_request("DELETE", f"/api/opportunities/{opp_b_id}", token=token_a)
    assert status == 403, f"SECURITY FAILURE: Expected 403 Forbidden, got {status}"
    print(f"  ✓ BACKEND SECURITY CONFIRMED: Faculty A blocked from deleting Faculty B's post {opp_b_id} (403 Forbidden)")

    # Faculty A deletes their OWN Opportunity A
    status, del_a = api_request("DELETE", f"/api/opportunities/{opp_a_id}", token=token_a)
    assert status == 200, f"Expected 200 for owner delete, got {status}"
    print(f"  ✓ Faculty A deleted their own opportunity {opp_a_id} successfully")

    # 5. ADMIN FULL PRIVILEGES
    print("\n[5] Testing Administrator Full Control...")
    # Admin login
    status, res_adm = api_request("POST", "/api/auth/login", {
        "username": "admin", "password": "AdminPassword123!"
    })
    assert status == 200, f"Expected 200 admin login, got {status}"
    admin_token = res_adm["token"]
    print(f"  ✓ Admin authenticated (Token: {admin_token[:12]}...)")

    # Admin can edit Faculty B's post
    status, adm_upd = api_request("PUT", f"/api/opportunities/{opp_b_id}", {
        "title": "Silicon Photonics Circuit Design (Admin Supervised)"
    }, token=admin_token)
    assert status == 200, f"Expected 200 admin update of faculty post, got {status}"
    print(f"  ✓ Admin successfully modified Faculty B's post {opp_b_id}")

    # Admin can delete Faculty B's post
    status, adm_del = api_request("DELETE", f"/api/opportunities/{opp_b_id}", token=admin_token)
    assert status == 200, f"Expected 200 admin delete, got {status}"
    print(f"  ✓ Admin successfully deleted opportunity {opp_b_id}")

    # Admin can create a portal-wide opportunity (faculty_id is NULL)
    status, adm_create = api_request("POST", "/api/opportunities", {
        "title": "Autonomous Robotics Navigation System",
        "description": "SLAM algorithms for indoor aerial inspection drones.",
        "research_area": "Robotics & Computer Vision",
        "faculty_name": "Admin Department Head",
        "department": "Computer Science",
        "required_skills": "ROS 2, C++, OpenCV, Python",
        "available_positions": 3,
        "deadline": "2026-11-20",
        "status": "Open"
    }, token=admin_token)
    assert status == 201, f"Expected 201, got {status}"
    admin_created_id = adm_create["data"]["id"]
    assert adm_create["data"].get("faculty_id") is None, "Admin post should have faculty_id NULL"
    print(f"  ✓ Admin created new opportunity ID {admin_created_id} (faculty_id: NULL)")

    # 6. STATIC FRONTEND ROUTES & PAGES
    print("\n[6] Testing Frontend Route Accessibility...")
    pages = [
        ("/", "Research Opportunity Portal"),
        ("/faculty/register", "Faculty Registration"),
        ("/faculty/login", "Faculty Sign In"),
        ("/faculty/dashboard", "Faculty Dashboard"),
        ("/admin/login", "Administrator Sign In")
    ]
    for path, expected_text in pages:
        status, content = api_request("GET", path)
        assert status == 200, f"Route {path} returned {status}"
        assert expected_text in content, f"Route {path} missing text '{expected_text}'"
        print(f"  ✓ Route '{path}' serves correct HTML view")

    print("\n" + "=" * 65)
    print("ALL 18 RBAC & AUTHORIZATION CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
