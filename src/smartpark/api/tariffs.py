from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import db
from ..schemas import PageResponse, TariffPlanCreate, TariffPlanResponse, TariffPlanUpdate
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/tariffs", tags=["Tariff Plans"], dependencies=[Depends(get_current_user)])

TARIFF_SELECT = """
SELECT t.*, z.name AS zone_name
FROM tariff_plans t
LEFT JOIN parking_zones z ON z.zone_id = t.zone_id
"""


@router.get("", response_model=PageResponse)
def list_tariffs(search: str = "", limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    term = f"%{search.strip()}%"
    return db.paged_query(
        f"{TARIFF_SELECT} WHERE t.name LIKE ? OR COALESCE(z.name, '') LIKE ? ORDER BY t.is_active DESC, t.name",
        "SELECT COUNT(*) FROM tariff_plans t LEFT JOIN parking_zones z ON z.zone_id = t.zone_id WHERE t.name LIKE ? OR COALESCE(z.name, '') LIKE ?",
        (term, term),
        limit,
        offset,
    )


@router.get("/{tariff_id}", response_model=TariffPlanResponse)
def get_tariff(tariff_id: str):
    tariff = db.fetch_one(f"{TARIFF_SELECT} WHERE t.tariff_id = ?", (tariff_id,))
    if not tariff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan was not found.")
    tariff["is_active"] = bool(tariff["is_active"])
    return tariff


@router.post("", response_model=TariffPlanResponse, status_code=status.HTTP_201_CREATED)
def create_tariff(payload: TariffPlanCreate):
    tariff_id = db.new_id("tariff")
    try:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO tariff_plans (tariff_id, name, hourly_rate, grace_minutes, daily_max, vehicle_type, zone_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (tariff_id, payload.name.strip(), payload.hourly_rate, payload.grace_minutes, payload.daily_max, payload.vehicle_type.value if payload.vehicle_type else None, payload.zone_id, int(payload.is_active)),
            )
            tariff = dict(conn.execute(f"{TARIFF_SELECT} WHERE t.tariff_id = ?", (tariff_id,)).fetchone())
            tariff["is_active"] = bool(tariff["is_active"])
            return tariff
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.put("/{tariff_id}", response_model=TariffPlanResponse)
def update_tariff(tariff_id: str, payload: TariffPlanUpdate):
    if not db.fetch_one("SELECT * FROM tariff_plans WHERE tariff_id = ?", (tariff_id,)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan was not found.")
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return get_tariff(tariff_id)
    values = {key: (value.value if hasattr(value, "value") else value) for key, value in values.items()}
    values = {key: (int(value) if isinstance(value, bool) else value) for key, value in values.items()}
    assignments = ", ".join([f"{key} = ?" for key in values])
    try:
        with db.transaction() as conn:
            conn.execute(f"UPDATE tariff_plans SET {assignments}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE tariff_id = ?", tuple(values.values()) + (tariff_id,))
            tariff = dict(conn.execute(f"{TARIFF_SELECT} WHERE t.tariff_id = ?", (tariff_id,)).fetchone())
            tariff["is_active"] = bool(tariff["is_active"])
            return tariff
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)


@router.delete("/{tariff_id}")
def delete_tariff(tariff_id: str):
    try:
        with db.transaction() as conn:
            cursor = conn.execute("DELETE FROM tariff_plans WHERE tariff_id = ?", (tariff_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan was not found.")
        return {"message": "Tariff plan deleted.", "tariff_id": tariff_id}
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)
