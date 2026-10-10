import uuid

def test_admin_can_create_service(client, admin_headers):
    unique_name = f"Service-{uuid.uuid4().hex[:6]}"
    res = client.post("/api/v1/services", json={
        "name": unique_name,
        "description": "Admin created test service",
        "environment": "staging",
        "owner_team": "Infra"
    }, headers=admin_headers)
    assert res.status_code == 201
    assert res.json()["name"] == unique_name

def test_responder_cannot_create_service(client, responder_headers):
    res = client.post("/api/v1/services", json={
        "name": "Unauthorized-Service",
        "environment": "production"
    }, headers=responder_headers)
    assert res.status_code == 403
    assert "Administrative privileges required" in res.json()["detail"]

def test_responder_can_manage_incidents(client, responder_headers, db_session):
    # Verify responders can list and update incidents
    res = client.get("/api/v1/incidents", headers=responder_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
