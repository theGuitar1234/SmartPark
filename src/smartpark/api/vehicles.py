from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import db
from ..schemas import PageResponse, VehicleCreate, VehicleResponse, VehicleUpdate
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/vehicles", tags=["Vehicles"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=PageResponse)
def list_vehicles(search: str = "", limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    term = f"%{search.strip().upper()}%"
    return db.paged_query(
        "SELECT * FROM vehicles WHERE plate_number LIKE ? OR owner_name LIKE ? ORDER BY plate_number",
        "SELECT COUNT(*) FROM vehicles WHERE plate_number LIKE ? OR owner_name LIKE ?",
        (term, f"%{search.strip()}%"),
        limit,
        offset,
    )


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: VehicleCreate):
    vehicle_id = db.new_id("veh")
    try:
        with db.transaction() as conn:
            conn.execute("INSERT INTO vehicles (vehicle_id, plate_number, vehicle_type, owner_name) VALUES (?, ?, ?, ?)", (vehicle_id, payload.plate_number, payload.vehicle_type.value, payload.owner_name.strip()))
            return dict(conn.execute("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,)).fetchone())
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: str):
    vehicle = db.fetch_one("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle was not found.")
    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: str, payload: VehicleUpdate):
    if not db.fetch_one("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle was not found.")
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return get_vehicle(vehicle_id)
    values = {key: (value.value if hasattr(value, "value") else value) for key, value in values.items()}
    assignments = ", ".join([f"{key} = ?" for key in values])
    try:
        with db.transaction() as conn:
            conn.execute(f"UPDATE vehicles SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE vehicle_id = ?", tuple(values.values()) + (vehicle_id,))
            return dict(conn.execute("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,)).fetchone())
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: str):
    try:
        with db.transaction() as conn:
            cursor = conn.execute("DELETE FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle was not found.")
        return {"message": "Vehicle deleted.", "vehicle_id": vehicle_id}
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)
