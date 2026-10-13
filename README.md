# University Research Opportunity Portal

[![Course](https://img.shields.io/badge/Course-Computer%20Networks-blue)](https://www.nu.edu.pk/)
[![Semester](https://img.shields.io/badge/Semester-Fall%202026-green)](https://www.nu.edu.pk/)
[![Database](https://img.shields.io/badge/Database-MySQL%208.4-orange)](https://www.mysql.com/)
[![Backend](https://img.shields.io/badge/Backend-Python%20%2F%20Flask-black)](https://flask.palletsprojects.com/)

> **Assignment No. 1 — University Research Opportunity Portal**  
> **Course:** Computer Networks (BS CS 5B)  
> **Institution:** National University of Computer & Emerging Sciences (FAST-NUCES), Peshawar Campus  

---

## 📌 GitHub Repository
* **Repository Link:** `https://github.com/username/research-opportunity-portal` *(Replace with your actual GitHub repository URL before submission)*

> **Security Note:** In strict compliance with assignment guidelines, no database passwords, API keys, `.env` files, personal access tokens, or private credentials are committed to this repository. All sensitive parameters are configured via `.env` which is ignored by `.gitignore`.

---

## 📖 Scenario & Project Overview
University research opportunities are traditionally fragmented across disparate noticeboards, emails, and WhatsApp groups, causing students to miss deadlines and professors to struggle with opening management. 

This full-stack application provides a centralized web portal where faculty members can create, inspect, update, and manage research openings. It comprises:
1. **Relational Database (MySQL):** Stores research openings with 10 mandatory attributes and persistence guarantees.
2. **REST API (Flask):** Complete CRUD endpoints with rigorous HTTP status codes (`200`, `201`, `400`, `404`, `500`) and input validation.
3. **Responsive Frontend UI:** Modern dark glassmorphic dashboard with live search, filters, metrics, status toggling, and interactive modals.
4. **Postman Collection:** Ready-to-import API test suite covering all 8 assignment verification scenarios.

---

## 🛠️ Technology Stack
* **Backend:** Python 3.14 / Flask, Flask-CORS, PyMySQL, Cryptography, python-dotenv
* **Database:** MySQL 8.4
* **Frontend:** Semantic HTML5, Vanilla CSS3 (Custom Glassmorphism Design System), Modern JavaScript (Fetch API)
* **Testing:** Postman / Bruno (Collection v2.1)
* **Version Control:** Git

---

## 🗄️ Database Schema & Data Model
Each research opportunity record contains the following 10 mandatory fields:
1. `id` (`INT AUTO_INCREMENT PRIMARY KEY`)
2. `title` (`VARCHAR(255)`): Title of the research project
3. `description` (`TEXT`): Full overview and objectives
4. `research_area` (`VARCHAR(150)`): Field of study (e.g., Computer Networks, Cybersecurity, AI)
5. `faculty_name` (`VARCHAR(150)`): Supervising professor
6. `department` (`VARCHAR(100)`): Academic department
7. `required_skills` (`TEXT`): Required technical prerequisites
8. `available_positions` (`INT`): Number of student seats
9. `deadline` (`DATE`): Application closing date (`YYYY-MM-DD`)
10. `status` (`ENUM('Open', 'Closed')`): Current status of the opening

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
Open `.env` and set your MySQL credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=portal_user
DB_PASSWORD=portal_pass123
DB_NAME=research_portal
PORT=5000
```

### 4. Initialize Database
You can initialize the MySQL database using either the automated script or the direct SQL schema file:

**Option A — Automated Script:**
```bash
python3 scripts/init_db.py
```

**Option B — Direct MySQL CLI:**
```bash
sudo mysql < database/schema.sql
```

*(If you need to create a dedicated user for MySQL:)*
```sql
CREATE USER IF NOT EXISTS 'portal_user'@'localhost' IDENTIFIED BY 'portal_pass123';
GRANT ALL PRIVILEGES ON research_portal.* TO 'portal_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Run the Application
Activate the virtual environment and start the Flask server:
```bash
source venv/bin/activate
python3 backend/app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📡 REST API Reference

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| **`POST`** | `/api/opportunities` | Create and persist a new opportunity | `201 Created`, `400 Bad Request` |
| **`GET`** | `/api/opportunities` | Retrieve all stored opportunities | `200 OK`, `500 Error` |
| **`GET`** | `/api/opportunities/:id` | Retrieve single opportunity by ID | `200 OK`, `404 Not Found` |
| **`PUT`** | `/api/opportunities/:id` | Update opportunity fields or status | `200 OK`, `400 Bad Request`, `404 Not Found` |
| **`DELETE`**| `/api/opportunities/:id` | Delete opportunity permanently | `200 OK`, `404 Not Found` |
| **`GET`** | `/api/health` | Healthcheck & MySQL connectivity check | `200 OK`, `500 Disconnected` |

---

## 🧪 Postman & Bruno Testing

The exported collection is located at:
📁 `postman/University_Research_Opportunity_Portal.postman_collection.json`

### Import & Execute:
1. Open **Postman** or **Bruno**.
2. Click **Import** and select the JSON file from the `postman/` directory.
3. The collection is pre-configured with the `base_url` variable pointing to `http://127.0.0.1:5000`.
4. Run the requests sequentially to verify all 8 required scenarios:
   - Request 1, 2, 3: Create at least three research opportunities (`POST`).
   - Request 4: Retrieve all research opportunities (`GET`).
   - Request 5: Retrieve one research opportunity by ID (`GET`).
   - Request 6: Update an existing opportunity (`PUT`).
   - Request 7: Change opportunity status from Open to Closed (`PUT`).
   - Request 8: Delete an opportunity (`DELETE`).
   - Request 9: Request deleted opportunity again to demonstrate `404 Not Found`.
   - Request 10: Send missing/invalid payload to demonstrate `400 Bad Request` input validation.

---

## 🎥 1-Minute Demonstration Video Guide
The video must **not exceed 60 seconds**. Suggested timing:
* **0:00 - 0:10:** Show terminal with backend running & open web portal in browser.
* **0:10 - 0:25:** Fill form & click "Post Opportunity" (Create operation), verify card appears in grid.
* **0:25 - 0:35:** Click "Details" modal (Retrieve One), then click "Edit" or "Close Opportunity" toggle button (Update & Status Change).
* **0:35 - 0:45:** Click delete icon & confirm removal (Delete operation).
* **0:45 - 0:60:** Switch to Postman: Send invalid payload (`400 Bad Request`) and request non-existent ID (`404 Not Found`).

---

## 📦 Submission ZIP Packaging
Before submitting, package your repository as instructed:
```bash
# Example ZIP naming format: P24_0000_NAME_CLASS.zip
zip -r P24_0000_NAME_CLASS.zip . -x "venv/*" ".git/*" ".env" "__pycache__/*"
```
Ensure the ZIP contains:
* Complete backend and frontend source code
* `database/schema.sql`
* `postman/University_Research_Opportunity_Portal.postman_collection.json`
* `README.md`
* Link to 1-minute demonstration video
