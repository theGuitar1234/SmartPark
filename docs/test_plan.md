# SmartPark Test Plan

## Automated test result

Verified command:

```bash
PYTHONPATH=src pytest -q
```

Verified result:

```text
14 passed
```

## Automated coverage

| Area | Test coverage |
|---|---|
| Health endpoint | Confirms public backend health endpoint. |
| Dashboard | Confirms operational metrics and slot map. |
| Vehicle uniqueness | Duplicate plate number rejected. |
| Session lifecycle | Start, duplicate active prevention, exit, fee calculation, payment mismatch rejection, successful payment. |
| Bulk slot preview | Duplicate detection before insert. |
| Sensor uniqueness | Rejects assigning a second sensor to the same slot. |
| Slot detail drawer API | Returns slot, sensor, active session, and activity data. |
| Bulk create + sensor simulation | Creates real slots, assigns sensor, simulates occupancy, verifies persisted slot status. |
| Tariff fee service | Deterministic grace and daily cap behavior. |
| Slot optimizer | Compatibility, exclusions, and no-available-slot behavior. |

## Manual UI checklist

| Check | Expected result |
|---|---|
| Login with admin credentials | Dashboard loads. |
| Login with bad password | Error message shown, no crash. |
| Dashboard quick actions | New session, emergency exit, export report, and add slot open real flows. |
| Occupancy map click | Slot detail drawer opens with real backend data. |
| Slot drawer reserve/release/maintenance | Backend slot status persists and dashboard refreshes. |
| Assign sensor | Sensor assignment persists and uniqueness constraint is respected. |
| Zone selectors | Slot grid updates by selected lot/zone. |
| Bulk slot preview | Shows generated codes and duplicate rows before commit. |
| New session optimizer preview | Shows recommended slot or no-slot explanation. |
| Start session | Vehicle/session persists and slot becomes occupied. |
| Duplicate active vehicle | Backend rejects with useful error. |
| Exit session | Fee is calculated and slot released. |
| Pay session | Payment amount must match fee if status is Paid. |
| Receipt view | Shows reference, plate, slot, fee, method, and status. |
| Sensor simulation | Updates sensor status and eligible slot status. |
| Reports | Revenue/payment rows reflect processed payments. |
| Backend unavailable | UI shows backend-unavailable error state, not raw traceback. |

## Edge cases to test live

- No available compatible slots.
- Duplicate plate number.
- Duplicate slot code.
- Sensor already assigned to a different slot.
- Vehicle already parked.
- Slot already occupied.
- Payment amount mismatch.
- Exit before entry through API.
- Delete zone with slots.
- Delete tariff used by historical sessions.
- Backend stopped while frontend is open.
