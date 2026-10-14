# Research Opportunity Portal

**Assignment No. 1 — Computer Networks (Fall 2026)**  
**FAST-NUCES, Peshawar Campus — BS Computer Science (5B)**

---

## 🔗 GitHub Repository

> **https://github.com/p240575/research-opportunity-portal**  
> *(Replace with your actual GitHub link after pushing)*

---

## 📹 Demonstration Video

> **[Watch 1-Minute Demo](#)**  
> *(Replace `#` with your video link — YouTube, Google Drive, or Loom)*

---

## 📌 About

A full-stack web portal where faculty post research opportunities and students browse them. Built with **Flask** (Python) + **MySQL** + vanilla HTML/CSS/JS.

**Three roles:**
- **Visitor** — Browse & search (no login needed)
- **Faculty** — Register, login, manage own posts via dashboard
- **Admin** — Full control over all posts

---

## ⚙️ Prerequisites

- Python 3.10+
- MySQL 8.0+
- pip

---

## 🚀 Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/p240575/research-opportunity-portal.git
cd research-opportunity-portal
```

### 2. Set up the database
```bash
mysql -u root -p < database/schema.sql
```

### 3. Configure environment variables
```bash
cp .env.example .env
```
Open `.env` and fill in your MySQL credentials:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=research_portal
SECRET_KEY=any_random_string
```

### 4. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the server
```bash
python backend/app.py
```

### 6. Open in browser
```
http://127.0.0.1:5000
```

---

## 🗂️ Project Structure

```
├── backend/
│   ├── app.py          # Flask REST API & routes
│   └── db.py           # Database helpers & auth
├── database/
│   └── schema.sql      # MySQL schema + seed data
├── frontend/
│   ├── index.html      # Public portal
│   ├── faculty-dashboard.html
│   ├── admin-login.html
│   ├── faculty-login.html
│   ├── faculty-register.html
│   ├── 404.html
│   ├── app.js
│   └── style.css
├── ResearchPortal_API_Tests.postman_collection.json
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔑 Default Admin Login

| Field    | Value   |
|----------|---------|
| Username | `admin` |
| Password | *(set during first run — see terminal output)* |

Admin panel: `http://127.0.0.1:5000/admin/login`

---

## 🧪 API Testing

Import `ResearchPortal_API_Tests.postman_collection.json` into Postman.

The collection covers all 8 required scenarios:
1. Create 3 research opportunities
2. Retrieve all opportunities
3. Retrieve one by ID
4. Update an opportunity
5. Change status Open → Closed
6. Delete an opportunity
7. Request deleted opportunity → 404
8. Invalid data → 400 validation error

---

## 🛡️ Security Note

Never commit `.env` to GitHub. Real credentials are excluded via `.gitignore`.  
Use `.env.example` as a template only.
