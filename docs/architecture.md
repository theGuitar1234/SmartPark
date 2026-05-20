# SmartPark Architecture Overview

SmartPark is organized as a local, presentable, class-demo application with production-style boundaries.

## Runtime shape

The backend is a FastAPI application. It owns validation, persistence, fee calculation, optimizer logic, authentication, and business rules. The frontend is a Flet application that communicates with the backend through `frontend/api_client.py`; it does not duplicate business rules.

The recommended demo mode is two-process local execution:

1. Start FastAPI on port `8000`.
2. Start Flet web on port `8550`.
3. Flet calls `http://127.0.0.1:8000/api` unless `SMARTPARK_API_URL` overrides it.

A combined ASGI entry point is also present in `smartpark.main`, but the two-process mode is simpler to defend and debug during evaluation.

## Package structure

```text
src/smartpark/
  backend_app.py           FastAPI app factory and router registration
  main.py                  Optional combined ASGI entry
  db.py                    SQLite connection, schema initialization, seed data
  schemas.py               Pydantic request and response models
  security.py              Password hashing and token generation
  api/                     Organized FastAPI routers
  services/                Domain business logic
  frontend/                Flet app, state, API client, UI helpers
  sql/schema.sql           SQL DDL
```

## Design principles

The backend is the source of truth. Session start, exit, payment validation, sensor updates, and slot optimization all happen in backend services. The frontend only sends intent: create this lot, start this session, simulate this sensor, process this payment.

SQLite is used because the project must be runnable locally without external infrastructure. The schema uses foreign keys, check constraints, unique constraints, and partial unique indexes. The upgrade path is PostgreSQL because the relational model is already normalized and migration-friendly.

## Why FastAPI

FastAPI gives clean routing, validation through Pydantic models, automatic OpenAPI documentation, and straightforward testing through `TestClient`. It is appropriate for a Python student project that still needs professional API structure.

## Why Flet

Flet keeps the entire student project in Python while still producing a desktop/web admin dashboard. That fits the class/demo requirement and avoids a separate JavaScript stack. The design is intentionally admin-oriented: navigation rail, dashboard cards, occupancy grid, tables, dialogs, and form workflows.

## Why SQLite

SQLite is a correct local choice because this is a single-machine demo application. It has real foreign key support, check constraints, unique constraints, transactions, and partial unique indexes. The backend enables `PRAGMA foreign_keys = ON` for every connection.

## Scaling path

For production, the main changes would be PostgreSQL, Alembic migrations, real JWT or OAuth2 authentication, server-side RBAC, background sensor ingestion, WebSocket/SSE live updates, audit logs, payment gateway integration, and deployment behind a reverse proxy.

## Second-pass frontend architecture

The Flet frontend now has a product shell instead of a developer CRUD shell. The main app file composes a persistent sidebar, topbar, reusable panels, badges, cards, modals, tables, slot tiles, and workflow forms. Styling is centralized in `src/smartpark/frontend/design.py` so colors, radius, spacing, buttons, and status badges are consistent across screens.

The frontend talks to the backend through `SmartParkClient` only. Core UI actions are not frontend-only illusions: slot status changes, sensor assignment, sensor simulation, optimized session start, session exit, payment processing, receipts, dashboard metrics, and reports all use FastAPI endpoints and SQLite persistence.

## Product screen map

| Screen | Backend dependencies |
|---|---|
| Dashboard | `/dashboard`, `/sessions`, `/slots`, `/reports/summary`, `/payments/receipt/{session_id}` |
| Zone Management | `/lots`, `/zones`, `/slots`, `/slots/{slot_id}/detail` |
| Slot Drawer | `/slots/{slot_id}/detail`, `/slots/{slot_id}/status`, `/slots/{slot_id}`, `/sensors/{sensor_id}`, `/sensors/{sensor_id}/simulate` |
| Sessions & Payments | `/sessions`, `/sessions/start`, `/sessions/{id}/exit`, `/sessions/{id}/cancel`, `/payments/process`, `/payments/receipt/{id}` |
| Forms Library | Domain create/update endpoints across lots, zones, slots, sensors, tariffs, sessions |
| System Configuration | `/dashboard`, `/sensors`, `/tariffs`, `/slots/bulk-preview`, `/slots/bulk-create` |
| Reports | `/reports/summary` |
