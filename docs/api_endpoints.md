# API Endpoint List

| Area | Endpoint | Purpose |
|---|---|---|
| System | `GET /api/health` | Health check |
| Auth | `POST /api/auth/login` | Login |
| Auth | `POST /api/auth/register` | Admin/operator registration for setup/demo |
| Dashboard | `GET /api/dashboard` | KPIs, alerts, map, suggestions |
| Lots | `GET/POST /api/lots` | List/create lots |
| Lots | `GET/PUT/DELETE /api/lots/{lot_id}` | Detail/update/delete lot |
| Zones | `GET/POST /api/zones` | List/create zones |
| Zones | `GET/PUT/DELETE /api/zones/{zone_id}` | Detail/update/delete zone |
| Slots | `GET/POST /api/slots` | List/create slots |
| Slots | `GET/PUT/DELETE /api/slots/{slot_id}` | Detail/update/delete slot configuration |
| Slots | `GET /api/slots/{slot_id}/detail` | Slot panel detail with sensor/session/activity |
| Slots | `POST /api/slots/{slot_id}/status` | Audited slot status override |
| Slots | `POST /api/slots/bulk-preview` | Preview bulk slot range |
| Slots | `POST /api/slots/bulk-create` | Create bulk slot range |
| Sensors | `GET/POST /api/sensors` | List/register sensors |
| Sensors | `GET/PUT/DELETE /api/sensors/{sensor_id}` | Detail/update/delete sensor |
| Sensors | `POST /api/sensors/{sensor_id}/simulate` | Simulate sensor event |
| Vehicles | `GET/POST /api/vehicles` | List/register vehicles |
| Vehicles | `GET/PUT/DELETE /api/vehicles/{vehicle_id}` | Detail/update/delete vehicle |
| Sessions | `GET /api/sessions` | List sessions |
| Sessions | `GET /api/sessions/{session_id}` | Session detail |
| Sessions | `POST /api/sessions/start` | Start optimized/manual session |
| Sessions | `POST /api/sessions/{session_id}/exit` | Complete session and calculate fee |
| Sessions | `POST /api/sessions/{session_id}/cancel` | Cancel active session |
| Payments | `GET /api/payments` | List payments |
| Payments | `POST /api/payments/process` | Create/retry payment |
| Payments | `GET /api/payments/receipt/{session_id}` | Receipt data |
| Optimizer | `POST /api/optimizer/recommend` | Explainable slot recommendation |
| Reports | `GET /api/reports/summary` | Report dashboard data |
| Reports | `GET /api/reports/summary.csv` | Summary CSV |
| Reports | `GET /api/reports/payments.csv` | Payments CSV |
| Reports | `GET /api/reports/sessions.csv` | Sessions CSV |
