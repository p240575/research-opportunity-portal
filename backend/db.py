import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "portal_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "portal_pass123")
DB_NAME = os.getenv("DB_NAME", "research_portal")

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
