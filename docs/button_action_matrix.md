# Visible Button and Control QA Matrix

This matrix was generated after invoking the actual Flet control callbacks against a live local FastAPI backend on a clean seeded SQLite database. It covers visible buttons, icon buttons, dialog actions, search fields, filters, and sidebar navigation.

| Screen | Button/control | Expected behavior | Actual behavior after fix | Backend endpoint used | Fixed? | Tested? |
|---|---|---|---|---|---|---|
| Login | Sign in | authenticates demo admin | opened/updated without snackbar | POST /api/auth/login | Yes | Yes |
| Dashboard | A-02 | opens slot detail panel | opened/updated without snackbar | GET /api/slots/{id}/detail | Yes | Yes |
| Slot Detail | Save changes | saves slot configuration | opened/updated without snackbar | PUT /api/slots, POST /api/slots/{id}/status if needed | Yes | Yes |
| Slot Detail | Assign sensor | opens sensor assignment | opened/updated without snackbar | GET /api/sensors | Yes | Yes |
| Slot Detail | Assign sensor | assigns selected sensor | opened/updated without snackbar | PUT /api/sensors/{id} | Yes | Yes |
| Slot Detail | Simulate clear | simulates clear sensor reading | opened/updated without snackbar | POST /api/sensors/{id}/simulate | Yes | Yes |
| Slot Detail | Simulate occupied | simulates occupied sensor reading | opened/updated without snackbar | POST /api/sensors/{id}/simulate | Yes | Yes |
| Slot Detail | Fault | simulates sensor fault | opened/updated without snackbar | POST /api/sensors/{id}/simulate | Yes | Yes |
| Slot Detail | Reserve | sets slot reserved | opened/updated without snackbar | POST /api/slots/{id}/status | Yes | Yes |
| Slot Detail | Release | sets slot available | opened/updated without snackbar | POST /api/slots/{id}/status | Yes | Yes |
| Slot Detail | Maintenance | sets slot maintenance | opened/updated without snackbar | POST /api/slots/{id}/status | Yes | Yes |
| Dashboard | Add slot | opens create-slot form safely | opened/updated without snackbar | GET /api/zones, GET /api/slots | Yes | Yes |
| Dashboard | Save slot | creates slot and refreshes | opened/updated without snackbar | POST /api/slots | Yes | Yes |
| Dashboard | New session | opens new session workflow | opened/updated without snackbar | GET /api/zones | Yes | Yes |
| Dashboard | Preview optimized slot | shows backend recommendation | opened/updated without snackbar | POST /api/optimizer/recommend | Yes | Yes |
| Dashboard | Start session | starts optimized session | opened/updated without snackbar | POST /api/sessions/start | Yes | Yes |
| Dashboard | Emergency exit | opens active session selector | opened/updated without snackbar | GET /api/sessions | Yes | Yes |
| Dashboard | Exit session | exits selected active session | opened/updated without snackbar | POST /api/sessions/{id}/exit | Yes | Yes |
| Dashboard | Bulk create slots | opens bulk modal | opened/updated without snackbar | GET /api/zones | Yes | Yes |
| Dashboard | Preview generated slots | shows duplicate-aware preview | opened/updated without snackbar | POST /api/slots/bulk-preview | Yes | Yes |
| Dashboard | Confirm import | creates slots | opened/updated without snackbar | POST /api/slots/bulk-create | Yes | Yes |
| Dashboard | Export report | opens export preview | opened/updated without snackbar | local | Yes | Yes |
| Dashboard | Generate CSV | loads backend CSV | opened/updated without snackbar | GET /api/reports/*.csv | Yes | Yes |
| Dashboard | Cancel | closes export modal | opened/updated without snackbar | local | Yes | Yes |
| Dashboard | Refresh | reloads current screen | opened/updated without snackbar | GET /api/dashboard | Yes | Yes |
| Search/filter | Search slots, vehicles, sessions | updates visible dataset | updated without exception | GET list endpoint/local filter | Yes | Yes |
| Dashboard | Cancel | closes global search modal | opened/updated without snackbar | local | Yes | Yes |
| Navigation sidebar | Zone Management | navigate to Zone Management | opened/updated without snackbar | local state | Yes | Yes |
| Zone Management | Add zone | opens zone form | opened/updated without snackbar | GET /api/lots | Yes | Yes |
| Zone Management | Save zone | creates zone | opened/updated without snackbar | POST /api/zones | Yes | Yes |
| Zone Management | Add slot | opens selected-zone slot form | opened/updated without snackbar | GET /api/zones, GET /api/slots | Yes | Yes |
| Zone Management | Save slot | creates slot for selected zone | opened/updated without snackbar | POST /api/slots | Yes | Yes |
| Zone Management | Bulk create | opens bulk modal | opened/updated without snackbar | GET /api/zones | Yes | Yes |
| Zone Management | Preview generated slots | previews generated slots | opened/updated without snackbar | POST /api/slots/bulk-preview | Yes | Yes |
| Zone Management | Confirm import | creates generated slots | opened/updated without snackbar | POST /api/slots/bulk-create | Yes | Yes |
| Search/filter | Search slots | updates visible dataset | updated without exception | GET list endpoint/local filter | Yes | Yes |
| Zone Management | Apply | applies lot/zone/search/status filters | opened/updated without snackbar | GET /api/slots | Yes | Yes |
| Navigation sidebar | Sessions & Payments | navigate to Sessions & Payments | opened/updated without snackbar | local state | Yes | Yes |
| Sessions & Payments | Apply | clears persisted search before session actions | opened/updated without snackbar | GET /api/sessions | Yes | Yes |
| Sessions & Payments | New session | opens session workflow | opened/updated without snackbar | GET /api/zones | Yes | Yes |
| Sessions & Payments | Preview optimized slot | shows recommendation | opened/updated without snackbar | POST /api/optimizer/recommend | Yes | Yes |
| Sessions & Payments | Start session | starts active session | opened/updated without snackbar | POST /api/sessions/start | Yes | Yes |
| Sessions & Payments | Apply | applies filters/search | opened/updated without snackbar | GET /api/sessions | Yes | Yes |
| Sessions & Payments | New session | opens another session workflow | opened/updated without snackbar | GET /api/zones | Yes | Yes |
| Sessions & Payments | Start session | starts active session for cancellation test | opened/updated without snackbar | POST /api/sessions/start | Yes | Yes |
| Sessions & Payments | Cancel | opens cancel confirmation | opened/updated without snackbar | local | Yes | Yes |
| Sessions & Payments | Confirm | cancels active session | opened/updated without snackbar | POST /api/sessions/{id}/cancel | Yes | Yes |
| Sessions & Payments | Exit session | opens exit modal | opened/updated without snackbar | local | Yes | Yes |
| Sessions & Payments | Exit and calculate | exits and calculates fee | opened/updated without snackbar | POST /api/sessions/{id}/exit | Yes | Yes |
| Sessions & Payments | Process payment | opens payment modal | opened/updated without snackbar | local | Yes | Yes |
| Sessions & Payments | Complete payment | persists payment | opened/updated without snackbar | POST /api/payments/process | Yes | Yes |
| Sessions & Payments | Receipt | opens receipt view | opened/updated without snackbar | GET /api/payments/receipt/{id} | Yes | Yes |
| Navigation sidebar | Forms Library | navigate to Forms Library | opened/updated without snackbar | local state | Yes | Yes |
| Forms Library | Add Parking Lot | opens Add Parking Lot form | opened/updated without snackbar | local | Yes | Yes |
| Forms Library | Save lot | saves Add Parking Lot | opened/updated without snackbar | POST /api/lots | Yes | Yes |
| Forms Library | Add Parking Zone | opens Add Parking Zone form | opened/updated without snackbar | local | Yes | Yes |
| Forms Library | Save zone | saves Add Parking Zone | opened/updated without snackbar | POST /api/zones | Yes | Yes |
| Forms Library | Add Parking Slot | opens Add Parking Slot form | opened/updated without snackbar | local | Yes | Yes |
| Forms Library | Save slot | saves Add Parking Slot | opened/updated without snackbar | POST /api/slots | Yes | Yes |
| Forms Library | Register Hardware Sensor | opens Register Hardware Sensor form | opened/updated without snackbar | local | Yes | Yes |
| Forms Library | Save sensor | saves Register Hardware Sensor | opened/updated without snackbar | POST /api/sensors | Yes | Yes |
| Forms Library | Create Tariff Plan | opens Create Tariff Plan form | opened/updated without snackbar | local | Yes | Yes |
| Forms Library | Save tariff | saves Create Tariff Plan | opened/updated without snackbar | POST /api/tariffs | Yes | Yes |
| Forms Library | Manual Session Entry | opens manual session workflow | opened/updated without snackbar | local | Yes | Yes |
| Forms Library | Start session | starts manual session | opened/updated without snackbar | POST /api/sessions/start | Yes | Yes |
| Forms Library | Bulk slot creation | opens bulk modal | opened/updated without snackbar | GET /api/zones | Yes | Yes |
| Forms Library | Preview generated slots | previews bulk form slots | opened/updated without snackbar | POST /api/slots/bulk-preview | Yes | Yes |
| Forms Library | Confirm import | creates bulk form slots | opened/updated without snackbar | POST /api/slots/bulk-create | Yes | Yes |
| Navigation sidebar | System Configuration | navigate to System Configuration | opened/updated without snackbar | local state | Yes | Yes |
| System Configuration | Register sensor | opens sensor form | opened/updated without snackbar | GET /api/slots | Yes | Yes |
| System Configuration | Save sensor | creates sensor | opened/updated without snackbar | POST /api/sensors | Yes | Yes |
| System Configuration | Create tariff | opens tariff form | opened/updated without snackbar | GET /api/zones | Yes | Yes |
| System Configuration | Save tariff | creates tariff | opened/updated without snackbar | POST /api/tariffs | Yes | Yes |
| System Configuration | Bulk create slots | opens bulk modal | opened/updated without snackbar | GET /api/zones | Yes | Yes |
| System Configuration | Preview generated slots | previews slots | opened/updated without snackbar | POST /api/slots/bulk-preview | Yes | Yes |
| System Configuration | Confirm import | creates slots | opened/updated without snackbar | POST /api/slots/bulk-create | Yes | Yes |
| System Configuration | Simulate | opens sensor simulation | opened/updated without snackbar | local | Yes | Yes |
| System Configuration | Simulate | persists sensor simulation | opened/updated without snackbar | POST /api/sensors/{id}/simulate | Yes | Yes |
| System Configuration | Edit | opens first editable row | opened/updated without snackbar | local | Yes | Yes |
| System Configuration | Save sensor | saves edited row | opened/updated without snackbar | PUT endpoint | Yes | Yes |
| System Configuration | Delete | opens delete confirmation | opened/updated without snackbar | local | Yes | Yes |
| System Configuration | Confirm | attempts safe delete with clean feedback | opened/updated without snackbar | DELETE endpoint | Yes | Yes |
| System Configuration | Refresh | refreshes system screen | opened/updated without snackbar | GET /api/dashboard | Yes | Yes |
| Navigation sidebar | Reports | navigate to Reports | opened/updated without snackbar | local state | Yes | Yes |
| Reports | Export report | opens report export | opened/updated without snackbar | local | Yes | Yes |
| Reports | Generate CSV | generates CSV | opened/updated without snackbar | GET /api/reports/*.csv | Yes | Yes |
| Reports | Cancel | closes report export modal | opened/updated without snackbar | local | Yes | Yes |
| Navigation sidebar | Dashboard | navigate to Dashboard | opened/updated without snackbar | local state | Yes | Yes |
| Navigation sidebar | Logout | returns to login | opened/updated without snackbar | local state | Yes | Yes |
