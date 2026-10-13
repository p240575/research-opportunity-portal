import os
import pymysql
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_USER     = os.getenv("DB_USER", "portal_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "portal_pass123")
DB_NAME     = os.getenv("DB_NAME", "research_portal")

DEFAULT_ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "AdminPassword123!")

# ---------------------------------------------------------------------------
# Core connection helper
# ---------------------------------------------------------------------------
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
            cursor.fetchone()
        conn.close()
        return True, "Database connection successful."
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------------------------
# Admin table initialisation & helpers
# ---------------------------------------------------------------------------
def init_admin_tables():
    """
    Ensures the admins & faculty tables exist, then seeds the default
    administrator account and adds the faculty_id FK to research_opportunities
    if it is not already present.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # --- admins table ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(150) DEFAULT 'Portal Administrator',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Seed default admin if absent
            cursor.execute("SELECT id FROM admins WHERE username = %s;", (DEFAULT_ADMIN_USER,))
            if not cursor.fetchone():
                pwd_hash = generate_password_hash(DEFAULT_ADMIN_PASS)
                cursor.execute(
                    "INSERT INTO admins (username, password_hash, full_name) VALUES (%s, %s, %s);",
                    (DEFAULT_ADMIN_USER, pwd_hash, "Portal Administrator")
                )
                print(f"[Database] Seeded default administrator: '{DEFAULT_ADMIN_USER}'")

            # --- faculty table ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faculty (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(150) NOT NULL,
                    email VARCHAR(200) NOT NULL UNIQUE,
                    department VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # --- Add faculty_id column to research_opportunities if missing ---
            cursor.execute("""
                SELECT COUNT(*) AS cnt
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name   = 'research_opportunities'
                  AND column_name  = 'faculty_id';
            """, (DB_NAME,))
            row = cursor.fetchone()
            if not row or row["cnt"] == 0:
                cursor.execute("""
                    ALTER TABLE research_opportunities
                    ADD COLUMN faculty_id INT DEFAULT NULL
                    AFTER status;
                """)
                print("[Database] Added faculty_id column to research_opportunities.")

            # Add FK if not already present
            cursor.execute("""
                SELECT COUNT(*) AS cnt
                FROM information_schema.key_column_usage
                WHERE table_schema   = %s
                  AND table_name     = 'research_opportunities'
                  AND constraint_name = 'fk_opp_faculty';
            """, (DB_NAME,))
            fk = cursor.fetchone()
            if not fk or fk["cnt"] == 0:
                try:
                    cursor.execute("""
                        ALTER TABLE research_opportunities
                        ADD CONSTRAINT fk_opp_faculty
                        FOREIGN KEY (faculty_id) REFERENCES faculty(id)
                        ON DELETE SET NULL;
                    """)
                    print("[Database] Added FK fk_opp_faculty.")
                except Exception:
                    pass   # FK may already exist under a different name; safe to skip

        conn.close()
        return True
    except Exception as e:
        print(f"[Database Warning] Could not initialise tables: {e}")
        return False

# ---------------------------------------------------------------------------
# Admin credential helpers
# ---------------------------------------------------------------------------
def get_admin_by_username(username):
    """Fetches an admin record by username."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password_hash, full_name FROM admins WHERE username = %s;",
                (username,)
            )
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
            "id":        admin["id"],
            "username":  admin["username"],
            "full_name": admin.get("full_name") or "Administrator"
        }
    return False, None

# ---------------------------------------------------------------------------
# Faculty account helpers
# ---------------------------------------------------------------------------
def get_faculty_by_email(email):
    """Fetches a faculty record by email."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, full_name, email, department, password_hash, is_active FROM faculty WHERE email = %s;",
                (email.strip().lower(),)
            )
            member = cursor.fetchone()
        conn.close()
        return member
    except Exception as e:
        print(f"[Database Error] Error fetching faculty: {e}")
        return None

def register_faculty(full_name, email, department, password):
    """
    Creates a new faculty account.
    Returns (True, faculty_dict) on success, or (False, error_message) on failure.
    """
    try:
        email = email.strip().lower()
        if get_faculty_by_email(email):
            return False, "An account with this email address already exists."

        pwd_hash = generate_password_hash(password)
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO faculty (full_name, email, department, password_hash)
                   VALUES (%s, %s, %s, %s);""",
                (full_name.strip(), email, department.strip(), pwd_hash)
            )
            new_id = cursor.lastrowid
            cursor.execute(
                "SELECT id, full_name, email, department FROM faculty WHERE id = %s;",
                (new_id,)
            )
            faculty_record = cursor.fetchone()
        conn.close()
        return True, faculty_record
    except Exception as e:
        print(f"[Database Error] Faculty registration failed: {e}")
        return False, str(e)

def verify_faculty_credentials(email, password):
    """
    Verifies faculty credentials.
    Returns (True, faculty_dict) if valid, or (False, None) if invalid.
    """
    if not email or not password:
        return False, None
    member = get_faculty_by_email(email)
    if not member:
        return False, None
    if not member.get("is_active"):
        return False, None
    if check_password_hash(member["password_hash"], password):
        return True, {
            "id":         member["id"],
            "full_name":  member["full_name"],
            "email":      member["email"],
            "department": member["department"]
        }
    return False, None
