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
4. Proceed with the next unchecked `[ ]` item in the **Master Requirement Checklist**.

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
  - Database `research_portal`
  - Table `research_opportunities` with all 10 mandatory fields:
    1. `id` (`INT AUTO_INCREMENT PRIMARY KEY`)
    2. `title` (`VARCHAR(255)`)
    3. `description` (`TEXT`)
    4. `research_area` (`VARCHAR(150)`)
    5. `faculty_name` (`VARCHAR(150)`)
    6. `department` (`VARCHAR(100)`)
    7. `required_skills` (`TEXT`)
    8. `available_positions` (`INT`)
    9. `deadline` (`DATE`)
    10. `status` (`ENUM('Open', 'Closed') DEFAULT 'Open'`)
    - Timestamps (`created_at`, `updated_at`) and performance indexes.
- [x] Included 3 realistic seed data records covering AI, Networks/SDN, and Cybersecurity.
- [x] Created automated database initialization script `scripts/init_db.py`.

### Phase 3: Backend REST API [COMPLETED]
- [x] Built database connection manager with `.env` loading and error resilience (`backend/db.py`).
- [x] Implemented `POST /api/opportunities` (Create opportunity with full field validation -> returns `201 Created` or `400 Bad Request`).
- [x] Implemented `GET /api/opportunities` (Retrieve all opportunities -> returns `200 OK`).
- [x] Implemented `GET /api/opportunities/:id` (Retrieve single opportunity by ID -> returns `200 OK` or `404 Not Found`).
- [x] Implemented `PUT /api/opportunities/:id` (Update existing opportunity -> returns `200 OK`, `400 Bad Request`, or `404 Not Found`).
- [x] Implemented `DELETE /api/opportunities/:id` (Delete opportunity by ID -> returns `200 OK` or `404 Not Found`).
- [x] Implemented standardized JSON error responses and HTTP status codes (`200`, `201`, `400`, `404`, `500`).
- [x] Added `/api/health` endpoint for dynamic connection monitoring.

### Phase 4: Eye-Catching Frontend Interface [COMPLETED]
- [x] Modern, responsive web portal UI with premium dark glassmorphism design system (`frontend/index.html`, `frontend/style.css`).
- [x] **Live Metrics Dashboard:** Total openings, Open openings, Available seats, Active departments.
- [x] **Research Opportunities Grid:** Glassmorphism cards with department badges, glowing status pills, deadlines, positions, and skill chips.
- [x] **Detail Modal:** In-depth view showing complete research description, supervisor details, and requirements.
- [x] **Create Opportunity Modal:** Clean interactive form with client-side field validation and clear error hints.
- [x] **Edit Opportunity Modal:** Pre-filled edit form with full field editing capability.
- [x] **One-Click Quick Status Toggle:** Toggle between `Open` and `Closed` directly from the card.
- [x] **Delete with Confirmation:** Clean modal prompt before removing an entry from the database.
- [x] **Toast Notification System:** Instant animated feedback for success (created, updated, deleted) and API errors.
- [x] **Search & Real-time Filtering:** Search by keyword, filter by status, filter by department.

### Phase 5: Postman / Bruno API Test Collection [COMPLETED]
- [x] Generated exported Postman Collection v2.1 JSON file (`postman/University_Research_Opportunity_Portal.postman_collection.json`) covering:
  1. `POST` Create opportunity #1
  2. `POST` Create opportunity #2
  3. `POST` Create opportunity #3
  4. `GET` Retrieve all opportunities
  5. `GET` Retrieve opportunity by ID
  6. `PUT` Update an existing opportunity
  7. `PUT` Change status from `Open` to `Closed`
  8. `DELETE` Delete an opportunity
  9. `GET` Verify deleted opportunity returns `404 Not Found`
  10. `POST` Send invalid/missing data to verify `400 Bad Request`

### Phase 6: Demonstration Video Preparation & Final Packaging [PENDING]
- [ ] Record 60-second video following the walkthrough script in `README.md`.
- [ ] Export final ZIP file named `P24_0000_NAME_CLASS.zip`.

---

## 📈 Git Commit History (Planned & In Progress)
1. `feat: initialize project structure with git security and status tracker`
2. `feat(db): add MySQL database schema and initial seed data`
3. `feat(api): implement REST API with CRUD endpoints and HTTP status codes`
4. `feat(ui): design modern responsive frontend with glassmorphism styling`
5. `feat(ui): connect frontend to REST API with full CRUD and validation`
6. `test: add exported Postman collection for all assignment scenarios`
7. `docs: add comprehensive README with setup instructions and submission guide`
