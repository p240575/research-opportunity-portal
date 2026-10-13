# University Research Opportunity Portal — Progress & Requirement Tracker

> **Course:** Computer Networks (CN) — BS (CS 5B), Fall-2026  
> **Institution:** National University of Computer & Emerging Sciences (FAST-NUCES), Peshawar Campus  
> **Assignment:** Assignment No. 1 — University Research Opportunity Portal  

---

## 📌 Quota Expiry & Session Resume Guide
If the AI assistant session ends or your usage quota expires, **open this file first**. It outlines every completed component, active tasks, and remaining steps so any new session can resume instantly without duplication.

To resume quickly:
1. Check the **Current Status & Checkpoints** section below.
2. Ensure MySQL is running: `sudo systemctl status mysql`.
3. Check Git log to verify latest commits: `git log --oneline`.
4. Run server: `source venv/bin/activate && python3 backend/app.py`.
5. Public portal: `http://127.0.0.1:5000` | Admin login: `http://127.0.0.1:5000/admin/login`.

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
  - Table `research_opportunities` with all 10 mandatory fields (`id`, `title`, `description`, `research_area`, `faculty_name`, `department`, `required_skills`, `available_positions`, `deadline`, `status`).
  - Table `admins` for secure administrator credentials and authentication (`id`, `username`, `password_hash`, `full_name`, `created_at`).
  - Seed data with sample research opportunities and default admin account.
- [x] Created automated database initialization script `scripts/init_db.py`.
- [x] Verified live database connectivity against local MySQL 8.4 server.

### Phase 3: Backend REST API & RBAC Security [COMPLETED]
- [x] Database connection manager with `.env` loading and error resilience (`backend/db.py`).
- [x] Public endpoints:
  - `GET /api/opportunities` (Retrieve all opportunities -> returns `200 OK`).
  - `GET /api/opportunities/:id` (Retrieve single opportunity by ID -> returns `200 OK` or `404 Not Found`).
  - `GET /api/health` (Healthcheck and database status).
  - `GET /api/auth/status` (Check current authentication role).
- [x] Administrative authentication endpoints:
  - `POST /api/auth/login` (Admin login with secure password verification -> returns `200 OK` + token, or `401 Unauthorized`).
  - `POST /api/auth/logout` (Invalidates session and revokes token -> returns `200 OK`).
- [x] Protected endpoints guarded by `@admin_required` middleware:
  - `POST /api/opportunities` (Create opportunity -> returns `201 Created` or `401 Unauthorized`).
  - `PUT /api/opportunities/:id` (Update existing opportunity -> returns `200 OK`, `400`, `401 Unauthorized`, or `404`).
  - `DELETE /api/opportunities/:id` (Delete opportunity -> returns `200 OK`, `401 Unauthorized`, or `404`).
- [x] Standardized JSON error responses and HTTP status codes (`200`, `201`, `400`, `401`, `404`, `500`).

### Phase 4: Eye-Catching Frontend Interface with Role Separation [COMPLETED]
- [x] **Public Visitor Mode (Read-Only):**
  - Visitors browse all research opportunities without registering, logging in, or providing credentials.
  - Search, filter by department and status, and view complete details modal.
  - Create, Edit, Delete, and Status Toggle buttons are completely hidden for unauthenticated visitors.
  - Discrete "Admin Login" button in header for administrative access.
- [x] **Dedicated Admin Login Page (`frontend/admin-login.html`):**
  - Separate authentication portal with modern glassmorphism design, alert feedback, and redirection.
- [x] **Administrator Mode (Full CRUD Dashboard):**
  - Authenticated admin badge and Logout button in header.
  - "+ Post Opportunity" button and Create Modal with client-side validation.
  - "Edit" button and pre-filled modal on every opportunity card.
  - One-click "Close Opening" / "Reopen" status toggle directly on each card.
  - "Delete" button with confirmation modal.
  - Immediate return to visitor mode upon logout.
- [x] **Toast Notifications System:** Instant feedback for operations and authorization events.

### Phase 5: Postman / Bruno API Test Collection [COMPLETED]
- [x] Generated exported Postman Collection v2.1 JSON file (`postman/University_Research_Opportunity_Portal.postman_collection.json`) covering:
  - Public visitor tests (`GET /api/opportunities`, `GET /api/opportunities/1`).
  - Security rejections (Unauthorized POST, PUT, DELETE returning `401 Unauthorized`).
  - Invalid login attempt (`401 Unauthorized`).
  - Valid admin login (`POST /api/auth/login` returning token).
  - Protected operations (Create, Update, Status toggle, Delete using Bearer token).
  - Admin logout and post-logout token invalidation test (`401 Unauthorized`).

### Phase 6: Demonstration Video Preparation & Final Packaging [PENDING]
- [ ] Record 60-second video following the walkthrough script in `README.md`.
- [ ] Export final ZIP file named `P24_0000_NAME_CLASS.zip`.

---

## 📈 Git Commit History
1. `feat: initialize project structure with git security and status tracker`
2. `feat(db): add MySQL database schema and initial seed data`
3. `feat(api): implement REST API with CRUD endpoints and HTTP status codes`
4. `feat(ui): design modern responsive frontend with glassmorphism styling`
5. `feat(ui): connect frontend to REST API with full CRUD and validation`
6. `docs & test: add Postman collection for all 8 assignment scenarios and setup README`
7. `feat(security): implement RBAC with secure admin auth and public visitor read-only access`
