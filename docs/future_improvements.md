# Future Improvements

## Production-grade backend

- Move from SQLite to PostgreSQL.
- Add Alembic migrations.
- Replace demo bearer tokens with expiring JWTs or secure server-side sessions.
- Add role-based access control for admin, operator, finance, and maintenance roles.
- Add full audit trails with actor, IP/device, before/after values, and immutable storage.

## Live operations

- Use WebSockets or Server-Sent Events for live slot, sensor, and dashboard refresh.
- Add background workers for sensor ingestion and alert generation.
- Add notification routing for low battery, sensor faults, unpaid sessions, and high occupancy.

## Product upgrades

- CSV/PDF report export.
- Reservation workflow.
- License plate recognition integration.
- Real payment gateway integration.
- Interactive floor plan editor.
- Demand forecasting and staffing recommendations.
- Multi-tenant support for operators managing multiple parking companies.

## UX upgrades

- Keyboard shortcuts for operators.
- Advanced filtering/sorting pagination on every table.
- Offline queueing for frontend actions.
- Dark mode.
- Accessibility audit for contrast, focus, and screen reader labels.
