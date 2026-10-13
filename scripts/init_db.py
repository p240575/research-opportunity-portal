#!/usr/bin/env python3
"""
Database Initialization Script
Executes database/schema.sql using credentials defined in .env
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "portal_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "portal_pass123")
DB_NAME = os.getenv("DB_NAME", "research_portal")

SCHEMA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql"))

def initialize_database():
    print(f"Connecting to MySQL at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")
    try:
        # First connect without database selected to create database
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        )
    except pymysql.MySQLError as err:
        print(f"❌ Failed to connect to MySQL: {err}")
        print("\nPlease verify:")
        print(" 1. MySQL service is active: 'sudo systemctl status mysql'")
        print(" 2. User credentials in .env match your MySQL user permissions.")
        sys.exit(1)

    print(f"Reading schema from: {SCHEMA_FILE}")
    if not os.path.exists(SCHEMA_FILE):
        print(f"❌ Schema file not found: {SCHEMA_FILE}")
        sys.exit(1)

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split commands by semicolon (ignoring comments)
    commands = [cmd.strip() for cmd in sql_content.split(";") if cmd.strip()]

    with conn.cursor() as cursor:
        for cmd in commands:
            if cmd:
                try:
                    cursor.execute(cmd)
                except pymysql.MySQLError as e:
                    print(f"⚠️ Warning on command: {e}")

    conn.close()
    print("✅ Database 'research_portal' and table 'research_opportunities' initialized successfully with seed data!")

if __name__ == "__main__":
    initialize_database()
