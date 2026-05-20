from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import db
from ..schemas import BulkSlotPreviewRequest, PageResponse, ParkingSlotCreate, ParkingSlotResponse, ParkingSlotUpdate, SlotStatusUpdate
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/slots", tags=["Parking Slots"], dependencies=[Depends(get_current_user)])

SLOT_SELECT = """
SELECT
    s.*,
    z.name AS zone_name,
    l.name AS lot_name,
    sn.sensor_id,
    sn.sensor_code,
    sn.last_status AS sensor_status,
    sn.battery_level AS sensor_battery_level,
    v.plate_number AS active_plate,
    ps.session_id AS active_session_id
FROM parking_slots s
JOIN parking_zones z ON z.zone_id = s.zone_id
JOIN parking_lots l ON l.lot_id = z.lot_id
LEFT JOIN sensors sn ON sn.slot_id = s.slot_id
LEFT JOIN parking_sessions ps ON ps.slot_id = s.slot_id AND ps.status = 'Active'
LEFT JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
"""


def slot_codes(payload: BulkSlotPreviewRequest) -> list[str]:
    return [f"{payload.prefix}-{n:02}" for n in range(payload.start_number, payload.start_number + payload.count)]


@router.get("", response_model=PageResponse)
def list_slots(search: str = "", zone_id: str | None = None, status_filter: str | None = None, limit: int = Query(80, ge=1, le=200), offset: int = Query(0, ge=0)):
    where = "WHERE (s.slot_code LIKE ? OR z.name LIKE ? OR l.name LIKE ?)"
    params: list = [f"%{search.strip()}%", f"%{search.strip()}%", f"%{search.strip()}%"]
    if zone_id:
        where += " AND s.zone_id = ?"
        params.append(zone_id)
    if status_filter:
        where += " AND s.status = ?"
        params.append(status_filter)
    return db.paged_query(
        f"{SLOT_SELECT} {where} ORDER BY l.name, z.name, s.slot_code",
        f"SELECT COUNT(*) FROM parking_slots s JOIN parking_zones z ON z.zone_id = s.zone_id JOIN parking_lots l ON l.lot_id = z.lot_id {where}",
        tuple(params),
        limit,
        offset,
    )


@router.get("/{slot_id}", response_model=ParkingSlotResponse)
def get_slot(slot_id: str):
    slot = db.fetch_one(f"{SLOT_SELECT} WHERE s.slot_id = ?", (slot_id,))
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking slot was not found.")
    return slot




@router.get("/{slot_id}/detail")
def get_slot_detail(slot_id: str):
    with db.get_connection() as conn:
        slot = conn.execute(f"{SLOT_SELECT} WHERE s.slot_id = ?", (slot_id,)).fetchone()
        if not slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking slot was not found.")
        slot_data = dict(slot)
        sensor = conn.execute("SELECT * FROM sensors WHERE slot_id = ?", (slot_id,)).fetchone()
        active_session = conn.execute(
            """
            SELECT ps.*, v.plate_number, v.vehicle_type, v.owner_name, s.slot_code
            FROM parking_sessions ps
            JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
            JOIN parking_slots s ON s.slot_id = ps.slot_id
            WHERE ps.slot_id = ? AND ps.status = 'Active'
            """,
            (slot_id,),
        ).fetchone()
        recent_sessions = db.rows_to_dicts(conn.execute(
            """
            SELECT ps.session_id, v.plate_number, ps.entry_time, ps.exit_time, ps.status, ps.fee_amount, ps.payment_status
            FROM parking_sessions ps
            JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
            WHERE ps.slot_id = ?
            ORDER BY ps.created_at DESC
            LIMIT 8
            """,
            (slot_id,),
        ).fetchall())
        sensor_events = db.rows_to_dicts(conn.execute(
            """
            SELECT reported_status, raw_payload, created_at
            FROM sensor_events
            WHERE slot_id = ?
            ORDER BY created_at DESC
            LIMIT 8
            """,
            (slot_id,),
        ).fetchall())
        ids = [slot_id]
        if sensor:
            ids.append(sensor["sensor_id"])
        if active_session:
            ids.append(active_session["session_id"])
        placeholders = ",".join(["?"] * len(ids))
        activity = db.rows_to_dicts(conn.execute(
            f"SELECT * FROM activity_logs WHERE entity_id IN ({placeholders}) ORDER BY created_at DESC LIMIT 14",
            tuple(ids),
        ).fetchall())
        return {
            "slot": slot_data,
            "sensor": dict(sensor) if sensor else None,
            "active_session": dict(active_session) if active_session else None,
            "recent_sessions": recent_sessions,
            "sensor_events": sensor_events,
            "activity": activity,
        }


@router.post("", response_model=ParkingSlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(payload: ParkingSlotCreate):
    slot_id = db.new_id("slot")
    try:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO parking_slots (slot_id, zone_id, slot_code, slot_type, status, distance_score, priority_score, override_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (slot_id, payload.zone_id, payload.slot_code, payload.slot_type.value, payload.status.value, payload.distance_score, payload.priority_score, payload.override_reason),
            )
            slot = dict(conn.execute(f"{SLOT_SELECT} WHERE s.slot_id = ?", (slot_id,)).fetchone())
            db.log_activity(conn, "slot", slot_id, "Slot created", f"Slot {slot['slot_code']} was created as {slot['slot_type']} in {slot['zone_name']}.", "Success")
            return slot
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.put("/{slot_id}", response_model=ParkingSlotResponse)
def update_slot(slot_id: str, payload: ParkingSlotUpdate):
    current = db.fetch_one("SELECT * FROM parking_slots WHERE slot_id = ?", (slot_id,))
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking slot was not found.")
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return get_slot(slot_id)
    if "status" in values:
        active = db.fetch_one("SELECT session_id FROM parking_sessions WHERE slot_id = ? AND status = 'Active'", (slot_id,))
        if active and values["status"].value != "Occupied":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active session is using this slot. Use session exit/cancel before changing availability.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Use the status override endpoint for slot status changes so a reason and audit record are captured.")
    values = {key: (value.value if hasattr(value, "value") else value) for key, value in values.items()}
    assignments = ", ".join([f"{key} = ?" for key in values])
    params = tuple(values.values()) + (slot_id,)
    try:
        with db.transaction() as conn:
            conn.execute(f"UPDATE parking_slots SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ?", params)
            slot = dict(conn.execute(f"{SLOT_SELECT} WHERE s.slot_id = ?", (slot_id,)).fetchone())
            db.log_activity(conn, "slot", slot_id, "Slot updated", f"Slot {slot['slot_code']} configuration was updated.", "Info")
            return slot
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.post("/{slot_id}/status", response_model=ParkingSlotResponse)
def set_slot_status(slot_id: str, payload: SlotStatusUpdate):
    current = db.fetch_one("SELECT * FROM parking_slots WHERE slot_id = ?", (slot_id,))
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking slot was not found.")
    active = db.fetch_one("SELECT session_id FROM parking_sessions WHERE slot_id = ? AND status = 'Active'", (slot_id,))
    if active and payload.status.value != "Occupied":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active session is using this slot. End or cancel the session first.")
    with db.transaction() as conn:
        conn.execute("UPDATE parking_slots SET status = ?, override_reason = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ?", (payload.status.value, payload.reason.strip(), slot_id))
        slot = dict(conn.execute(f"{SLOT_SELECT} WHERE s.slot_id = ?", (slot_id,)).fetchone())
        severity = "Warning" if payload.status.value in ("Maintenance", "Disabled", "Reserved") else "Info"
        db.log_activity(conn, "slot", slot_id, "Manual status override", f"Slot {slot['slot_code']} changed to {payload.status.value}. Reason: {payload.reason.strip()}", severity)
        return slot


@router.delete("/{slot_id}")
def delete_slot(slot_id: str):
    try:
        with db.transaction() as conn:
            cursor = conn.execute("DELETE FROM parking_slots WHERE slot_id = ?", (slot_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking slot was not found.")
        return {"message": "Parking slot deleted.", "slot_id": slot_id}
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.post("/bulk-preview")
def bulk_preview(payload: BulkSlotPreviewRequest):
    codes = slot_codes(payload)
    placeholders = ",".join(["?"] * len(codes))
    existing = db.fetch_all(f"SELECT slot_code FROM parking_slots WHERE slot_code IN ({placeholders})", tuple(codes)) if codes else []
    existing_codes = {row["slot_code"] for row in existing}
    rows = [{"slot_code": code, "will_create": code not in existing_codes, "issue": "Duplicate slot code" if code in existing_codes else ""} for code in codes]
    return {"zone_id": payload.zone_id, "total_requested": len(rows), "duplicates": len(existing_codes), "rows": rows}


@router.post("/bulk-create")
def bulk_create(payload: BulkSlotPreviewRequest):
    preview = bulk_preview(payload)
    if preview["duplicates"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bulk create rejected because duplicate slot codes were found. Run preview and adjust the range.")
    try:
        with db.transaction() as conn:
            zone = conn.execute("SELECT zone_id FROM parking_zones WHERE zone_id = ?", (payload.zone_id,)).fetchone()
            if not zone:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking zone was not found.")
            rows = [(db.new_id("slot"), payload.zone_id, code, payload.slot_type.value, "Available", payload.distance_score, payload.priority_score) for code in slot_codes(payload)]
            conn.executemany("INSERT INTO parking_slots (slot_id, zone_id, slot_code, slot_type, status, distance_score, priority_score) VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
            db.log_activity(conn, "zone", payload.zone_id, "Bulk slots created", f"Created {payload.count} {payload.slot_type.value} slots using prefix {payload.prefix}.", "Success")
        return {"message": "Slots created.", "created": payload.count}
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)
