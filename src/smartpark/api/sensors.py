from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import db
from ..schemas import PageResponse, SensorCreate, SensorResponse, SensorSimulationRequest, SensorUpdate
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/sensors", tags=["Sensors"], dependencies=[Depends(get_current_user)])

SENSOR_SELECT = """
SELECT sn.*, s.slot_code
FROM sensors sn
LEFT JOIN parking_slots s ON s.slot_id = sn.slot_id
"""


@router.get("", response_model=PageResponse)
def list_sensors(search: str = "", limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    term = f"%{search.strip()}%"
    return db.paged_query(
        f"{SENSOR_SELECT} WHERE sn.sensor_code LIKE ? OR s.slot_code LIKE ? ORDER BY sn.sensor_code",
        "SELECT COUNT(*) FROM sensors sn LEFT JOIN parking_slots s ON s.slot_id = sn.slot_id WHERE sn.sensor_code LIKE ? OR s.slot_code LIKE ?",
        (term, term),
        limit,
        offset,
    )


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: str):
    sensor = db.fetch_one(f"{SENSOR_SELECT} WHERE sn.sensor_id = ?", (sensor_id,))
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor was not found.")
    sensor["is_active"] = bool(sensor["is_active"])
    return sensor


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(payload: SensorCreate):
    sensor_id = db.new_id("sensor")
    try:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO sensors (sensor_id, sensor_code, sensor_type, slot_id, is_active, battery_level) VALUES (?, ?, ?, ?, ?, ?)",
                (sensor_id, payload.sensor_code, payload.sensor_type.strip(), payload.slot_id, int(payload.is_active), payload.battery_level),
            )
            sensor = dict(conn.execute(f"{SENSOR_SELECT} WHERE sn.sensor_id = ?", (sensor_id,)).fetchone())
            sensor["is_active"] = bool(sensor["is_active"])
            db.log_activity(conn, "sensor", sensor_id, "Sensor registered", f"Sensor {sensor['sensor_code']} was registered and assigned to {sensor.get('slot_code') or 'no slot'}.", "Success")
            if sensor.get("slot_id"):
                db.log_activity(conn, "slot", sensor["slot_id"], "Sensor assigned", f"Sensor {sensor['sensor_code']} is now assigned to this slot.", "Info")
            return sensor
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(sensor_id: str, payload: SensorUpdate):
    if not db.fetch_one("SELECT * FROM sensors WHERE sensor_id = ?", (sensor_id,)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor was not found.")
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return get_sensor(sensor_id)
    values = {key: int(value) if isinstance(value, bool) else value for key, value in values.items()}
    assignments = ", ".join([f"{key} = ?" for key in values])
    try:
        with db.transaction() as conn:
            conn.execute(f"UPDATE sensors SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE sensor_id = ?", tuple(values.values()) + (sensor_id,))
            sensor = dict(conn.execute(f"{SENSOR_SELECT} WHERE sn.sensor_id = ?", (sensor_id,)).fetchone())
            sensor["is_active"] = bool(sensor["is_active"])
            db.log_activity(conn, "sensor", sensor_id, "Sensor updated", f"Sensor {sensor['sensor_code']} configuration was updated.", "Info")
            if sensor.get("slot_id"):
                db.log_activity(conn, "slot", sensor["slot_id"], "Sensor assignment updated", f"Sensor {sensor['sensor_code']} is linked to this slot.", "Info")
            return sensor
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.post("/{sensor_id}/simulate", response_model=SensorResponse)
def simulate_sensor(sensor_id: str, payload: SensorSimulationRequest):
    with db.transaction(immediate=True) as conn:
        sensor = conn.execute("SELECT * FROM sensors WHERE sensor_id = ?", (sensor_id,)).fetchone()
        if not sensor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor was not found.")
        if not sensor["is_active"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inactive sensors cannot update occupancy.")
        event_id = db.new_id("evt")
        conn.execute("INSERT INTO sensor_events (event_id, sensor_id, slot_id, reported_status, raw_payload) VALUES (?, ?, ?, ?, ?)", (event_id, sensor_id, sensor["slot_id"], payload.reported_status.value, payload.raw_payload))
        conn.execute("UPDATE sensors SET last_status = ?, last_seen_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'), updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE sensor_id = ?", (payload.reported_status.value, sensor_id))
        if sensor["slot_id"]:
            active = conn.execute("SELECT session_id FROM parking_sessions WHERE slot_id = ? AND status = 'Active'", (sensor["slot_id"],)).fetchone()
            if not active and payload.reported_status.value in ("Clear", "Occupied"):
                new_status = "Available" if payload.reported_status.value == "Clear" else "Occupied"
                conn.execute("UPDATE parking_slots SET status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE slot_id = ? AND status NOT IN ('Reserved','Maintenance','Disabled')", (new_status, sensor["slot_id"]))
            severity = "Warning" if payload.reported_status.value == "Fault" else "Info"
            db.log_activity(conn, "slot", sensor["slot_id"], "Sensor update", f"Sensor reported {payload.reported_status.value}; active-session protection was respected.", severity)
        db.log_activity(conn, "sensor", sensor_id, "Sensor simulation", f"Simulated reading: {payload.reported_status.value}.", "Warning" if payload.reported_status.value == "Fault" else "Info")
        updated = dict(conn.execute(f"{SENSOR_SELECT} WHERE sn.sensor_id = ?", (sensor_id,)).fetchone())
        updated["is_active"] = bool(updated["is_active"])
        return updated


@router.delete("/{sensor_id}")
def delete_sensor(sensor_id: str):
    with db.transaction() as conn:
        cursor = conn.execute("DELETE FROM sensors WHERE sensor_id = ?", (sensor_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor was not found.")
    return {"message": "Sensor deleted.", "sensor_id": sensor_id}
