import os
import sqlite3
import hashlib
import hmac

DB_PATH = "data/parking.db"
PATH = "data"


def get_connection():
    if not os.path.exists(PATH):
        os.mkdir(PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, stored_password: str) -> bool:
    try:
        salt_hex, stored_key_hex = stored_password.split("$")
        salt = bytes.fromhex(salt_hex)

        new_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            200_000
        )

        return hmac.compare_digest(new_key.hex(), stored_key_hex)
    except Exception:
        return False


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
          full_name      TEXT NOT NULL,
          email          TEXT NOT NULL UNIQUE,
          password       TEXT NOT NULL,
          created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)


def create_user(full_name: str, email: str, password: str):
    password_hash = hash_password(password)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (full_name, email, password)
            VALUES (?, ?, ?)
            """,
            (full_name, email, password_hash),
        )


def authenticate_user(email: str, password: str) -> bool:
    with get_connection() as conn:
        user = conn.execute(
            "SELECT password FROM users WHERE email = ?",
            (email,)
        ).fetchone()

    if not user:
        return False

    return verify_password(password, user["password"])