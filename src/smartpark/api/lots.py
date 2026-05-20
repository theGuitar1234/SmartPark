from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import db
from ..schemas import ParkingLotCreate, ParkingLotResponse, ParkingLotUpdate, PageResponse
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/lots", tags=["Parking Lots"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=PageResponse)
def list_lots(search: str = "", limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    term = f"%{search.strip()}%"
    return db.paged_query(
        "SELECT * FROM parking_lots WHERE name LIKE ? OR address LIKE ? ORDER BY name",
        "SELECT COUNT(*) FROM parking_lots WHERE name LIKE ? OR address LIKE ?",
        (term, term),
        limit,
        offset,
    )


@router.get("/{lot_id}", response_model=ParkingLotResponse)
def get_lot(lot_id: str):
    lot = db.fetch_one("SELECT * FROM parking_lots WHERE lot_id = ?", (lot_id,))
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking lot was not found.")
    return lot


@router.post("", response_model=ParkingLotResponse, status_code=status.HTTP_201_CREATED)
def create_lot(payload: ParkingLotCreate):
    lot_id = db.new_id("lot")
    try:
        with db.transaction() as conn:
            conn.execute("INSERT INTO parking_lots (lot_id, name, address, description) VALUES (?, ?, ?, ?)", (lot_id, payload.name.strip(), payload.address.strip(), payload.description.strip()))
            return dict(conn.execute("SELECT * FROM parking_lots WHERE lot_id = ?", (lot_id,)).fetchone())
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.put("/{lot_id}", response_model=ParkingLotResponse)
def update_lot(lot_id: str, payload: ParkingLotUpdate):
    current = db.fetch_one("SELECT * FROM parking_lots WHERE lot_id = ?", (lot_id,))
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking lot was not found.")
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return current
    assignments = ", ".join([f"{key} = ?" for key in values])
    params = tuple(value.strip() if isinstance(value, str) else value for value in values.values()) + (lot_id,)
    try:
        with db.transaction() as conn:
            conn.execute(f"UPDATE parking_lots SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE lot_id = ?", params)
            return dict(conn.execute("SELECT * FROM parking_lots WHERE lot_id = ?", (lot_id,)).fetchone())
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.delete("/{lot_id}")
def delete_lot(lot_id: str):
    try:
        with db.transaction() as conn:
            cursor = conn.execute("DELETE FROM parking_lots WHERE lot_id = ?", (lot_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking lot was not found.")
        return {"message": "Parking lot deleted.", "lot_id": lot_id}
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)
