from pathlib import Path
import sqlite3
import hashlib
import hmac
import re
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "parking.db"

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email))


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)

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

            CREATE TABLE IF NOT EXISTS parking_slots (
                slot_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                zone        TEXT NOT NULL,
                slot_number TEXT NOT NULL,
                status      TEXT NOT NULL CHECK(status IN ('Available', 'Occupied', 'Reserved')),
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(zone, slot_number)
            );
            """)

        count = conn.execute("SELECT COUNT(*) AS total FROM parking_slots").fetchone()

        if count["total"] == 0:
            conn.executemany(
                """
                INSERT INTO parking_slots (zone, slot_number, status)
                VALUES (?, ?, ?)
                """,
                [
                    ("A", "A-01", "Occupied"),
                    ("A", "A-02", "Available"),
                    ("A", "A-03", "Available"),
                    ("B", "B-01", "Reserved"),
                    ("B", "B-02", "Occupied"),
                    ("C", "C-01", "Available"),
                ],
            )


def create_user(full_name: str, email: str, password: str):
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name:
        raise ValueError("Full name is required.")

    if not validate_email(email):
        raise ValueError("Email validation failed.")

    password_hash = hash_password(password)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (full_name, email, password)
            VALUES (?, ?, ?)
            """,
            (full_name, email, password_hash),
        )

        user_id = cursor.lastrowid

    return {
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
    }


def authenticate_user(email: str, password: str):
    email = email.strip().lower()

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


def get_user_by_id(user_id: int):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT user_id, full_name, email
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if not user:
        return None

    return {
        "user_id": user["user_id"],
        "full_name": user["full_name"],
        "email": user["email"],
    }


def update_user(
    user_id: int, full_name: str, email: str, new_password: str | None = None
):
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name:
        raise ValueError("Full name is required.")

    if not validate_email(email):
        raise ValueError("Email validation failed.")

    with get_connection() as conn:
        if new_password:
            password_hash = hash_password(new_password)

            cursor = conn.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?, password = ?
                WHERE user_id = ?
                """,
                (full_name, email, password_hash, user_id),
            )
        else:
            cursor = conn.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?
                WHERE user_id = ?
                """,
                (full_name, email, user_id),
            )

        if cursor.rowcount == 0:
            raise ValueError("User not found.")

    return get_user_by_id(user_id)


def get_dashboard_data():
    with get_connection() as conn:
        stats = conn.execute("""
            SELECT
                COUNT(*) AS total_slots,
                COALESCE(SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END), 0) AS occupied,
                COALESCE(SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END), 0) AS available,
                COALESCE(SUM(CASE WHEN status = 'Reserved' THEN 1 ELSE 0 END), 0) AS reserved
            FROM parking_slots
            """).fetchone()

        slots = conn.execute("""
            SELECT slot_id, zone, slot_number, status
            FROM parking_slots
            ORDER BY zone, slot_number
            """).fetchall()

    return {
        "total_slots": stats["total_slots"],
        "occupied": stats["occupied"],
        "available": stats["available"],
        "reserved": stats["reserved"],
        "slots": [dict(slot) for slot in slots],
    }
