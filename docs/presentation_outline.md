# Presentation Outline

1. Problem: parking operations need live occupancy, sensor trust checks, deterministic fees, and auditable payments.
2. Product: SmartPark operations console.
3. Stack: FastAPI backend, SQLite local database, Flet Python frontend.
4. Architecture: API-first frontend with a small client layer; business rules live in backend services.
5. Database: lots, zones, slots, sensors, vehicles, sessions, tariffs, payments, sensor events, activity logs.
6. Dashboard: KPIs, occupancy map, active sessions, alerts, revenue trend, optimizer suggestions.
7. Slot detail: side panel with session, sensor, scoring, actions, conflicts, and history.
8. Optimizer: excludes invalid slots, scores compatible candidates by type, zone, priority, distance, occupancy balance, and sensor health.
9. Fee calculation: tariff snapshot preserved on session entry, deterministic exit calculation.
10. Payment workflow: completed sessions become payable; failed/pending payments can be retried; receipts are backend-driven.
11. Reports: summary, utilization, payments, and CSV exports.
12. Testing: 17 passing automated tests plus manual smoke probes for visible flows.
13. Limitations: local-demo auth, simulated sensors/payments, SQLite rather than production DB.
