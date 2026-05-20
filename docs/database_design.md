# SmartPark Database Design Document

## Normalized ERD summary

The final model separates physical assets, operational events, pricing, and settlement. A parking lot contains zones; a zone contains slots; a slot can have one sensor; a vehicle can create many parking sessions; each session uses one tariff snapshot; a completed session can have one payment.

## Entity dictionary

| Entity | Purpose |
|---|---|
| `users` | Stores admin/operator accounts for demo authentication. |
| `auth_tokens` | Stores demo bearer tokens issued after login. |
| `parking_lots` | Represents a physical parking facility. |
| `parking_zones` | Represents a logical/floor section inside a lot. |
| `parking_slots` | Represents an individual assignable parking space. |
| `sensors` | Represents hardware units that report occupancy or faults. |
| `vehicles` | Represents unique vehicles by plate number. |
| `tariff_plans` | Defines pricing rules, optionally scoped by vehicle type and zone. |
| `parking_sessions` | Represents vehicle entry-to-exit parking usage. |
| `payments` | Represents financial settlement for completed sessions. |
| `sensor_events` | Stores sensor updates for traceability and debugging. |

## Relationship table

| Parent | Child | Relationship | Rationale |
|---|---|---:|---|
| `parking_lots` | `parking_zones` | 1:N | A facility has multiple zones; a zone belongs to one facility. |
| `parking_zones` | `parking_slots` | 1:N | A zone has multiple spaces; a slot belongs to one zone. |
| `parking_slots` | `sensors` | 1:0..1 | A slot may have one sensor; a sensor may be temporarily unassigned. |
| `vehicles` | `parking_sessions` | 1:N | Vehicles can park many times historically. |
| `parking_slots` | `parking_sessions` | 1:N | Slots are reused across time, but only one active session is allowed. |
| `tariff_plans` | `parking_sessions` | 1:N | Many sessions can use the same plan; snapshot fields preserve historical pricing. |
| `parking_sessions` | `payments` | 1:0..1 | A session may be unpaid, failed, pending, or paid later. |
| `sensors` | `sensor_events` | 1:N | A sensor emits many readings over time. |
| `parking_slots` | `sensor_events` | 1:N | Sensor events are tied to the affected slot when available. |

## Cardinality table

| Relationship | Minimum | Maximum | Enforced by |
|---|---:|---:|---|
| Lot to zones | 0 | Many | `parking_zones.lot_id` FK |
| Zone to slots | 0 | Many | `parking_slots.zone_id` FK |
| Slot to sensor | 0 | 1 | `sensors.slot_id UNIQUE` |
| Vehicle to active sessions | 0 | 1 | Partial unique index on active sessions |
| Slot to active sessions | 0 | 1 | Partial unique index on active sessions |
| Session to payment | 0 | 1 | `payments.session_id UNIQUE` |
| Tariff to sessions | 0 | Many | `parking_sessions.tariff_id` FK |

## Field dictionary

| Table | Key fields | Important validation |
|---|---|---|
| `users` | `user_id`, `email`, `password_hash`, `role` | Unique email, role check, hashed password only. |
| `parking_lots` | `lot_id`, `name`, `address` | Unique lot name. |
| `parking_zones` | `zone_id`, `lot_id`, `name`, `floor_level`, `zone_type` | Unique `(lot_id, name)`, zone type check, priority range. |
| `parking_slots` | `slot_id`, `zone_id`, `slot_code`, `slot_type`, `status` | Unique slot code, status/type checks, score ranges. |
| `sensors` | `sensor_id`, `sensor_code`, `slot_id`, `last_status` | Unique sensor code, unique slot assignment, battery range. |
| `vehicles` | `vehicle_id`, `plate_number`, `vehicle_type` | Unique normalized plate, vehicle type check. |
| `tariff_plans` | `tariff_id`, `hourly_rate`, `grace_minutes`, `daily_max` | Non-negative rates, optional vehicle/zone scope. |
| `parking_sessions` | `session_id`, `vehicle_id`, `slot_id`, `tariff_id`, `entry_time`, `exit_time`, `status`, `fee_amount` | Exit after entry, active vehicle/slot uniqueness, tariff snapshots. |
| `payments` | `payment_id`, `session_id`, `paid_amount`, `method`, `status` | One payment per session, paid amount validated in service. |
| `sensor_events` | `event_id`, `sensor_id`, `slot_id`, `reported_status` | Status check, FK traceability. |

## Constraints table

| Constraint | Implementation | Reason |
|---|---|---|
| Unique plate number | `vehicles.plate_number UNIQUE` | Prevents duplicate active identity. |
| Unique slot code | `parking_slots.slot_code UNIQUE` | Slot codes must be human-stable labels. |
| One active session per vehicle | Partial unique index where `status='Active'` | Blocks double parking. |
| One active session per slot | Partial unique index where `status='Active'` | Blocks double assignment. |
| One sensor per slot | `sensors.slot_id UNIQUE` | Avoids conflicting sensor authority. |
| One payment per session | `payments.session_id UNIQUE` | Prevents double settlement. |
| FK enforcement | `PRAGMA foreign_keys = ON` per connection | Prevents orphan data. |
| Status validity | SQLite `CHECK` constraints | Prevents invalid enum values. |
| Exit after entry | Session table `CHECK(exit_time IS NULL OR exit_time > entry_time)` plus service validation | Prevents negative durations. |

## Business rules table

| Rule | Implementation |
|---|---|
| Available, Occupied, Reserved, Maintenance, Disabled slot statuses | `parking_slots.status` check and API validation. |
| Active session locks slot | `start_session` updates slot to `Occupied` inside `BEGIN IMMEDIATE` transaction. |
| Completed session releases slot | `exit_session` updates slot to `Available`. |
| Vehicle cannot have two active sessions | Partial unique index and service pre-check. |
| Slot cannot have two active sessions | Partial unique index and service pre-check. |
| Payment amount must match fee | `payment_service.process_payment` rejects mismatch for `Paid` payments. |
| Tariff changes should not alter active/historical sessions | Session stores tariff snapshot fields. |
| Sensor cannot override active session release | Sensor clear event does not free a slot with an active session. |
| Maintenance/reserved/disabled slots are excluded from optimizer | Optimizer filters `status='Available'` before scoring. |

## Design choices

Payment is separate from session because parking usage and financial settlement are different lifecycles. A session can be completed but unpaid; a payment can fail; a refund can occur. Combining them would make those states ambiguous.

Sensor is separate from slot because sensors are physical hardware assets. They can be replaced, deactivated, unassigned, or faulty without deleting the slot. This also lets the system record sensor health and history.

Tariff is snapshot into sessions because prices can change while a vehicle is parked. The session must remain financially explainable after the tariff plan changes.

SQLite foreign keys are enabled on every connection. Without that, SQLite accepts FK declarations but does not enforce them by default in many environments.

## Second-pass schema addition: ActivityLog

The second-pass rebuild adds `activity_logs` because the slot detail drawer needs meaningful operational history. Without this table, the drawer would only be a static slot record and would feel like CRUD. Activity logs record slot, sensor, session, and payment events such as session start, session exit, payment processed, sensor simulation, manual status override, and bulk slot creation.

| Entity | Purpose |
|---|---|
| ActivityLog | Lightweight event stream for drawer history and operator traceability. |

| Field | Purpose |
|---|---|
| activity_id | Primary key. |
| entity_type | Logical source such as `slot`, `sensor`, `session`, or `zone`. |
| entity_id | ID of the related entity. Not a strict foreign key because it can point to multiple entity tables. |
| title | Short event title shown in the drawer. |
| message | Human-readable operational explanation. |
| severity | Info, Success, Warning, or Critical. |
| created_at | Timestamp for ordering activity history. |

The design intentionally avoids one polymorphic foreign key because SQLite cannot enforce a foreign key that targets multiple tables. For a local demo this is acceptable; in production this would become typed audit tables or a stronger event/audit model.
