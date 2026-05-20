from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
import os
import sqlite3

from .security import hash_password

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR / "data" / "smartpark.db"


def get_db_path() -> Path:
    return Path(os.getenv("SMARTPARK_DB_PATH", str(DEFAULT_DB_PATH)))


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def utc_now_sql() -> str:
    return "strftime('%Y-%m-%dT%H:%M:%fZ','now')"


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def transaction(immediate: bool = False):
    conn = get_connection()
    try:
        if immediate:
            conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


SCHEMA_SQL = r'''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin' CHECK(role IN ('admin','operator')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS auth_tokens (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS parking_lots (
    lot_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS parking_zones (
    zone_id TEXT PRIMARY KEY,
    lot_id TEXT NOT NULL REFERENCES parking_lots(lot_id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    floor_level INTEGER NOT NULL DEFAULT 0,
    zone_type TEXT NOT NULL DEFAULT 'Standard' CHECK(zone_type IN ('Standard','EV','Disabled Access','VIP','Truck','Motorcycle')),
    priority_score INTEGER NOT NULL DEFAULT 50 CHECK(priority_score BETWEEN 0 AND 100),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(lot_id, name)
);

CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id TEXT PRIMARY KEY,
    zone_id TEXT NOT NULL REFERENCES parking_zones(zone_id) ON DELETE RESTRICT,
    slot_code TEXT NOT NULL UNIQUE,
    slot_type TEXT NOT NULL DEFAULT 'Standard' CHECK(slot_type IN ('Standard','Motorcycle','EV','Disabled Access','Truck','VIP')),
    status TEXT NOT NULL DEFAULT 'Available' CHECK(status IN ('Available','Occupied','Reserved','Maintenance','Disabled')),
    distance_score INTEGER NOT NULL DEFAULT 50 CHECK(distance_score BETWEEN 0 AND 100),
    priority_score INTEGER NOT NULL DEFAULT 50 CHECK(priority_score BETWEEN 0 AND 100),
    override_reason TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS sensors (
    sensor_id TEXT PRIMARY KEY,
    sensor_code TEXT NOT NULL UNIQUE,
    sensor_type TEXT NOT NULL DEFAULT 'Ultrasonic',
    slot_id TEXT UNIQUE REFERENCES parking_slots(slot_id) ON DELETE SET NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    last_status TEXT NOT NULL DEFAULT 'Unknown' CHECK(last_status IN ('Clear','Occupied','Fault','Unknown')),
    battery_level INTEGER NOT NULL DEFAULT 100 CHECK(battery_level BETWEEN 0 AND 100),
    last_seen_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY,
    plate_number TEXT NOT NULL UNIQUE,
    vehicle_type TEXT NOT NULL DEFAULT 'Car' CHECK(vehicle_type IN ('Car','Motorcycle','EV','Disabled Access','Truck','VIP')),
    owner_name TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS tariff_plans (
    tariff_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    hourly_rate REAL NOT NULL CHECK(hourly_rate >= 0),
    grace_minutes INTEGER NOT NULL DEFAULT 0 CHECK(grace_minutes >= 0),
    daily_max REAL NOT NULL CHECK(daily_max >= 0),
    vehicle_type TEXT CHECK(vehicle_type IN ('Car','Motorcycle','EV','Disabled Access','Truck','VIP')),
    zone_id TEXT REFERENCES parking_zones(zone_id) ON DELETE SET NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS parking_sessions (
    session_id TEXT PRIMARY KEY,
    vehicle_id TEXT NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE RESTRICT,
    slot_id TEXT NOT NULL REFERENCES parking_slots(slot_id) ON DELETE RESTRICT,
    tariff_id TEXT NOT NULL REFERENCES tariff_plans(tariff_id) ON DELETE RESTRICT,
    tariff_name_snapshot TEXT NOT NULL,
    hourly_rate_snapshot REAL NOT NULL CHECK(hourly_rate_snapshot >= 0),
    grace_minutes_snapshot INTEGER NOT NULL CHECK(grace_minutes_snapshot >= 0),
    daily_max_snapshot REAL NOT NULL CHECK(daily_max_snapshot >= 0),
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active','Completed','Cancelled')),
    fee_amount REAL NOT NULL DEFAULT 0 CHECK(fee_amount >= 0),
    payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid','Pending','Paid','Failed','Refunded')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    CHECK(exit_time IS NULL OR exit_time > entry_time)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_active_session_vehicle ON parking_sessions(vehicle_id) WHERE status = 'Active';
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_session_slot ON parking_sessions(slot_id) WHERE status = 'Active';

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE REFERENCES parking_sessions(session_id) ON DELETE RESTRICT,
    paid_amount REAL NOT NULL CHECK(paid_amount >= 0),
    method TEXT NOT NULL CHECK(method IN ('Cash','Card','Online','Wallet')),
    status TEXT NOT NULL CHECK(status IN ('Pending','Paid','Failed','Refunded')),
    reference_number TEXT NOT NULL UNIQUE,
    paid_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS sensor_events (
    event_id TEXT PRIMARY KEY,
    sensor_id TEXT NOT NULL REFERENCES sensors(sensor_id) ON DELETE CASCADE,
    slot_id TEXT REFERENCES parking_slots(slot_id) ON DELETE SET NULL,
    reported_status TEXT NOT NULL CHECK(reported_status IN ('Clear','Occupied','Fault','Unknown')),
    raw_payload TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS activity_logs (
    activity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'Info' CHECK(severity IN ('Info','Success','Warning','Critical')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
'''


def init_db(reset: bool = False, seed: bool = True) -> None:
    with get_connection() as conn:
        if reset:
            conn.executescript("""
            DROP TABLE IF EXISTS activity_logs;
            DROP TABLE IF EXISTS sensor_events;
            DROP TABLE IF EXISTS payments;
            DROP TABLE IF EXISTS parking_sessions;
            DROP TABLE IF EXISTS tariff_plans;
            DROP TABLE IF EXISTS vehicles;
            DROP TABLE IF EXISTS sensors;
            DROP TABLE IF EXISTS parking_slots;
            DROP TABLE IF EXISTS parking_zones;
            DROP TABLE IF EXISTS parking_lots;
            DROP TABLE IF EXISTS auth_tokens;
            DROP TABLE IF EXISTS users;
            """)
        conn.executescript(SCHEMA_SQL)
        if seed:
            seed_demo_data(conn)


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    with get_connection() as conn:
        return row_to_dict(conn.execute(query, params).fetchone())


def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    with get_connection() as conn:
        return rows_to_dicts(conn.execute(query, params).fetchall())


def execute(query: str, params: tuple = ()) -> None:
    with get_connection() as conn:
        conn.execute(query, params)


def touch_clause() -> str:
    return "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')"


def log_activity(conn: sqlite3.Connection, entity_type: str, entity_id: str, title: str, message: str, severity: str = "Info") -> None:
    conn.execute(
        "INSERT INTO activity_logs (activity_id, entity_type, entity_id, title, message, severity) VALUES (?, ?, ?, ?, ?, ?)",
        (new_id("act"), entity_type, entity_id, title, message, severity),
    )


def paged_query(base_sql: str, count_sql: str, params: tuple = (), limit: int = 50, offset: int = 0) -> dict:
    safe_limit = min(max(int(limit), 1), 200)
    safe_offset = max(int(offset), 0)
    with get_connection() as conn:
        total = conn.execute(count_sql, params).fetchone()[0]
        rows = conn.execute(f"{base_sql} LIMIT ? OFFSET ?", params + (safe_limit, safe_offset)).fetchall()
    return {"total": total, "limit": safe_limit, "offset": safe_offset, "items": rows_to_dicts(rows)}


def seed_demo_data(conn: sqlite3.Connection) -> None:
    admin = conn.execute("SELECT user_id FROM users WHERE email = ?", ("admin@smartpark.com",)).fetchone()
    if not admin:
        conn.execute(
            "INSERT INTO users (user_id, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            ("usr_admin", "SmartPark Admin", "admin@smartpark.com", hash_password("admin1234"), "admin"),
        )

    if conn.execute("SELECT COUNT(*) FROM parking_lots").fetchone()[0] > 0:
        return

    conn.executemany(
        "INSERT INTO parking_lots (lot_id, name, address, description) VALUES (?, ?, ?, ?)",
        [
            ("lot_central", "Central Business Garage", "28 Nizami Street, Baku", "Primary downtown demo facility"),
            ("lot_airport", "Airport Long Stay", "Terminal Avenue, Baku", "Long stay parking near departures"),
        ],
    )
    conn.executemany(
        "INSERT INTO parking_zones (zone_id, lot_id, name, floor_level, zone_type, priority_score) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("zone_a", "lot_central", "A Ground", 0, "Standard", 20),
            ("zone_b", "lot_central", "B EV", 1, "EV", 15),
            ("zone_c", "lot_central", "C Accessible", 0, "Disabled Access", 5),
            ("zone_d", "lot_airport", "D Long Stay", 2, "Standard", 60),
        ],
    )
    slots = []
    for code, zone_id, slot_type, distance, priority in [
        ("A", "zone_a", "Standard", 20, 20),
        ("B", "zone_b", "EV", 35, 20),
        ("C", "zone_c", "Disabled Access", 10, 10),
        ("D", "zone_d", "Standard", 70, 50),
    ]:
        for n in range(1, 13):
            status = "Available"
            if code == "A" and n in (11, 12):
                status = "Maintenance" if n == 11 else "Reserved"
            if code == "D" and n == 12:
                status = "Disabled"
            slots.append((f"slot_{code.lower()}_{n:02}", zone_id, f"{code}-{n:02}", slot_type, status, min(distance + n, 100), priority))
    conn.executemany(
        "INSERT INTO parking_slots (slot_id, zone_id, slot_code, slot_type, status, distance_score, priority_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
        slots,
    )
    sensors = []
    for n in range(1, 25):
        if n <= 12:
            zone = "a"
            local = n
        else:
            zone = "b"
            local = n - 12
        active = 0 if n in (7, 23) else 1
        last_status = "Fault" if n == 7 else "Clear"
        battery = max(8, 95 - n * 3)
        sensors.append((f"sensor_{n:02}", f"SNS-{n:03}", "Ultrasonic", f"slot_{zone}_{local:02}", active, last_status, battery))
    conn.executemany(
        "INSERT INTO sensors (sensor_id, sensor_code, sensor_type, slot_id, is_active, last_status, battery_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
        sensors,
    )
    conn.executemany(
        "INSERT INTO vehicles (vehicle_id, plate_number, vehicle_type, owner_name) VALUES (?, ?, ?, ?)",
        [
            ("veh_alpha", "10-AA-101", "Car", "Demo Driver One"),
            ("veh_ev", "10-EV-222", "EV", "Demo Driver Two"),
            ("veh_vip", "10-VIP-777", "VIP", "Executive Driver"),
            ("veh_disabled", "10-DA-404", "Disabled Access", "Accessible Driver"),
        ],
    )
    conn.executemany(
        "INSERT INTO tariff_plans (tariff_id, name, hourly_rate, grace_minutes, daily_max, vehicle_type, zone_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("tariff_standard", "Standard Daily", 2.5, 15, 18.0, None, None, 1),
            ("tariff_ev", "EV Priority", 3.5, 10, 24.0, "EV", "zone_b", 1),
            ("tariff_vip", "VIP Covered", 5.0, 5, 35.0, "VIP", None, 1),
        ],
    )
    conn.execute(
        """
        INSERT INTO parking_sessions (
            session_id, vehicle_id, slot_id, tariff_id, tariff_name_snapshot,
            hourly_rate_snapshot, grace_minutes_snapshot, daily_max_snapshot,
            entry_time, status, fee_amount, payment_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now','-45 minutes'), ?, ?, ?)
        """,
        ("sess_active_demo", "veh_alpha", "slot_a_01", "tariff_standard", "Standard Daily", 2.5, 15, 18.0, "Active", 0.0, "Unpaid"),
    )
    conn.execute("UPDATE parking_slots SET status = 'Occupied' WHERE slot_id = 'slot_a_01'")
    conn.execute("UPDATE sensors SET last_status = 'Occupied', last_seen_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = 'slot_a_01'")
    conn.execute(
        """
        INSERT INTO parking_sessions (
            session_id, vehicle_id, slot_id, tariff_id, tariff_name_snapshot,
            hourly_rate_snapshot, grace_minutes_snapshot, daily_max_snapshot,
            entry_time, exit_time, status, fee_amount, payment_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now','-4 hours'), strftime('%Y-%m-%dT%H:%M:%fZ','now','-1 hours'), ?, ?, ?)
        """,
        ("sess_paid_demo", "veh_ev", "slot_b_01", "tariff_ev", "EV Priority", 3.5, 10, 24.0, "Completed", 10.5, "Paid"),
    )
    conn.execute(
        "INSERT INTO payments (payment_id, session_id, paid_amount, method, status, reference_number, paid_at) VALUES (?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now','-1 hours'))",
        ("pay_paid_demo", "sess_paid_demo", 10.5, "Card", "Paid", "SP-DEMO-0001"),
    )
    conn.execute(
        """
        INSERT INTO parking_sessions (
            session_id, vehicle_id, slot_id, tariff_id, tariff_name_snapshot,
            hourly_rate_snapshot, grace_minutes_snapshot, daily_max_snapshot,
            entry_time, exit_time, status, fee_amount, payment_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now','-6 hours'), strftime('%Y-%m-%dT%H:%M:%fZ','now','-3 hours'), ?, ?, ?)
        """,
        ("sess_unpaid_demo", "veh_vip", "slot_d_01", "tariff_vip", "VIP Covered", 5.0, 5, 35.0, "Completed", 15.0, "Unpaid"),
    )
    conn.execute(
        """
        INSERT INTO parking_sessions (
            session_id, vehicle_id, slot_id, tariff_id, tariff_name_snapshot,
            hourly_rate_snapshot, grace_minutes_snapshot, daily_max_snapshot,
            entry_time, exit_time, status, fee_amount, payment_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now','-8 hours'), strftime('%Y-%m-%dT%H:%M:%fZ','now','-7 hours'), ?, ?, ?)
        """,
        ("sess_failed_demo", "veh_disabled", "slot_c_01", "tariff_standard", "Standard Daily", 2.5, 15, 18.0, "Completed", 2.5, "Failed"),
    )
    conn.execute(
        "INSERT INTO payments (payment_id, session_id, paid_amount, method, status, reference_number) VALUES (?, ?, ?, ?, ?, ?)",
        ("pay_failed_demo", "sess_failed_demo", 2.5, "Wallet", "Failed", "SP-DEMO-0002"),
    )
    conn.executemany(
        "INSERT INTO activity_logs (activity_id, entity_type, entity_id, title, message, severity, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("act_seed_01", "slot", "slot_a_01", "Session started", "Vehicle 10-AA-101 entered A-01 through optimized assignment.", "Success", "2026-05-19T09:15:00.000Z"),
            ("act_seed_02", "slot", "slot_b_01", "Payment completed", "EV session settled by card for 10.50.", "Success", "2026-05-19T11:25:00.000Z"),
            ("act_seed_03", "slot", "slot_a_07", "Maintenance flag", "A-07 is blocked for bay line inspection.", "Warning", "2026-05-19T08:40:00.000Z"),
            ("act_seed_04", "sensor", "sensor_07", "Sensor attention", "Sensor SNS-007 has lower battery than the target operating threshold.", "Warning", "2026-05-19T10:00:00.000Z"),
        ],
    )
