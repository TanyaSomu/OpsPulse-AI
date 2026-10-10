import uuid
from app.models.service import Service

def test_incident_lifecycle_valid_state_transitions(client, responder_headers, db_session):
    service = db_session.query(Service).filter(Service.name == "Customer Inventory Service").first()

    # 1. Create Incident (TRIGGERED)
    create_payload = {
        "service_id": service.id,
        "title": f"Cache sync failure {uuid.uuid4().hex[:6]}",
        "description": "Inventory sync job timed out.",
        "severity": "HIGH"
    }
    create_res = client.post("/api/v1/incidents", json=create_payload, headers=responder_headers)
    assert create_res.status_code == 201
    inc_data = create_res.json()
    incident_id = inc_data["id"]
    assert inc_data["status"] == "TRIGGERED"

    # 2. Acknowledge Incident (TRIGGERED -> ACKNOWLEDGED)
    ack_res = client.post(f"/api/v1/incidents/{incident_id}/acknowledge", headers=responder_headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"
    assert ack_res.json()["acknowledged_at"] is not None

    # 3. Mitigate Incident (ACKNOWLEDGED -> MITIGATED)
    mit_res = client.post(
        f"/api/v1/incidents/{incident_id}/mitigate",
        json={"message": "Flushed stale Redis key and triggered manual sync."},
        headers=responder_headers
    )
    assert mit_res.status_code == 200
    assert mit_res.json()["status"] == "MITIGATED"
    assert mit_res.json()["mitigated_at"] is not None

    # 4. Resolve Incident (MITIGATED -> RESOLVED)
    res_res = client.post(
        f"/api/v1/incidents/{incident_id}/resolve",
        json={"message": "Inventory cache verified clean."},
        headers=responder_headers
    )
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
    assert res_res.json()["resolved_at"] is not None

    # 5. Reopen Incident (RESOLVED -> TRIGGERED)
    reopen_res = client.post(
        f"/api/v1/incidents/{incident_id}/reopen",
        json={"message": "Discrepancy observed again in store SKU."},
        headers=responder_headers
    )
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "TRIGGERED"

def test_incident_invalid_state_transitions_rejected(client, responder_headers, db_session):
    service = db_session.query(Service).filter(Service.name == "Customer Inventory Service").first()

    # Create incident in TRIGGERED
    create_payload = {
        "service_id": service.id,
        "title": f"Transient error {uuid.uuid4().hex[:6]}",
        "severity": "LOW"
    }
    create_res = client.post("/api/v1/incidents", json=create_payload, headers=responder_headers)
    incident_id = create_res.json()["id"]

    # Directly resolve it (TRIGGERED -> RESOLVED is allowed for quick resolve)
    res_res = client.post(f"/api/v1/incidents/{incident_id}/resolve", headers=responder_headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"

    # From RESOLVED, attempting to ACKNOWLEDGE or MITIGATE directly must be rejected!
    ack_res = client.post(f"/api/v1/incidents/{incident_id}/acknowledge", headers=responder_headers)
    assert ack_res.status_code == 400
    assert "Invalid state transition" in ack_res.json()["detail"]

    mit_res = client.post(f"/api/v1/incidents/{incident_id}/mitigate", headers=responder_headers)
    assert mit_res.status_code == 400
    assert "Invalid state transition" in mit_res.json()["detail"]
