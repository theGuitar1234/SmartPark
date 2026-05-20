# Speaker Notes

## Why separate payment from session?

A session is the parking lifecycle. A payment is the financial settlement. Keeping them separate allows unpaid, failed, pending, refunded, and paid states without corrupting the session history.

## Why separate sensor from slot?

A slot is a physical bay. A sensor is hardware that can fail, be reassigned, or report suspicious data. Separating them lets the system detect sensor/occupancy conflicts.

## What happens if a sensor lies?

Sensor events are recorded, slot state is updated only when eligible, and the dashboard/slot panel surfaces conflicts such as sensor-occupied without an active session or active session with sensor clear.

## What happens if two users assign the same slot?

The backend uses immediate transactions and partial unique indexes for active session vehicle/slot constraints. UI optimism does not override database integrity.

## Why SQLite?

For a local judged demo, SQLite is simple, reproducible, and easy to reset. Foreign keys are enabled per connection. Production would move to PostgreSQL and migrations.

## Why FastAPI?

FastAPI gives typed request validation, clear OpenAPI docs, organized routers, and clean HTTP status handling.

## Why Flet?

Flet allows a Python-native admin UI while still producing a desktop/web-like dashboard. It fits a Python project without introducing a separate JavaScript stack.
