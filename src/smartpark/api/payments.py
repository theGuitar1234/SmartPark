from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .. import db
from ..schemas import PageResponse, PaymentCreate, PaymentResponse
from ..services.payment_service import process_payment
from .deps import get_current_user, handle_integrity_error

router = APIRouter(prefix="/payments", tags=["Payments"], dependencies=[Depends(get_current_user)])

PAYMENT_SELECT = """
SELECT p.*, v.plate_number, ps.fee_amount, ps.payment_status
FROM payments p
JOIN parking_sessions ps ON ps.session_id = p.session_id
JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
"""


@router.get("", response_model=PageResponse)
def list_payments(search: str = "", limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    term = f"%{search.strip().upper()}%"
    return db.paged_query(
        f"{PAYMENT_SELECT} WHERE p.reference_number LIKE ? OR v.plate_number LIKE ? ORDER BY p.created_at DESC",
        "SELECT COUNT(*) FROM payments p JOIN parking_sessions ps ON ps.session_id = p.session_id JOIN vehicles v ON v.vehicle_id = ps.vehicle_id WHERE p.reference_number LIKE ? OR v.plate_number LIKE ?",
        (term, term),
        limit,
        offset,
    )


@router.post("/process", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def process(payload: PaymentCreate):
    try:
        with db.transaction(immediate=True) as conn:
            return process_payment(conn, payload.model_dump(mode="json"))
    except sqlite3.IntegrityError as ex:
        raise handle_integrity_error(ex)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ex))


@router.get("/receipt/{session_id}")
def receipt(session_id: str):
    receipt_data = db.fetch_one(
        """
        SELECT ps.session_id, v.plate_number, v.vehicle_type, s.slot_code, ps.entry_time, ps.exit_time, ps.fee_amount,
               p.payment_id, p.paid_amount, p.method, p.status, p.reference_number, p.paid_at
        FROM parking_sessions ps
        JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
        JOIN parking_slots s ON s.slot_id = ps.slot_id
        LEFT JOIN payments p ON p.session_id = ps.session_id
        WHERE ps.session_id = ?
        """,
        (session_id,),
    )
    if not receipt_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking session was not found.")
    return receipt_data
