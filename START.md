# 🚀 How to Run After Restart

## Step 1 — Start MySQL
```bash
sudo systemctl start mysql
```

## Step 2 — Go to project folder
```bash
cd ~/project
```

## Step 3 — Activate Python virtual environment
```bash
source venv/bin/activate
```

## Step 4 — Create `.env` if it doesn't exist yet
```bash
cp .env.example .env
# Then open .env and fill in your actual DB credentials
```

## Step 5 — Run the backend server
```bash
cd backend
python app.py
```

## Done ✅
Open your browser at: **http://localhost:5000**  
Admin login page: **http://localhost:5000/admin/login**

---

## To stop the server
Press `Ctrl + C` in the terminal.
