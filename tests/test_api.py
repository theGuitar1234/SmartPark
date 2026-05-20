def test_health_endpoint_is_public(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_returns_operational_metrics(client):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert "total_revenue" in body
    assert "slot_map" in body


def test_duplicate_vehicle_plate_is_rejected(client):
    payload = {"plate_number": "10-AA-101", "vehicle_type": "Car", "owner_name": "Duplicate"}
    response = client.post("/api/vehicles", json=payload)
    assert response.status_code == 409


def test_start_exit_pay_session_flow(client):
    start = client.post("/api/sessions/start", json={"plate_number": "10-TEST-42", "vehicle_type": "Car", "owner_name": "Test Driver", "use_optimizer": True, "entry_time": "2026-01-01T10:00:00Z"})
    assert start.status_code == 201, start.text
    session = start.json()
    assert session["status"] == "Active"
    duplicate = client.post("/api/sessions/start", json={"plate_number": "10-TEST-42", "vehicle_type": "Car", "owner_name": "Test Driver", "use_optimizer": True})
    assert duplicate.status_code == 409
    exit_response = client.post(f"/api/sessions/{session['session_id']}/exit", json={"exit_time": "2026-01-01T12:20:00Z"})
    assert exit_response.status_code == 200, exit_response.text
    completed = exit_response.json()
    assert completed["status"] == "Completed"
    assert completed["fee_amount"] > 0
    bad_payment = client.post("/api/payments/process", json={"session_id": session["session_id"], "paid_amount": completed["fee_amount"] + 1, "method": "Card", "status": "Paid"})
    assert bad_payment.status_code == 409
    payment = client.post("/api/payments/process", json={"session_id": session["session_id"], "paid_amount": completed["fee_amount"], "method": "Card", "status": "Paid"})
    assert payment.status_code == 201, payment.text
    assert payment.json()["status"] == "Paid"


def test_bulk_slot_preview_rejects_duplicates(client):
    response = client.post("/api/slots/bulk-preview", json={"zone_id": "zone_a", "prefix": "A", "start_number": 1, "count": 2, "slot_type": "Standard"})
    assert response.status_code == 200
    assert response.json()["duplicates"] == 2


def test_sensor_already_assigned_is_rejected(client):
    response = client.post("/api/sensors", json={"sensor_code": "SNS-NEW", "sensor_type": "Ultrasonic", "slot_id": "slot_a_01", "is_active": True, "battery_level": 95})
    assert response.status_code == 409


def test_slot_detail_returns_sensor_activity_and_session_context(client):
    response = client.get("/api/slots/slot_a_01/detail")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["slot"]["slot_code"] == "A-01"
    assert body["sensor"]["sensor_code"] == "SNS-001"
    assert body["active_session"]["plate_number"] == "10-AA-101"
    assert isinstance(body["activity"], list)


def test_bulk_create_and_sensor_simulation_update_real_data(client):
    preview = client.post("/api/slots/bulk-preview", json={"zone_id": "zone_a", "prefix": "QA", "start_number": 1, "count": 3, "slot_type": "Standard"})
    assert preview.status_code == 200, preview.text
    assert preview.json()["duplicates"] == 0
    created = client.post("/api/slots/bulk-create", json={"zone_id": "zone_a", "prefix": "QA", "start_number": 1, "count": 3, "slot_type": "Standard"})
    assert created.status_code == 200, created.text
    slots = client.get("/api/slots", params={"search": "QA-01"})
    assert slots.status_code == 200
    slot = slots.json()["items"][0]
    sensor = client.post("/api/sensors", json={"sensor_code": "SNS-QA", "sensor_type": "Ultrasonic", "slot_id": slot["slot_id"], "is_active": True, "battery_level": 96})
    assert sensor.status_code == 201, sensor.text
    simulated = client.post(f"/api/sensors/{sensor.json()['sensor_id']}/simulate", json={"reported_status": "Occupied", "raw_payload": "qa simulation"})
    assert simulated.status_code == 200, simulated.text
    updated = client.get(f"/api/slots/{slot['slot_id']}")
    assert updated.json()["status"] == "Occupied"


def test_failed_payment_can_be_retried_successfully(client):
    payment = client.post("/api/payments/process", json={"session_id": "sess_unpaid_demo", "paid_amount": 0, "method": "Wallet", "status": "Failed"})
    assert payment.status_code == 201, payment.text
    retry = client.post("/api/payments/process", json={"session_id": "sess_unpaid_demo", "paid_amount": 15.0, "method": "Card", "status": "Paid"})
    assert retry.status_code == 201, retry.text
    assert retry.json()["status"] == "Paid"
    receipt = client.get("/api/payments/receipt/sess_unpaid_demo")
    assert receipt.status_code == 200
    assert receipt.json()["status"] == "Paid"


def test_slot_update_cannot_change_status_without_status_endpoint(client):
    response = client.put("/api/slots/slot_a_01", json={"status": "Available"})
    assert response.status_code == 409
    assert "status override" in response.json()["detail"] or "active session" in response.json()["detail"]


def test_report_csv_exports_are_real_backend_outputs(client):
    for path in ["/api/reports/summary.csv", "/api/reports/payments.csv", "/api/reports/sessions.csv"]:
        response = client.get(path)
        assert response.status_code == 200, response.text
        assert "text/csv" in response.headers["content-type"]
        assert response.text.strip()
