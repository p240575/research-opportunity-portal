# University Research Opportunity Portal — Progress & Requirement Tracker

> **Course:** Computer Networks (CN) — BS (CS 5B), Fall-2026  
> **Institution:** National University of Computer & Emerging Sciences (FAST-NUCES), Peshawar Campus  
> **Assignment:** Assignment No. 1 — University Research Opportunity Portal  

---

## 📌 Quota Expiry & Session Resume Guide
If the AI assistant session ends or your usage quota expires, **open this file first**. It outlines every completed component, active tasks, and remaining steps so any new session can resume instantly without duplication.

To resume quickly:
1. Ensure MySQL is running: `sudo systemctl status mysql`.
2. Check Git log: `git log --oneline`.
3. Run server: `source venv/bin/activate && python3 backend/app.py`.
4. Portal URLs:
   - **Visitor Public Portal**: `http://127.0.0.1:5000/`
   - **Faculty Registration**: `http://127.0.0.1:5000/faculty/register`
   - **Faculty Login**: `http://127.0.0.1:5000/faculty/login`
   - **Faculty Dashboard**: `http://127.0.0.1:5000/faculty/dashboard`
   - **Administrator Login**: `http://127.0.0.1:5000/admin/login`

---

## 📊 Master Requirement Checklist

### Phase 1: Project Setup & Git Security [COMPLETED]
- [x] Initialized Git repository with proper structure (`main`/`master` branch).
- [x] Created comprehensive `.gitignore` preventing `.env`, credentials, secrets, virtual environments, and `node_modules` from entering Git.
- [x] Created `.env.example` template with placeholder values for secure credential handling.
- [x] Created `PROJECT_STATUS.md` tracking system.
- [x] Created comprehensive `README.md` with architecture overview, setup steps, and repository link placeholder.

### Phase 2: Database Schema & MySQL Setup [COMPLETED]
- [x] Created `database/schema.sql` defining:
  - Table `research_opportunities` with all 10 mandatory fields plus `faculty_id` foreign key.
  - Table `admins` for secure administrator credentials and authentication.
  - Table `faculty` for registered faculty members (`id`, `full_name`, `email`, `department`, `password_hash`, `is_active`, `created_at`).
  - Seed data with sample research opportunities and default admin account.
- [x] Automated schema migration via `init_admin_tables()` in `backend/db.py`.

### Phase 3: Three-Role Access Control (RBAC) & Ownership Security [COMPLETED]
- [x] **Role 1: Visitors (Public Read-Only)**:
  - Can view all published research opportunities via `GET /api/opportunities`.
  - Can view single opportunity details via `GET /api/opportunities/:id`.
  - Prohibited from creating, updating, or deleting any posts (`401 Unauthorized`).
- [x] **Role 2: Faculty Members (Self-Service CRUD on Own Posts)**:
  - Registration via `POST /api/faculty/register` with validation, duplicate email detection (`409 Conflict`), and scrypt password hashing.
  - Login via `POST /api/faculty/login` with session cookies and API Bearer tokens.
  - Logout via `POST /api/faculty/logout`.
  - Can create new opportunities via `POST /api/opportunities` (automatically tagged with `faculty_id`).
  - Personalized dashboard endpoint `GET /api/faculty/opportunities` showing only their own opportunities.
  - **Backend Ownership Verification**:
    - Can update only their own opportunities (`PUT /api/opportunities/:id`). Attempts to edit other faculty posts return `403 Forbidden`.
    - Can delete only their own opportunities (`DELETE /api/opportunities/:id`). Attempts to delete other faculty posts return `403 Forbidden`.
- [x] **Role 3: Administrator (Global Portal Management)**:
  - Dedicated admin authentication via `POST /api/auth/login`.
  - Full authority to create, view, modify, and delete any opportunity across the entire portal regardless of creator.
- [x] **Backend REST API Security & Route Guards**:
  - `@admin_required` and `@faculty_or_admin_required` decorators.
  - Token and session-based authentication support.
  - Standardized JSON responses with proper HTTP status codes (`200`, `201`, `400`, `401`, `403`, `404`, `409`, `422`).

### Phase 4: Frontend Implementation [COMPLETED]
- [x] **Public Portal (`frontend/index.html` & `app.js`)**:
  - Live three-role detection and visual role banner ("Visitor", "Faculty Member", "Administrator").
  - Navigation links tailored per role:
    - Visitors see "Faculty Sign In" and "Admin Sign In".
    - Faculty see "My Dashboard" and "Logout".
    - Admins see "+ Post Opportunity" and "Logout".
  - Opportunity cards display "Faculty Post" / "FAST Official" badges and faculty account email.
- [x] **Faculty Registration Page (`frontend/faculty-register.html`)**:
  - Responsive form with real-time password strength meter, password match confirmation, department dropdown, and error handling.
- [x] **Faculty Sign In Page (`frontend/faculty-login.html`)**:
  - Dedicated login interface with redirection to the Faculty Dashboard.
- [x] **Personalized Faculty Dashboard (`frontend/faculty-dashboard.html`)**:
  - Metrics cards (Total Opportunities, Open Positions, Active Postings).
  - List of faculty member's own postings with quick-action Edit and Delete modal flows.
  - "Post New Opportunity" modal with full validation.
  - Direct links back to public view and one-click logout.

### Phase 5: Verification & Automated Test Suite [COMPLETED]
- [x] Created `backend/test_rbac.py` verifying all 18 RBAC criteria:
  - Visitor read-only access and 401 blocks on mutation endpoints.
  - Faculty registration validation, duplicate email 409 rejection, and password security.
  - Faculty authentication, session issuance, and `/api/auth/status`.
  - Cross-faculty post isolation and backend 403 Forbidden checks on unauthorized PUT and DELETE.
  - Admin full authority and ability to modify/delete any faculty post.
  - Static frontend route availability (`/`, `/faculty/register`, `/faculty/login`, `/faculty/dashboard`, `/admin/login`).

---

## 📈 Git Commit History
1. `feat: initialize project structure with git security and status tracker`
2. `feat(db): add MySQL database schema and initial seed data`
3. `feat(api): implement REST API with CRUD endpoints and HTTP status codes`
4. `feat(ui): design modern responsive frontend with glassmorphism styling`
5. `feat(ui): connect frontend to REST API with full CRUD and validation`
6. `docs & test: add Postman collection for all 8 assignment scenarios and setup README`
7. `feat(security): implement RBAC with secure admin auth and public visitor read-only access`
8. `feat(rbac): implement faculty registration, authentication, ownership-based CRUD, and personalized dashboard`
