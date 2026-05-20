from __future__ import annotations

import sqlite3

from .. import db
from .slot_optimizer import find_best_slot
from .tariff_service import TariffSnapshot, calculate_fee, now_iso


def get_vehicle_or_create(conn: sqlite3.Connection, plate_number: str, vehicle_type: str, owner_name: str) -> dict:
    row = conn.execute("SELECT * FROM vehicles WHERE plate_number = ?", (plate_number,)).fetchone()
    if row:
        return dict(row)
    vehicle_id = db.new_id("veh")
    conn.execute(
        "INSERT INTO vehicles (vehicle_id, plate_number, vehicle_type, owner_name) VALUES (?, ?, ?, ?)",
        (vehicle_id, plate_number, vehicle_type, owner_name or ""),
    )
    return dict(conn.execute("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,)).fetchone())


def choose_tariff(conn: sqlite3.Connection, tariff_id: str | None, vehicle_type: str, zone_id: str) -> dict:
    if tariff_id:
        row = conn.execute("SELECT * FROM tariff_plans WHERE tariff_id = ? AND is_active = 1", (tariff_id,)).fetchone()
        if not row:
            raise ValueError("Selected tariff plan is inactive or does not exist.")
        return dict(row)
    row = conn.execute(
        """
        SELECT * FROM tariff_plans
        WHERE is_active = 1 AND vehicle_type = ? AND (zone_id = ? OR zone_id IS NULL)
        ORDER BY CASE WHEN zone_id = ? THEN 0 ELSE 1 END, daily_max ASC, hourly_rate ASC
        LIMIT 1
        """,
        (vehicle_type, zone_id, zone_id),
    ).fetchone()
    if not row:
        row = conn.execute(
            """
            SELECT * FROM tariff_plans
            WHERE is_active = 1 AND vehicle_type IS NULL AND (zone_id = ? OR zone_id IS NULL)
            ORDER BY CASE WHEN zone_id = ? THEN 0 ELSE 1 END, daily_max ASC, hourly_rate ASC
            LIMIT 1
            """,
            (zone_id, zone_id),
        ).fetchone()
    if not row:
        raise ValueError("No active tariff plan is available for this vehicle and zone.")
    return dict(row)


def get_session(conn: sqlite3.Connection, session_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT ps.*, v.plate_number, v.vehicle_type, s.slot_code
        FROM parking_sessions ps
        JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
        JOIN parking_slots s ON s.slot_id = ps.slot_id
        WHERE ps.session_id = ?
        """,
        (session_id,),
    ).fetchone()
    return dict(row) if row else None


def start_session(conn: sqlite3.Connection, payload: dict) -> dict:
    vehicle = get_vehicle_or_create(conn, payload["plate_number"], payload["vehicle_type"], payload.get("owner_name") or "")
    active = conn.execute("SELECT session_id FROM parking_sessions WHERE vehicle_id = ? AND status = 'Active'", (vehicle["vehicle_id"],)).fetchone()
    if active:
        raise ValueError("This vehicle already has an active parking session.")
    slot_id = payload.get("slot_id")
    if slot_id:
        slot = conn.execute("SELECT * FROM parking_slots WHERE slot_id = ?", (slot_id,)).fetchone()
        if not slot:
            raise ValueError("Selected slot does not exist.")
        if slot["status"] != "Available":
            raise ValueError("Selected slot is not available.")
        zone_id = slot["zone_id"]
    else:
        result = find_best_slot(conn, payload["vehicle_type"], payload.get("zone_id"))
        if not result["slot"]:
            raise ValueError(result["explanation"][0])
        slot_id = result["slot"]["slot_id"]
        zone_id = result["slot"]["zone_id"]
    slot_active = conn.execute("SELECT session_id FROM parking_sessions WHERE slot_id = ? AND status = 'Active'", (slot_id,)).fetchone()
    if slot_active:
        raise ValueError("Selected slot already has an active parking session.")
    tariff = choose_tariff(conn, payload.get("tariff_id"), payload["vehicle_type"], zone_id)
    session_id = db.new_id("sess")
    entry_time = payload.get("entry_time") or now_iso()
    conn.execute(
        """
        INSERT INTO parking_sessions (
            session_id, vehicle_id, slot_id, tariff_id, tariff_name_snapshot,
            hourly_rate_snapshot, grace_minutes_snapshot, daily_max_snapshot,
            entry_time, status, fee_amount, payment_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', 0, 'Unpaid')
        """,
        (session_id, vehicle["vehicle_id"], slot_id, tariff["tariff_id"], tariff["name"], tariff["hourly_rate"], tariff["grace_minutes"], tariff["daily_max"], entry_time),
    )
    conn.execute("UPDATE parking_slots SET status = 'Occupied', override_reason = NULL, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ?", (slot_id,))
    conn.execute("UPDATE sensors SET last_status = 'Occupied', last_seen_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'), updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ?", (slot_id,))
    session = get_session(conn, session_id)
    db.log_activity(conn, "slot", slot_id, "Session started", f"Vehicle {payload['plate_number']} assigned to {session['slot_code']} using {tariff['name']}.", "Success")
    db.log_activity(conn, "session", session_id, "Entry recorded", f"Active session opened for {payload['plate_number']} at {session['entry_time']}.", "Success")
    return session


def exit_session(conn: sqlite3.Connection, session_id: str, exit_time: str | None = None) -> dict:
    session = get_session(conn, session_id)
    if not session:
        raise ValueError("Parking session was not found.")
    if session["status"] != "Active":
        raise ValueError("Only active sessions can be exited.")
    actual_exit = exit_time or now_iso()
    tariff = TariffSnapshot(session["hourly_rate_snapshot"], session["grace_minutes_snapshot"], session["daily_max_snapshot"])
    fee = calculate_fee(session["entry_time"], actual_exit, tariff)
    conn.execute(
        """
        UPDATE parking_sessions
        SET exit_time = ?, status = 'Completed', fee_amount = ?, payment_status = CASE WHEN ? = 0 THEN 'Paid' ELSE 'Unpaid' END, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
        WHERE session_id = ?
        """,
        (actual_exit, fee, fee, session_id),
    )
    conn.execute("UPDATE parking_slots SET status = 'Available', updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ?", (session["slot_id"],))
    conn.execute("UPDATE sensors SET last_status = 'Clear', last_seen_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'), updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ?", (session["slot_id"],))
    updated = get_session(conn, session_id)
    db.log_activity(conn, "slot", session["slot_id"], "Session exited", f"Vehicle {session['plate_number']} left {session['slot_code']}; calculated fee is {fee:.2f}.", "Info")
    db.log_activity(conn, "session", session_id, "Fee calculated", f"Exit completed with a deterministic tariff snapshot fee of {fee:.2f}.", "Info")
    return updated


def cancel_session(conn: sqlite3.Connection, session_id: str) -> dict:
    session = get_session(conn, session_id)
    if not session:
        raise ValueError("Parking session was not found.")
    if session["status"] != "Active":
        raise ValueError("Only active sessions can be cancelled.")
    conn.execute("UPDATE parking_sessions SET status = 'Cancelled', updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE session_id = ?", (session_id,))
    conn.execute("UPDATE parking_slots SET status = 'Available', updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ?", (session["slot_id"],))
    conn.execute("UPDATE sensors SET last_status = 'Clear', last_seen_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'), updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ?", (session["slot_id"],))
    updated = get_session(conn, session_id)
    db.log_activity(conn, "slot", session["slot_id"], "Session cancelled", f"Active session for {session['plate_number']} was cancelled and {session['slot_code']} was released.", "Warning")
    db.log_activity(conn, "session", session_id, "Session cancelled", "Operator cancelled this active session.", "Warning")
    return updated
