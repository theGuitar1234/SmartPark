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
