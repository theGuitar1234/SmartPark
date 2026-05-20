from __future__ import annotations

import sqlite3

from .. import db
from .tariff_service import now_iso


def process_payment(conn: sqlite3.Connection, payload: dict) -> dict:
    session = conn.execute("SELECT * FROM parking_sessions WHERE session_id = ?", (payload["session_id"],)).fetchone()
    if not session:
        raise ValueError("Parking session was not found.")
    if session["status"] != "Completed":
        raise ValueError("Payment can only be processed for a completed session.")
    existing = conn.execute("SELECT * FROM payments WHERE session_id = ?", (payload["session_id"],)).fetchone()
    expected = round(float(session["fee_amount"]), 2)
    paid_amount = round(float(payload["paid_amount"]), 2)
    status = payload["status"]
    if session["payment_status"] == "Paid" and existing and existing["status"] == "Paid":
        raise ValueError("This session has already been paid.")
    if status == "Paid" and paid_amount != expected:
        raise ValueError(f"Payment amount must match the calculated fee of {expected:.2f}.")
    paid_at = now_iso() if status == "Paid" else None
    if existing:
        payment_id = existing["payment_id"]
        conn.execute(
            """
            UPDATE payments
            SET paid_amount = ?, method = ?, status = ?, paid_at = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE payment_id = ?
            """,
            (paid_amount, payload["method"], status, paid_at, payment_id),
        )
    else:
        payment_id = db.new_id("pay")
        reference = f"SP-{payment_id[-8:].upper()}"
        conn.execute(
            """
            INSERT INTO payments (payment_id, session_id, paid_amount, method, status, reference_number, paid_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (payment_id, payload["session_id"], paid_amount, payload["method"], status, reference, paid_at),
        )
    new_session_status = status
    if status == "Pending":
        new_session_status = "Pending"
    if status == "Failed":
        new_session_status = "Failed"
    if status == "Refunded":
        new_session_status = "Refunded"
    conn.execute("UPDATE parking_sessions SET payment_status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE session_id = ?", (new_session_status, payload["session_id"]))
    payment = dict(conn.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,)).fetchone())
    vehicle = conn.execute("SELECT v.plate_number, s.slot_code, ps.slot_id FROM parking_sessions ps JOIN vehicles v ON v.vehicle_id = ps.vehicle_id JOIN parking_slots s ON s.slot_id = ps.slot_id WHERE ps.session_id = ?", (payload["session_id"],)).fetchone()
    if vehicle:
        severity = "Success" if status == "Paid" else "Warning"
        db.log_activity(conn, "session", payload["session_id"], "Payment processed", f"{status} payment via {payload['method']} for {paid_amount:.2f}.", severity)
        db.log_activity(conn, "slot", vehicle["slot_id"], "Payment processed", f"{vehicle['plate_number']} session from {vehicle['slot_code']} recorded as {status}.", severity)
    return payment
