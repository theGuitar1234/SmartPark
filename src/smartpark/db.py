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

ALLOWED_ITEM_SORT_COLUMNS = {"id", "field1", "field2", "field3"}
ALLOWED_SORT_ORDERS = {"asc", "desc"}


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

            CREATE TABLE IF NOT EXISTS items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                field1      TEXT NOT NULL,
                field2      TEXT NOT NULL,
                field3      TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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

        item_count = conn.execute("SELECT COUNT(*) AS total FROM items").fetchone()
        if item_count["total"] == 0:
            conn.executemany(
                """
                INSERT INTO items (field1, field2, field3)
                VALUES (?, ?, ?)
                """,
                [
                    ("Alpha", "One", "First"),
                    ("Beta", "Two", "Second"),
                    ("Gamma", "Three", "Third"),
                ],
            )


def create_user(full_name: str, email: str, password: str):
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name:
        raise ValueError("Full name is required.")

    if not validate_email(email):
        raise ValueError("Email validation failed.")

    if len(password or "") < 4:
        raise ValueError("Password must be at least 4 characters long.")

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
            if len(new_password) < 4:
                raise ValueError("Password must be at least 4 characters long.")

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


def create_item(field1: str, field2: str, field3: str):
    field1 = field1.strip()
    field2 = field2.strip()
    field3 = field3.strip()

    if not field1 or not field2 or not field3:
        raise ValueError("All item fields are required.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO items (field1, field2, field3)
            VALUES (?, ?, ?)
            """,
            (field1, field2, field3),
        )
        item_id = cursor.lastrowid

    return get_item_by_id(item_id)


def get_item_by_id(item_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, field1, field2, field3
            FROM items
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()

    if not row:
        return None

    return dict(row)


def normalize_item_query_params(
    limit: int = 10,
    offset: int = 0,
    search: str | None = None,
    sort_by: str = "id",
    order: str = "asc",
):
    """Validate and normalize user-controlled list/query parameters."""
    limit = min(max(int(limit), 1), 100)
    offset = max(int(offset), 0)
    search = (search or "").strip()
    sort_by = sort_by if sort_by in ALLOWED_ITEM_SORT_COLUMNS else "id"
    order = (order or "asc").lower()
    order = order if order in ALLOWED_SORT_ORDERS else "asc"

    return limit, offset, search, sort_by, order


def get_items_page(
    limit: int = 10,
    offset: int = 0,
    search: str | None = None,
    sort_by: str = "id",
    order: str = "asc",
):
    limit, offset, search, sort_by, order = normalize_item_query_params(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        order=order,
    )

    where = ""
    args: tuple[str, ...] = ()

    if search:
        like = f"%{search}%"
        where = "WHERE field1 LIKE ? OR field2 LIKE ? OR field3 LIKE ?"
        args = (like, like, like)

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS total FROM items {where}",
            args,
        ).fetchone()["total"]

        rows = conn.execute(
            f"""
            SELECT id, field1, field2, field3
            FROM items
            {where}
            ORDER BY {sort_by} {order.upper()}
            LIMIT ? OFFSET ?
            """,
            args + (limit, offset),
        ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(row) for row in rows],
    }


def get_items(search: str | None = None):
    """Backward-compatible helper for callers that still need the full list."""
    return get_items_page(
        limit=100,
        offset=0,
        search=search,
        sort_by="id",
        order="asc",
    )["items"]


def seed_items(target_count: int = 100) -> int:
    """Seed deterministic demo records until the items table reaches target_count."""
    if target_count < 1:
        return 0

    inserted = 0
    with get_connection() as conn:
        current_count = conn.execute(
            "SELECT COUNT(*) AS total FROM items"
        ).fetchone()["total"]

        if current_count >= target_count:
            return 0

        rows = []
        for n in range(current_count + 1, target_count + 1):
            rows.append((f"Alpha-{n:03}", f"Beta-{n:03}", f"Gamma-{n:03}"))

        conn.executemany(
            """
            INSERT INTO items (field1, field2, field3)
            VALUES (?, ?, ?)
            """,
            rows,
        )
        inserted = len(rows)

    return inserted

def update_item(item_id: int, field1: str, field2: str, field3: str):
    field1 = field1.strip()
    field2 = field2.strip()
    field3 = field3.strip()

    if not field1 or not field2 or not field3:
        raise ValueError("All item fields are required.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE items
            SET field1 = ?, field2 = ?, field3 = ?
            WHERE id = ?
            """,
            (field1, field2, field3, item_id),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"ID '{item_id}' not found.")

    return get_item_by_id(item_id)


def delete_item(item_id: int):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        if cursor.rowcount == 0:
            raise ValueError(f"ID '{item_id}' not found.")
