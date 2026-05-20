from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import db
from ..schemas import ExitSessionRequest, PageResponse, SessionResponse, StartSessionRequest
from ..services.session_service import cancel_session, exit_session, start_session
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/sessions", tags=["Parking Sessions"], dependencies=[Depends(get_current_user)])

SESSION_SELECT = """
SELECT ps.*, v.plate_number, v.vehicle_type, s.slot_code
FROM parking_sessions ps
JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
JOIN parking_slots s ON s.slot_id = ps.slot_id
"""


@router.get("", response_model=PageResponse)
def list_sessions(search: str = "", status_filter: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    where = "WHERE (v.plate_number LIKE ? OR s.slot_code LIKE ? OR ps.session_id LIKE ?)"
    params: list = [f"%{search.strip().upper()}%", f"%{search.strip().upper()}%", f"%{search.strip()}%"]
    if status_filter:
        where += " AND ps.status = ?"
        params.append(status_filter)
    return db.paged_query(
        f"{SESSION_SELECT} {where} ORDER BY ps.created_at DESC",
        f"SELECT COUNT(*) FROM parking_sessions ps JOIN vehicles v ON v.vehicle_id = ps.vehicle_id JOIN parking_slots s ON s.slot_id = ps.slot_id {where}",
        tuple(params),
        limit,
        offset,
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    session = db.fetch_one(f"{SESSION_SELECT} WHERE ps.session_id = ?", (session_id,))
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking session was not found.")
    return session


@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start(payload: StartSessionRequest):
    try:
        with db.transaction(immediate=True) as conn:
            return start_session(conn, payload.model_dump(mode="json"))
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ex))


@router.post("/{session_id}/exit", response_model=SessionResponse)
def exit_active_session(session_id: str, payload: ExitSessionRequest):
    try:
        with db.transaction(immediate=True) as conn:
            return exit_session(conn, session_id, payload.exit_time)
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ex))


@router.post("/{session_id}/cancel", response_model=SessionResponse)
def cancel_active_session(session_id: str):
    try:
        with db.transaction(immediate=True) as conn:
            return cancel_session(conn, session_id)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ex))
