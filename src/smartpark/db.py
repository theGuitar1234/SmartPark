import os
import sqlite3
import hashlib
import hmac
import re


DB_PATH = "data/parking.db"
DATA_DIR = "data"


def get_connection():
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)

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
            200_000,
        )

        return hmac.compare_digest(new_key.hex(), stored_key_hex)
    except Exception:
        return False


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            password    TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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


def authenticate_user(email: str, password: str):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT user_id, full_name, email, password
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

    if not user:
        return None

    if verify_password(password, user["password"]):
        return {
            "user_id": user["user_id"],
            "full_name": user["full_name"],
            "email": user["email"],
        }

    return None


def update_user(user_id: int, full_name: str, email: str, new_password: str = None):
    with get_connection() as conn:
        if not re.match("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$", email):
            raise ValueError("Email Validation Failed")
        
        if new_password:
            password_hash = hash_password(new_password)
            conn.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?, password = ?
                WHERE user_id = ?
                """,
                (full_name, email, password_hash, user_id),
            )
        else:
            conn.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?
                WHERE user_id = ?
                """,
                (full_name, email, user_id),
            )