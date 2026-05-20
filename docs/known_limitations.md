# Known Limitations

SmartPark is now product-grade for a local judged demo, but it is not production hardened.

## Local demo limitations

- SQLite is used instead of PostgreSQL.
- Schema creation is migration-ready in structure but does not use Alembic yet.
- Auth uses hashed passwords and bearer demo tokens, but not expiring JWTs or enterprise RBAC.
- Flet screens are synchronous and refresh after actions rather than using live WebSocket updates.
- Sensor input is simulated through API endpoints rather than real hardware ingestion.
- Payment processing is simulated and validates amount/status, but does not integrate a payment provider.
- Export report opens an export-ready UI snapshot instead of writing CSV/PDF directly from the app.
- Activity logs are lightweight and polymorphic; production should implement stronger audit/event modeling.

## What is not a limitation anymore

- The app is not a generic items CRUD scaffold.
- The core session and payment lifecycle is implemented.
- Slot optimization is implemented and explainable.
- Bulk slot creation has duplicate preview and commit flow.
- Slot detail drawer is implemented.
- Sensor assignment and simulation are implemented.
- Reports and receipts are implemented.
- Dashboard and zone map use real backend data.
