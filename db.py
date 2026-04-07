import os
import sqlite3
import hashlib

DB_PATH = "parking.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${key.hex()}"


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS app_user (
          user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
          full_name      TEXT NOT NULL,
          email          TEXT NOT NULL UNIQUE,
          password_hash  TEXT NOT NULL,
          created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)


def create_user(full_name: str, email: str, password: str):
    password_hash = hash_password(password)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO app_user (full_name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (full_name, email, password_hash),
        )

# def find_user(full_name: str, email: str, password: str):
#     with get_connection() as conn:
#         conn.execute(
#             """
#             SELECT email, password FROM app_user
#             """
#         )