# Draw.io ERD Guidance

A safe Draw.io XML file is not included because hand-generated Draw.io XML is easy to corrupt and harder to maintain than the Mermaid and DBML sources.

Use either of these reliable options:

1. Open diagrams.net.
2. Choose Insert, Advanced, Mermaid.
3. Paste `docs/erd.mmd`.
4. Alternatively, open dbdiagram.io and paste `docs/schema.dbml`.

Recommended layout:

- Put `parking_lots`, `parking_zones`, and `parking_slots` in the center-left physical asset chain.
- Put `sensors` and `sensor_events` below slots.
- Put `vehicles`, `parking_sessions`, and `payments` in the center-right operational chain.
- Put `tariff_plans` above sessions.
- Put `users` and `auth_tokens` in the upper corner because they support access control rather than parking operations.

Use crow's-foot notation. Mark optional relationships clearly for sensor assignment and payments.
