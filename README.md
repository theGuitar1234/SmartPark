# SmartPark

SmartPark is a local, demo-ready parking operations dashboard built with FastAPI, SQLite, and Flet. It manages parking lots, zones, slots, sensors, vehicles, sessions, tariffs, payments, optimizer-based slot assignment, and reports.

## Current hardening pass

This pass focused on application quality rather than documentation volume. The frontend now behaves like an operations product instead of a CRUD scaffold:

- Branded login with demo credentials, validation, loading, and clean error states.
- Dashboard with revenue, occupancy, active sessions, available slots, sensor health, payment due, occupancy map, active sessions, alerts, optimizer suggestions, and wired quick actions.
- Zone Management with persistent lot/zone selection, filters, zone cards, utilization, slot map, add/edit/delete zone actions, selected-zone slot creation, bulk creation, and side-panel slot details.
- Slot detail side panel with configuration, current session, current vehicle, sensor health, sensor simulation, conflict warnings, recent activity, and guarded actions.
- Sessions & Payments with filters, active exit/cancel actions, retryable payment processing, receipt view, and status badges.
- System Configuration with real sensor/tariff tables, edit/delete actions, sensor simulation, bulk creation, and no decorative fake switches.
- Reports with real backend-generated CSV exports for summary, payments, and sessions.

## Requirements

- Python 3.11 or newer.
- Local SQLite database.
- Python packages from `requirements.txt`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run backend

```bash
PYTHONPATH=src uvicorn smartpark.backend_app:app --reload --port 8000
```

The API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Run frontend

Native Flet window:

```bash
PYTHONPATH=src python -m smartpark.frontend_app
```

Browser mode:

```bash
SMARTPARK_FLET_VIEW=web FLET_PORT=8550 PYTHONPATH=src python -m smartpark.frontend_app
```

## Demo login

```text
Email: admin@smartpark.com
Password: admin1234
```

## Test

```bash
PYTHONPATH=src pytest -q
```

Verified result in this hardening pass:

```text
17 passed
```

## Main demo flow

1. Login as admin.
2. Review dashboard KPIs, occupancy map, operational alerts, active sessions, and optimizer suggestions.
3. Open a slot from the occupancy map and review the side-panel detail view.
4. Simulate sensor clear/occupied/fault and see persisted state changes.
5. Use Zone Management to filter slots, add a slot, and bulk create a range.
6. Start an optimized session from Dashboard or Sessions & Payments.
7. Exit an active session and confirm deterministic fee calculation.
8. Process payment and open receipt.
9. Export reports as backend-generated CSV snapshots.

## Local demo boundaries

SmartPark is production-shaped but intentionally local. It uses SQLite, simple token authentication, and simulated sensors/payments. A production deployment would replace those with PostgreSQL, migrations, RBAC, live sensor ingestion, real payment gateway integration, and observability.
