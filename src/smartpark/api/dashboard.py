from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import db
from .deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)])


@router.get("")
def dashboard():
    with db.get_connection() as conn:
        slot_stats = dict(conn.execute(
            """
            SELECT
                COUNT(*) AS total_slots,
                SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) AS available_slots,
                SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_slots,
                SUM(CASE WHEN status = 'Reserved' THEN 1 ELSE 0 END) AS reserved_slots,
                SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END) AS maintenance_slots,
                SUM(CASE WHEN status = 'Disabled' THEN 1 ELSE 0 END) AS disabled_slots
            FROM parking_slots
            """
        ).fetchone())
        total_slots = slot_stats["total_slots"] or 0
        occupied_slots = slot_stats["occupied_slots"] or 0
        occupancy_rate = round((occupied_slots / total_slots * 100), 2) if total_slots else 0
        revenue = conn.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM payments WHERE status = 'Paid'").fetchone()[0]
        active_sessions = conn.execute("SELECT COUNT(*) FROM parking_sessions WHERE status = 'Active'").fetchone()[0]
        unpaid_sessions = conn.execute("SELECT COUNT(*) FROM parking_sessions WHERE status = 'Completed' AND payment_status IN ('Unpaid','Failed','Pending')").fetchone()[0]
        slot_map = db.rows_to_dicts(conn.execute(
            """
            SELECT s.slot_id, s.slot_code, s.slot_type, s.status, z.name AS zone_name, l.name AS lot_name
            FROM parking_slots s
            JOIN parking_zones z ON z.zone_id = s.zone_id
            JOIN parking_lots l ON l.lot_id = z.lot_id
            ORDER BY l.name, z.name, s.slot_code
            LIMIT 160
            """
        ).fetchall())
        recent_sessions = db.rows_to_dicts(conn.execute(
            """
            SELECT ps.session_id, v.plate_number, s.slot_code, ps.entry_time, ps.exit_time, ps.status, ps.fee_amount, ps.payment_status
            FROM parking_sessions ps
            JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
            JOIN parking_slots s ON s.slot_id = ps.slot_id
            ORDER BY ps.created_at DESC
            LIMIT 8
            """
        ).fetchall())
        zone_stats = db.rows_to_dicts(conn.execute(
            """
            SELECT z.zone_id, z.name, COUNT(s.slot_id) AS total_slots,
                   SUM(CASE WHEN s.status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_slots,
                   SUM(CASE WHEN s.status = 'Available' THEN 1 ELSE 0 END) AS available_slots
            FROM parking_zones z
            LEFT JOIN parking_slots s ON s.zone_id = z.zone_id
            GROUP BY z.zone_id
            ORDER BY z.name
            """
        ).fetchall())
        revenue_series = db.rows_to_dicts(conn.execute(
            """
            SELECT substr(COALESCE(paid_at, created_at), 1, 10) AS day, ROUND(SUM(paid_amount), 2) AS revenue
            FROM payments
            WHERE status = 'Paid'
            GROUP BY substr(COALESCE(paid_at, created_at), 1, 10)
            ORDER BY day DESC
            LIMIT 7
            """
        ).fetchall())
        sensor_faults = conn.execute("SELECT COUNT(*) FROM sensors WHERE is_active = 0 OR last_status = 'Fault' OR battery_level < 20").fetchone()[0]
        sensors_online = conn.execute("SELECT COUNT(*) FROM sensors WHERE is_active = 1 AND last_status != 'Fault' AND battery_level >= 20").fetchone()[0]
        sensors_total = conn.execute("SELECT COUNT(*) FROM sensors").fetchone()[0]
        payment_due = conn.execute("SELECT ROUND(COALESCE(SUM(fee_amount), 0), 2) FROM parking_sessions WHERE status = 'Completed' AND payment_status IN ('Unpaid','Failed','Pending')").fetchone()[0] or 0
        optimizer_suggestions = db.rows_to_dicts(conn.execute(
            """
            SELECT s.slot_id, s.slot_code, s.slot_type, z.name AS zone_name, l.name AS lot_name, s.priority_score, s.distance_score
            FROM parking_slots s
            JOIN parking_zones z ON z.zone_id = s.zone_id
            JOIN parking_lots l ON l.lot_id = z.lot_id
            WHERE s.status = 'Available'
            ORDER BY s.priority_score ASC, s.distance_score ASC, s.slot_code ASC
            LIMIT 5
            """
        ).fetchall())
        sensor_occupied_without_session = conn.execute(
            """
            SELECT COUNT(*)
            FROM sensors sn
            JOIN parking_slots s ON s.slot_id = sn.slot_id
            LEFT JOIN parking_sessions ps ON ps.slot_id = s.slot_id AND ps.status = 'Active'
            WHERE sn.last_status = 'Occupied' AND ps.session_id IS NULL
            """
        ).fetchone()[0]
        active_but_clear = conn.execute(
            """
            SELECT COUNT(*)
            FROM parking_sessions ps
            JOIN sensors sn ON sn.slot_id = ps.slot_id
            WHERE ps.status = 'Active' AND sn.last_status = 'Clear'
            """
        ).fetchone()[0]
        alerts = []
        if unpaid_sessions:
            alerts.append(f"{unpaid_sessions} completed sessions still require payment attention.")
        if sensor_faults:
            alerts.append(f"{sensor_faults} sensors are inactive, faulty, or below 20 percent battery.")
        if sensor_occupied_without_session:
            alerts.append(f"{sensor_occupied_without_session} slots report physical occupancy without an active session.")
        if active_but_clear:
            alerts.append(f"{active_but_clear} active sessions have sensors reporting clear; verify sensor alignment.")
        if occupancy_rate >= 85:
            alerts.append("Occupancy is above 85 percent. Reserve capacity should be monitored.")
        if not alerts:
            alerts.append("No critical operational alerts at the moment.")
        return {
            "total_revenue": round(float(revenue), 2),
            "occupancy_rate": occupancy_rate,
            "active_sessions": active_sessions,
            "slot_stats": slot_stats,
            "slot_map": slot_map,
            "recent_sessions": recent_sessions,
            "zone_stats": zone_stats,
            "revenue_series": revenue_series,
            "alerts": alerts,
            "sensors_online": sensors_online,
            "sensors_total": sensors_total,
            "payment_due": payment_due,
            "optimizer_suggestions": optimizer_suggestions,
        }
