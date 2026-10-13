# University Research Opportunity Portal

[![Course](https://img.shields.io/badge/Course-Computer%20Networks-blue)](https://www.nu.edu.pk/)
[![Semester](https://img.shields.io/badge/Semester-Fall%202026-green)](https://www.nu.edu.pk/)
[![Database](https://img.shields.io/badge/Database-MySQL%208.4-orange)](https://www.mysql.com/)
[![Backend](https://img.shields.io/badge/Backend-Python%20%2F%20Flask-black)](https://flask.palletsprojects.com/)
[![Security](https://img.shields.io/badge/Auth-RBAC%20%26%20Session%20Tokens-purple)](https://flask.palletsprojects.com/)

> **Assignment No. 1 — University Research Opportunity Portal**  
> **Course:** Computer Networks (BS CS 5B)  
> **Institution:** National University of Computer & Emerging Sciences (FAST-NUCES), Peshawar Campus  

---

## 📌 GitHub Repository
* **Repository Link:** `https://github.com/username/research-opportunity-portal` *(Replace with your actual GitHub repository URL before submission)*

> **Security Note:** In strict compliance with assignment guidelines, no database passwords, API keys, `.env` files, personal access tokens, or private credentials are committed to this repository. All sensitive parameters are configured via `.env` which is ignored by `.gitignore`.

---

## 📖 Scenario & Access Control Architecture

University research opportunities are traditionally fragmented across disparate noticeboards, emails, and WhatsApp groups, causing students to miss deadlines and professors to struggle with opening management. 

This full-stack application provides a centralized web portal with strict **Role-Based Access Control (RBAC)**:

### 1. Public Visitor Access (Read-Only)
* **Zero Barrier to Entry:** Visitors can open the portal, search, filter, and view complete research details **without registering, logging in, or providing credentials**.
* **Protected Views:** The Create, Edit, and Delete controls are completely hidden from visitors on the user interface.
* **Backend Enforced:** Any direct attempt to call Create/Update/Delete endpoints from a browser console, Postman, or curl without valid authentication is rejected with **`HTTP 401 Unauthorized`**.

### 2. Administrator Access (Full CRUD)
* **Dedicated Admin Login:** Administrators authenticate via a separate login page at `/admin/login`.
* **Administrative Controls:** Once authenticated, the admin can create new research openings, edit existing records, toggle status between Open and Closed, and permanently delete opportunities.
* **Session Invalidation:** Logging out terminates the session and revokes the active token, returning the user to read-only visitor mode.

---

## 🛠️ Technology Stack
* **Backend:** Python 3.14 / Flask, Flask-CORS, PyMySQL, Cryptography, python-dotenv, Werkzeug Security (Scrypt password hashing)
* **Database:** MySQL 8.4
* **Frontend:** Semantic HTML5, Vanilla CSS3 (Custom Glassmorphism Design System), Modern JavaScript (Fetch API, RBAC controller)
* **Testing:** Postman / Bruno (Collection v2.1 with public, security, and administrative test suites)
* **Version Control:** Git

---

## 🗄️ Database Schema & Data Models

### 1. `research_opportunities` Table
Each opportunity contains the 10 mandatory fields:
1. `id` (`INT AUTO_INCREMENT PRIMARY KEY`)
2. `title` (`VARCHAR(255)`): Research project title
3. `description` (`TEXT`): Overview, student responsibilities, and objectives
4. `research_area` (`VARCHAR(150)`): Discipline (e.g. Computer Networks, Cybersecurity, AI)
5. `faculty_name` (`VARCHAR(150)`): Supervising professor
6. `department` (`VARCHAR(100)`): Academic department
7. `required_skills` (`TEXT`): Technical prerequisites
8. `available_positions` (`INT`): Student seat count
9. `deadline` (`DATE`): Application cutoff date (`YYYY-MM-DD`)
10. `status` (`ENUM('Open', 'Closed')`): Current listing status

### 2. `admins` Table (Authentication)
* `id` (`INT AUTO_INCREMENT PRIMARY KEY`)
* `username` (`VARCHAR(100) UNIQUE NOT NULL`)
* `password_hash` (`VARCHAR(255) NOT NULL`): Cryptographically hashed using PBKDF2/Scrypt
* `full_name` (`VARCHAR(150)`): Administrator display name
* `created_at` (`TIMESTAMP DEFAULT CURRENT_TIMESTAMP`)

**Default Seeded Administrator Credentials:**
* **Username:** `admin`
* **Password:** `AdminPassword123!` *(Configurable via environment variables)*

---

## 🚀 Getting Started & Setup Instructions

### 1. Prerequisites
Ensure the following tools are installed on your system:
* Python 3.10+ (`python3 --version`)
* MySQL Server (`sudo systemctl status mysql`)
* Git (`git --version`)

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/username/research-opportunity-portal.git
cd research-opportunity-portal

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to create your local `.env` configuration:
```bash
cp .env.example .env
```
Ensure `.env` matches your MySQL database configuration:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=portal_user
DB_PASSWORD=portal_pass123
DB_NAME=research_portal
PORT=5000
SECRET_KEY=fast_nuces_secure_session_secret_2026
ADMIN_USERNAME=admin
ADMIN_PASSWORD=AdminPassword123!
```

### 4. Initialize Database
Initialize the database and tables using MySQL CLI:
```bash
sudo mysql < database/schema.sql
```

*(Or use the automated Python initializer:)*
```bash
python3 scripts/init_db.py
```

### 5. Run the Application
Start the Flask server:
```bash
source venv/bin/activate
python3 backend/app.py
```
Open your browser and navigate to:
* **Public Visitor Portal (Read-Only):** `http://127.0.0.1:5000/`
* **Dedicated Admin Login:** `http://127.0.0.1:5000/admin/login`

---

## 📡 REST API Reference

| Method | Endpoint | Access Level | Description | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| **`GET`** | `/api/opportunities` | **Public** | Retrieve all opportunities | `200 OK`, `500 Error` |
| **`GET`** | `/api/opportunities/:id` | **Public** | Retrieve single opportunity details | `200 OK`, `404 Not Found` |
| **`GET`** | `/api/health` | **Public** | Healthcheck & MySQL status | `200 OK`, `500 Error` |
| **`GET`** | `/api/auth/status` | **Public** | Check current session role | `200 OK` |
| **`POST`** | `/api/auth/login` | **Public** | Authenticate administrator | `200 OK`, `400 Bad Request`, `401 Unauthorized` |
| **`POST`** | `/api/auth/logout` | **Admin** | Invalidate administrator session | `200 OK` |
| **`POST`** | `/api/opportunities` | **Admin Only** | Create a new research opening | `201 Created`, `400 Bad Request`, `401 Unauthorized` |
| **`PUT`** | `/api/opportunities/:id` | **Admin Only** | Update opportunity or toggle status | `200 OK`, `400 Bad Request`, `401 Unauthorized`, `404 Not Found` |
| **`DELETE`**| `/api/opportunities/:id` | **Admin Only** | Delete an opportunity | `200 OK`, `401 Unauthorized`, `404 Not Found` |

---

## 🧪 Postman & Bruno Testing

The exported collection is located at:
📁 `postman/University_Research_Opportunity_Portal.postman_collection.json`

### Test Suite Structure:
1. **Public Access (Visitor):**
   - Retrieve all opportunities (`200 OK`).
   - Retrieve single opportunity (`200 OK`).
   - Auth status verification (`authenticated: false, role: "visitor"`).
2. **Security & Authorization Enforcement:**
   - Unauthenticated `POST` rejected with `401 Unauthorized`.
   - Unauthenticated `PUT` rejected with `401 Unauthorized`.
   - Unauthenticated `DELETE` rejected with `401 Unauthorized`.
   - Invalid admin credentials rejected with `401 Unauthorized`.
3. **Admin Authentication:**
   - Valid login (`200 OK`) and automatic capture of `admin_token`.
   - Verify authenticated status (`authenticated: true, role: "administrator"`).
4. **Protected Administrative Operations:**
   - Create opportunities with Bearer token (`201 Created`).
   - Update opportunity with Bearer token (`200 OK`).
   - Toggle status Open $\rightarrow$ Closed (`200 OK`).
   - Delete opportunity (`200 OK`).
   - Field validation failure check (`400 Bad Request`).
   - Missing resource check (`404 Not Found`).
5. **Logout & Session Revocation:**
   - Admin logout (`200 OK`).
   - Attempting operation with revoked token rejected with `401 Unauthorized`.

---

## 🎥 1-Minute Demonstration Video Guide (Max 60s)
1. **0:00 - 0:15:** Open public portal (`http://127.0.0.1:5000`). Show that visitors see all research openings and "View Details" without needing any login or registration. Point out that Create, Edit, and Delete buttons are absent.
2. **0:15 - 0:25:** Click "Admin Login" in the header to open `/admin/login`. Log in as `admin`. Show the UI updating to Administrator Mode with "+ Post Opportunity", Edit, Delete, and Status Toggle buttons visible.
3. **0:25 - 0:40:** Create an opportunity, toggle status from Open to Closed, and delete a listing.
4. **0:40 - 0:50:** Click "Logout". Demonstrate that the UI immediately reverts to visitor read-only mode.
5. **0:50 - 0:60:** Switch to Postman: Show public `GET` succeeding with `200 OK`, and unauthorized `POST` rejected with `401 Unauthorized`.

---

## 📦 Submission ZIP Packaging
Package the assignment repository:
```bash
zip -r P24_0000_NAME_CLASS.zip . -x "venv/*" ".git/*" ".env" "__pycache__/*"
```
Ensure the ZIP contains:
* Complete backend and frontend source code
* `database/schema.sql`
* `postman/University_Research_Opportunity_Portal.postman_collection.json`
* `README.md`
* Link to 1-minute demonstration video
