import os
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "portal_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "portal_pass123")
DB_NAME = os.getenv("DB_NAME", "research_portal")

DEFAULT_ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "AdminPassword123!")

def get_db_connection():
    """
    Establishes and returns a connection to the MySQL database.
    Uses DictCursor so query rows are returned as Python dictionaries.
    """
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=DictCursor,
            autocommit=True,
            connect_timeout=5
        )
        return connection
    except pymysql.MySQLError as err:
        print(f"[Database Error] Connection failed: {err}")
        raise err

def test_connection():
    """Quick helper to verify database connectivity."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS test;")
            result = cursor.fetchone()
        conn.close()
        return True, "Database connection successful."
    except Exception as e:
        return False, str(e)

def init_admin_tables():
    """
    Ensures the 'admins' table exists in the database and seeds
    the default administrator account if none exists.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Create admins table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(150) DEFAULT 'Portal Administrator',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Check if default admin exists
            cursor.execute("SELECT id, username FROM admins WHERE username = %s;", (DEFAULT_ADMIN_USER,))
            existing_admin = cursor.fetchone()

            if not existing_admin:
                pwd_hash = generate_password_hash(DEFAULT_ADMIN_PASS)
                cursor.execute("""
                    INSERT INTO admins (username, password_hash, full_name)
                    VALUES (%s, %s, %s);
                """, (DEFAULT_ADMIN_USER, pwd_hash, "Portal Administrator"))
                print(f"[Database] Seeded default administrator account: '{DEFAULT_ADMIN_USER}'")
        conn.close()
        return True
    except Exception as e:
        print(f"[Database Warning] Could not initialize admins table: {e}")
        return False

def get_admin_by_username(username):
    """Fetches an admin record by username."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, password_hash, full_name FROM admins WHERE username = %s;", (username,))
            admin = cursor.fetchone()
        conn.close()
        return admin
    except Exception as e:
        print(f"[Database Error] Error fetching admin: {e}")
        return None

def verify_admin_credentials(username, password):
    """
    Verifies admin credentials using werkzeug secure password hashing.
    Returns (True, admin_dict) if valid, or (False, None) if invalid.
    """
    if not username or not password:
        return False, None
    admin = get_admin_by_username(username.strip())
    if not admin:
        return False, None
    if check_password_hash(admin["password_hash"], password):
        return True, {
            "id": admin["id"],
            "username": admin["username"],
            "full_name": admin.get("full_name") or "Administrator"
        }
    return False, None
