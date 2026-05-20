from __future__ import annotations

from typing import Any

COMPATIBILITY = {
    "Car": ["Standard", "VIP"],
    "Motorcycle": ["Motorcycle", "Standard"],
    "EV": ["EV", "VIP"],
    "Disabled Access": ["Disabled Access"],
    "Truck": ["Truck"],
    "VIP": ["VIP", "Standard"],
}


def compatibility_penalty(vehicle_type: str, slot_type: str) -> int:
    options = COMPATIBILITY.get(vehicle_type, ["Standard"])
    if not options:
        return 1000
    if slot_type == options[0]:
        return 0
    if slot_type in options:
        return 15
    return 1000


def find_best_slot(conn, vehicle_type: str, zone_id: str | None = None) -> dict[str, Any]:
    params: list[Any] = []
    zone_filter = ""
    if zone_id:
        zone_filter = "AND s.zone_id = ?"
        params.append(zone_id)
    rows = conn.execute(
        f"""
        SELECT
            s.slot_id,
            s.zone_id,
            s.slot_code,
            s.slot_type,
            s.status,
            s.distance_score,
            s.priority_score,
            z.name AS zone_name,
            z.priority_score AS zone_priority,
            l.name AS lot_name,
            sn.sensor_code,
            sn.is_active AS sensor_is_active,
            sn.last_status AS sensor_last_status,
            (
                SELECT COUNT(*) FROM parking_slots zs WHERE zs.zone_id = s.zone_id
            ) AS zone_total,
            (
                SELECT COUNT(*) FROM parking_slots zs WHERE zs.zone_id = s.zone_id AND zs.status = 'Occupied'
            ) AS zone_occupied
        FROM parking_slots s
        JOIN parking_zones z ON z.zone_id = s.zone_id
        JOIN parking_lots l ON l.lot_id = z.lot_id
        LEFT JOIN sensors sn ON sn.slot_id = s.slot_id
        WHERE s.status = 'Available' {zone_filter}
        ORDER BY s.slot_code
        """,
        tuple(params),
    ).fetchall()
    candidates = []
    explanations = []
    for row in rows:
        slot = dict(row)
        penalty = compatibility_penalty(vehicle_type, slot["slot_type"])
        if penalty >= 1000:
            continue
        zone_occupancy = 0
        if slot["zone_total"]:
            zone_occupancy = (slot["zone_occupied"] / slot["zone_total"]) * 100
        sensor_penalty = 0
        if not slot["sensor_code"]:
            sensor_penalty = 8
        elif not slot["sensor_is_active"]:
            sensor_penalty = 12
        elif slot["sensor_last_status"] == "Fault":
            sensor_penalty = 20
        score = round(penalty + slot["distance_score"] * 0.35 + slot["priority_score"] * 0.25 + slot["zone_priority"] * 0.2 + zone_occupancy * 0.2 + sensor_penalty, 2)
        slot["score_breakdown"] = {
            "compatibility_penalty": penalty,
            "distance_component": round(slot["distance_score"] * 0.35, 2),
            "slot_priority_component": round(slot["priority_score"] * 0.25, 2),
            "zone_priority_component": round(slot["zone_priority"] * 0.2, 2),
            "occupancy_balance_component": round(zone_occupancy * 0.2, 2),
            "sensor_penalty": sensor_penalty,
            "total_score": score,
        }
        candidates.append(slot)
    candidates.sort(key=lambda item: (item["score_breakdown"]["total_score"], item["slot_code"]))
    if not candidates:
        message = "No compatible available slot was found for the requested vehicle type."
        if zone_id:
            message += " The selected zone may be full, incompatible, reserved, disabled, or under maintenance."
        return {"slot": None, "candidates_considered": len(rows), "explanation": [message], "score_breakdown": None}
    selected = candidates[0]
    explanations.append(f"Selected {selected['slot_code']} because it is available and compatible with {vehicle_type}.")
    explanations.append("Reserved, disabled, maintenance, and occupied slots were excluded before scoring.")
    explanations.append("Lower score wins: compatibility, shorter walking distance, configured priority, zone balance, and sensor health are considered.")
    return {
        "slot": {k: v for k, v in selected.items() if k != "score_breakdown"},
        "candidates_considered": len(candidates),
        "explanation": explanations,
        "score_breakdown": selected["score_breakdown"],
    }
