from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import db
from ..schemas import PageResponse, ParkingZoneCreate, ParkingZoneResponse, ParkingZoneUpdate
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/zones", tags=["Parking Zones"], dependencies=[Depends(get_current_user)])

ZONE_SELECT = """
SELECT z.*, l.name AS lot_name
FROM parking_zones z
JOIN parking_lots l ON l.lot_id = z.lot_id
"""


@router.get("", response_model=PageResponse)
def list_zones(search: str = "", lot_id: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    where = "WHERE (z.name LIKE ? OR l.name LIKE ?)"
    params: list = [f"%{search.strip()}%", f"%{search.strip()}%"]
    if lot_id:
        where += " AND z.lot_id = ?"
        params.append(lot_id)
    return db.paged_query(
        f"{ZONE_SELECT} {where} ORDER BY l.name, z.floor_level, z.name",
        f"SELECT COUNT(*) FROM parking_zones z JOIN parking_lots l ON l.lot_id = z.lot_id {where}",
        tuple(params),
        limit,
        offset,
    )


@router.get("/{zone_id}", response_model=ParkingZoneResponse)
def get_zone(zone_id: str):
    zone = db.fetch_one(f"{ZONE_SELECT} WHERE z.zone_id = ?", (zone_id,))
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking zone was not found.")
    return zone


@router.post("", response_model=ParkingZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(payload: ParkingZoneCreate):
    zone_id = db.new_id("zone")
    try:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO parking_zones (zone_id, lot_id, name, floor_level, zone_type, priority_score) VALUES (?, ?, ?, ?, ?, ?)",
                (zone_id, payload.lot_id, payload.name.strip(), payload.floor_level, payload.zone_type.value, payload.priority_score),
            )
            return dict(conn.execute(f"{ZONE_SELECT} WHERE z.zone_id = ?", (zone_id,)).fetchone())
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.put("/{zone_id}", response_model=ParkingZoneResponse)
def update_zone(zone_id: str, payload: ParkingZoneUpdate):
    current = db.fetch_one("SELECT * FROM parking_zones WHERE zone_id = ?", (zone_id,))
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking zone was not found.")
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return get_zone(zone_id)
    values = {key: (value.value if hasattr(value, "value") else value) for key, value in values.items()}
    assignments = ", ".join([f"{key} = ?" for key in values])
    params = tuple(value.strip() if isinstance(value, str) else value for value in values.values()) + (zone_id,)
    try:
        with db.transaction() as conn:
            conn.execute(f"UPDATE parking_zones SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE zone_id = ?", params)
            return dict(conn.execute(f"{ZONE_SELECT} WHERE z.zone_id = ?", (zone_id,)).fetchone())
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.delete("/{zone_id}")
def delete_zone(zone_id: str):
    try:
        with db.transaction() as conn:
            cursor = conn.execute("DELETE FROM parking_zones WHERE zone_id = ?", (zone_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking zone was not found.")
        return {"message": "Parking zone deleted.", "zone_id": zone_id}
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)
