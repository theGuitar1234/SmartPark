from __future__ import annotations


def test_dashboard_quick_actions_and_core_visible_workflows(client):
    dashboard = client.get('/api/dashboard')
    assert dashboard.status_code == 200
    assert dashboard.json()['slot_map']

    lot = client.post('/api/lots', json={'name': 'QA Lot', 'address': 'QA Address', 'description': 'Workflow test lot'})
    assert lot.status_code == 201, lot.text
    lot_id = lot.json()['lot_id']
    lot_update = client.put(f'/api/lots/{lot_id}', json={'description': 'Updated QA lot'})
    assert lot_update.status_code == 200, lot_update.text

    zone = client.post('/api/zones', json={'lot_id': lot_id, 'name': 'QA Zone', 'floor_level': 1, 'zone_type': 'Standard', 'priority_score': 12})
    assert zone.status_code == 201, zone.text
    zone_id = zone.json()['zone_id']
    zone_update = client.put(f'/api/zones/{zone_id}', json={'priority_score': 14})
    assert zone_update.status_code == 200, zone_update.text

    empty_zone = client.post('/api/zones', json={'lot_id': lot_id, 'name': 'QA Empty', 'floor_level': 2, 'zone_type': 'Standard', 'priority_score': 50})
    assert empty_zone.status_code == 201, empty_zone.text
    delete_empty_zone = client.delete(f"/api/zones/{empty_zone.json()['zone_id']}")
    assert delete_empty_zone.status_code == 200, delete_empty_zone.text

    slot = client.post('/api/slots', json={'zone_id': zone_id, 'slot_code': 'QA-ACTION-01', 'slot_type': 'Standard', 'status': 'Available', 'distance_score': 30, 'priority_score': 10, 'override_reason': 'qa create'})
    assert slot.status_code == 201, slot.text
    slot_id = slot.json()['slot_id']
    slot_update = client.put(f'/api/slots/{slot_id}', json={'slot_type': 'EV', 'distance_score': 25, 'priority_score': 8})
    assert slot_update.status_code == 200, slot_update.text
    reserve = client.post(f'/api/slots/{slot_id}/status', json={'status': 'Reserved', 'reason': 'qa reserve'})
    assert reserve.status_code == 200, reserve.text
    release = client.post(f'/api/slots/{slot_id}/status', json={'status': 'Available', 'reason': 'qa release'})
    assert release.status_code == 200, release.text
    detail = client.get(f'/api/slots/{slot_id}/detail')
    assert detail.status_code == 200, detail.text

    preview = client.post('/api/slots/bulk-preview', json={'zone_id': zone_id, 'prefix': 'QABULK', 'start_number': 1, 'count': 2, 'slot_type': 'Standard'})
    assert preview.status_code == 200, preview.text
    assert preview.json()['duplicates'] == 0
    bulk = client.post('/api/slots/bulk-create', json={'zone_id': zone_id, 'prefix': 'QABULK', 'start_number': 1, 'count': 2, 'slot_type': 'Standard'})
    assert bulk.status_code == 200, bulk.text
    duplicate_preview = client.post('/api/slots/bulk-preview', json={'zone_id': zone_id, 'prefix': 'QABULK', 'start_number': 1, 'count': 2, 'slot_type': 'Standard'})
    assert duplicate_preview.status_code == 200
    assert duplicate_preview.json()['duplicates'] == 2

    sensor = client.post('/api/sensors', json={'sensor_code': 'SNS-ACTION-01', 'sensor_type': 'Ultrasonic', 'slot_id': slot_id, 'is_active': True, 'battery_level': 91})
    assert sensor.status_code == 201, sensor.text
    sensor_id = sensor.json()['sensor_id']
    sensor_edit = client.put(f'/api/sensors/{sensor_id}', json={'sensor_code': 'SNS-ACTION-01', 'sensor_type': 'Ultrasonic', 'slot_id': slot_id, 'is_active': True, 'battery_level': 89})
    assert sensor_edit.status_code == 200, sensor_edit.text
    for reported in ['Occupied', 'Clear', 'Fault']:
        simulated = client.post(f'/api/sensors/{sensor_id}/simulate', json={'reported_status': reported, 'raw_payload': 'visible action qa'})
        assert simulated.status_code == 200, simulated.text

    tariff = client.post('/api/tariffs', json={'name': 'QA Tariff', 'hourly_rate': 4.0, 'grace_minutes': 5, 'daily_max': 30.0, 'vehicle_type': None, 'zone_id': zone_id, 'is_active': True})
    assert tariff.status_code == 201, tariff.text
    tariff_id = tariff.json()['tariff_id']
    tariff_edit = client.put(f'/api/tariffs/{tariff_id}', json={'hourly_rate': 4.5, 'is_active': True})
    assert tariff_edit.status_code == 200, tariff_edit.text

    recommendation = client.post('/api/optimizer/recommend', json={'vehicle_type': 'Car', 'zone_id': zone_id})
    assert recommendation.status_code == 200, recommendation.text

    active = client.post('/api/sessions/start', json={'plate_number': 'QA-ACTION-PLATE-01', 'vehicle_type': 'Car', 'owner_name': 'QA Driver', 'zone_id': zone_id, 'use_optimizer': True, 'entry_time': '2026-01-01T09:00:00Z'})
    assert active.status_code == 201, active.text
    session_id = active.json()['session_id']
    exit_response = client.post(f'/api/sessions/{session_id}/exit', json={'exit_time': '2026-01-01T11:10:00Z'})
    assert exit_response.status_code == 200, exit_response.text
    completed = exit_response.json()
    payment = client.post('/api/payments/process', json={'session_id': session_id, 'paid_amount': completed['fee_amount'], 'method': 'Card', 'status': 'Paid'})
    assert payment.status_code == 201, payment.text
    receipt = client.get(f'/api/payments/receipt/{session_id}')
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()['status'] == 'Paid'

    cancellable = client.post('/api/sessions/start', json={'plate_number': 'QA-CANCEL-PLATE-01', 'vehicle_type': 'Car', 'owner_name': 'QA Cancel', 'zone_id': zone_id, 'use_optimizer': True})
    assert cancellable.status_code == 201, cancellable.text
    cancel = client.post(f"/api/sessions/{cancellable.json()['session_id']}/cancel", json={})
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()['status'] == 'Cancelled'

    for path in ['/api/reports/summary', '/api/reports/summary.csv', '/api/reports/payments.csv', '/api/reports/sessions.csv']:
        response = client.get(path)
        assert response.status_code == 200, response.text

    sensor_unassign = client.put(f'/api/sensors/{sensor_id}', json={'sensor_code': 'SNS-ACTION-01', 'sensor_type': 'Ultrasonic', 'slot_id': None, 'is_active': True, 'battery_level': 89})
    assert sensor_unassign.status_code == 200, sensor_unassign.text
    delete_sensor = client.delete(f'/api/sensors/{sensor_id}')
    assert delete_sensor.status_code == 200, delete_sensor.text
    protected_delete = client.delete(f'/api/tariffs/{tariff_id}')
    assert protected_delete.status_code == 409, protected_delete.text
    orphan_tariff = client.post('/api/tariffs', json={'name': 'QA Delete Tariff', 'hourly_rate': 9.0, 'grace_minutes': 0, 'daily_max': 60.0, 'vehicle_type': 'Truck', 'zone_id': None, 'is_active': False})
    assert orphan_tariff.status_code == 201, orphan_tariff.text
    delete_tariff = client.delete(f"/api/tariffs/{orphan_tariff.json()['tariff_id']}")
    assert delete_tariff.status_code == 200, delete_tariff.text
