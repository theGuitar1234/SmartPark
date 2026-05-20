# User Manual

## Login

Use the seeded admin account. The login form validates missing email/password and reports backend errors without raw stack traces.

## Dashboard

The dashboard is the operational home screen. It shows live KPIs, occupancy map, active sessions, alerts, optimizer suggestions, revenue trend, and quick actions. Slot tiles are clickable and open the slot detail side panel.

## Zone Management

Use the lot selector, zone selector, slot search, and status filter to inspect the facility. Zone cards show utilization and provide edit/delete actions. The slot grid uses status colors and opens slot detail on click.

## Slot Detail

The side panel shows slot identity, zone/lot, status, type, optimizer scores, current session, sensor assignment, sensor health, recent activity, and sensor events. Invalid operational status changes are blocked when an active session owns the slot.

## Sessions & Payments

Use filters to find active, completed, cancelled, paid, unpaid, pending, failed, and refunded sessions. Active sessions can be exited or cancelled. Completed unpaid or failed sessions can be paid or retried. Receipts are read from backend payment/session data.

## Forms Library

Use the forms to create lots, zones, slots, sensors, tariffs, and manual sessions. Forms include labels, helper text, validation, and success/error feedback.

## System Configuration

System Configuration manages sensor network and tariff plans. Edit, delete, simulate, bulk create, register sensor, and create tariff are all wired to backend endpoints.

## Reports

Reports summarize revenue, sessions, average duration, zone utilization, and payment history. Export report generates backend CSV for summary, payments, or sessions.
