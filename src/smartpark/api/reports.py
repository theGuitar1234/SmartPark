from __future__ import annotations

from io import StringIO
import csv

from fastapi import APIRouter, Depends, Response

from .. import db
from .deps import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(get_current_user)])


def report_payload() -> dict:
    with db.get_connection() as conn:
        revenue = conn.execute("SELECT ROUND(COALESCE(SUM(paid_amount), 0), 2) FROM payments WHERE status = 'Paid'").fetchone()[0]
        session_count = conn.execute("SELECT COUNT(*) FROM parking_sessions").fetchone()[0]
        avg_duration = conn.execute(
            """
            SELECT ROUND(AVG((julianday(exit_time) - julianday(entry_time)) * 24 * 60), 2)
            FROM parking_sessions
            WHERE status = 'Completed' AND exit_time IS NOT NULL
            """
        ).fetchone()[0]
        by_zone = db.rows_to_dicts(conn.execute(
            """
            SELECT z.name AS zone_name,
                   l.name AS lot_name,
                   COUNT(DISTINCT s.slot_id) AS total_slots,
                   SUM(CASE WHEN s.status = 'Available' THEN 1 ELSE 0 END) AS available_slots,
                   SUM(CASE WHEN s.status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_slots,
                   COUNT(ps.session_id) AS session_count,
                   ROUND(COALESCE(SUM(ps.fee_amount), 0), 2) AS calculated_revenue,
                   ROUND(SUM(CASE WHEN s.status = 'Occupied' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(DISTINCT s.slot_id), 0), 2) AS current_utilization
            FROM parking_zones z
            JOIN parking_lots l ON l.lot_id = z.lot_id
            LEFT JOIN parking_slots s ON s.zone_id = z.zone_id
            LEFT JOIN parking_sessions ps ON ps.slot_id = s.slot_id
            GROUP BY z.zone_id
            ORDER BY l.name, z.name
            """
        ).fetchall())
        payments = db.rows_to_dicts(conn.execute(
            """
            SELECT p.reference_number, v.plate_number, s.slot_code, p.method, p.status, p.paid_amount, p.paid_at
            FROM payments p
            JOIN parking_sessions ps ON ps.session_id = p.session_id
            JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
            JOIN parking_slots s ON s.slot_id = ps.slot_id
            ORDER BY p.created_at DESC
            LIMIT 200
            """
        ).fetchall())
        sessions = db.rows_to_dicts(conn.execute(
            """
            SELECT ps.session_id, v.plate_number, s.slot_code, ps.entry_time, ps.exit_time, ps.status, ps.fee_amount, ps.payment_status
            FROM parking_sessions ps
            JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
            JOIN parking_slots s ON s.slot_id = ps.slot_id
            ORDER BY ps.created_at DESC
            LIMIT 200
            """
        ).fetchall())
        return {
            "total_revenue": revenue or 0,
            "session_count": session_count,
            "average_completed_duration_minutes": avg_duration or 0,
            "zone_utilization": by_zone,
            "payments": payments,
            "sessions": sessions,
        }


def to_csv(filename: str, rows: list[dict]) -> Response:
    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("message\nNo rows available\n")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(output.getvalue(), media_type="text/csv", headers=headers)


@router.get("/summary")
def summary_report():
    return report_payload()


@router.get("/summary.csv")
def summary_csv():
    payload = report_payload()
    rows = [
        {"metric": "total_revenue", "value": payload["total_revenue"]},
        {"metric": "session_count", "value": payload["session_count"]},
        {"metric": "average_completed_duration_minutes", "value": payload["average_completed_duration_minutes"]},
    ]
    return to_csv("smartpark-summary.csv", rows)


@router.get("/payments.csv")
def payments_csv():
    return to_csv("smartpark-payments.csv", report_payload()["payments"])


@router.get("/sessions.csv")
def sessions_csv():
    return to_csv("smartpark-sessions.csv", report_payload()["sessions"])
