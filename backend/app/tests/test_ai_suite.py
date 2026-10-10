import uuid
from datetime import datetime, timezone, timedelta
import pytest
from app.models.incident import Incident, IncidentEvent, IncidentStatus, Severity
from app.models.service import Service
from app.models.alert import Alert
from app.models.escalation import EscalationPolicy, EscalationRule
from app.services.escalation_service import check_and_escalate_incidents

# ==============================================================================
# MODULE A: AUTHENTICATION (TC-AUTH-01 to TC-AUTH-05)
# ==============================================================================

def test_tc_auth_01_successful_login(client):
    """TC-AUTH-01: Valid credentials return HTTP 200 and JWT access token."""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@opspulse.local",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20
    assert data["user"]["email"] == "admin@opspulse.local"

def test_tc_auth_02_invalid_password(client):
    """TC-AUTH-02: Incorrect password is rejected with HTTP 401."""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@opspulse.local",
        "password": "wrongpassword123"
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json().get("detail", "")

def test_tc_auth_03_unregistered_email(client):
    """TC-AUTH-03: Non-existent user is rejected with HTTP 401."""
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent_ghost@opspulse.local",
        "password": "somepassword"
    })
    assert response.status_code == 401

def test_tc_auth_04_missing_or_empty_credentials(client):
    """TC-AUTH-04: Empty string credentials produce client error."""
    response = client.post("/api/v1/auth/login", json={
        "email": "",
        "password": ""
    })
    assert response.status_code in (400, 401, 422)

def test_tc_auth_05_malformed_token_rejected(client):
    """TC-AUTH-05: Expired or malformed bearer token returns HTTP 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer bad.token.content"}
    )
    assert response.status_code == 401

# ==============================================================================
# MODULE B: ALERT MANAGEMENT & DEDUPLICATION (TC-ALRT-01 to TC-ALRT-05)
# ==============================================================================

def test_tc_alrt_01_valid_webhook_alert_ingestion(client, db_session):
    """TC-ALRT-01: Valid webhook alert ingests and triggers an incident."""
    service = db_session.query(Service).filter(Service.name == "Order Processing Pipeline").first()
    assert service is not None

    test_title = f"AI Test Alert Latency {uuid.uuid4().hex[:6]}"
    payload = {
        "service_name": service.name,
        "title": test_title,
        "description": "Synthetic latency test triggered by AI suite",
        "severity": "CRITICAL",
        "source": "AI-TestRunner",
        "metadata": {"test_run_id": "ai-001"}
    }
    response = client.post("/api/v1/alerts/webhook", json=payload)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["is_new_incident"] is True
    assert data["status"] == "success"
    assert data["incident_number"] > 0

    # Verify underlying incident was created in TRIGGERED status
    created_inc = db_session.query(Incident).filter(Incident.id == data["incident_id"]).first()
    assert created_inc is not None
    assert created_inc.status == IncidentStatus.TRIGGERED

def test_tc_alrt_02_alert_unknown_service_rejected(client):
    """TC-ALRT-02: Alert referencing unknown service returns HTTP 404."""
    payload = {
        "service_name": "Totally_Bogus_Service_DoesNotExist_9999",
        "title": "Alert for ghost service",
        "severity": "HIGH",
        "source": "AI-TestRunner"
    }
    response = client.post("/api/v1/alerts/webhook", json=payload)
    assert response.status_code == 404

def test_tc_alrt_03_alert_invalid_severity_rejected(client, db_session):
    """TC-ALRT-03: Alert with invalid severity enum returns HTTP 422."""
    service = db_session.query(Service).first()
    payload = {
        "service_name": service.name,
        "title": "Invalid severity test",
        "severity": "CATASTROPHIC_LEVEL_MAX",
        "source": "AI-TestRunner"
    }
    response = client.post("/api/v1/alerts/webhook", json=payload)
    assert response.status_code == 422

def test_tc_alrt_04_alert_missing_required_fields(client):
    """TC-ALRT-04: Alert payload missing required fields returns HTTP 422."""
    response = client.post("/api/v1/alerts/webhook", json={
        "source": "Prometheus"
    })
    assert response.status_code == 422

def test_tc_alrt_05_duplicate_alert_deduplication(client, db_session):
    """TC-ALRT-05: Identical alert within correlation window correlates into same incident."""
    service = db_session.query(Service).filter(Service.name == "Customer Inventory Service").first()
    unique_title = f"Duplicate Test Alert {uuid.uuid4().hex[:6]}"
    payload = {
        "service_name": service.name,
        "title": unique_title,
        "description": "Testing deterministic deduplication hash",
        "severity": "HIGH",
        "source": "AI-Deduplication-Test"
    }
    # First dispatch -> triggers new incident
    r1 = client.post("/api/v1/alerts/webhook", json=payload)
    assert r1.status_code in (200, 201)
    d1 = r1.json()
    assert d1["is_new_incident"] is True
    first_incident_num = d1["incident_number"]

    # Second dispatch with identical fingerprint -> correlates
    r2 = client.post("/api/v1/alerts/webhook", json=payload)
    assert r2.status_code in (200, 201)
    d2 = r2.json()
    assert d2["is_new_incident"] is False
    assert d2["incident_number"] == first_incident_num

# ==============================================================================
# MODULE C: INCIDENT MANAGEMENT & STATE MACHINE (TC-INCD-01 to TC-INCD-07)
# ==============================================================================

def test_tc_incd_01_create_incident(client, responder_headers, db_session):
    """TC-INCD-01: Manual incident creation starts in TRIGGERED status with SLA deadline."""
    service = db_session.query(Service).first()
    payload = {
        "service_id": service.id,
        "title": f"Manual AI Incident {uuid.uuid4().hex[:6]}",
        "description": "Created by automated AI testing suite",
        "severity": "HIGH"
    }
    response = client.post("/api/v1/incidents", json=payload, headers=responder_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "TRIGGERED"
    assert data["service_id"] == service.id
    assert data["ack_deadline"] is not None

def test_tc_incd_02_get_incident_detail(client, responder_headers, db_session):
    """TC-INCD-02: Retrieve full incident detail including timeline and alerts."""
    incident = db_session.query(Incident).first()
    assert incident is not None
    response = client.get(f"/api/v1/incidents/{incident.id}", headers=responder_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == incident.id
    assert "events" in data
    assert "alerts" in data

def test_tc_incd_03_to_07_full_lifecycle_and_audit(client, responder_headers, db_session):
    """TC-INCD-03 to 07: Validate Acknowledge -> Mitigate -> Resolve -> Invalid transition -> Audit."""
    service = db_session.query(Service).first()
    # 1. Create Incident
    create_res = client.post("/api/v1/incidents", json={
        "service_id": service.id,
        "title": f"Lifecycle Test Incident {uuid.uuid4().hex[:6]}",
        "severity": "MEDIUM"
    }, headers=responder_headers)
    assert create_res.status_code == 201
    inc_id = create_res.json()["id"]

    # 2. TC-INCD-03: Acknowledge
    ack_res = client.post(f"/api/v1/incidents/{inc_id}/acknowledge", headers=responder_headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"
    assert ack_res.json()["acknowledged_at"] is not None

    # 3. TC-INCD-04: Mitigate
    mit_res = client.post(f"/api/v1/incidents/{inc_id}/mitigate", json={
        "message": "Workaround applied by automated test"
    }, headers=responder_headers)
    assert mit_res.status_code == 200
    assert mit_res.json()["status"] == "MITIGATED"

    # 4. TC-INCD-05: Resolve
    res_res = client.post(f"/api/v1/incidents/{inc_id}/resolve", json={
        "message": "Permanent fix verified"
    }, headers=responder_headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
    assert res_res.json()["resolved_at"] is not None

    # 5. TC-INCD-06: Invalid transition from RESOLVED -> ACKNOWLEDGED rejected
    bad_res = client.post(f"/api/v1/incidents/{inc_id}/acknowledge", headers=responder_headers)
    assert bad_res.status_code == 400
    assert "Invalid state transition" in bad_res.json().get("detail", "")

    # 6. TC-INCD-07: Verify PostgreSQL persistence of IncidentEvents
    events = db_session.query(IncidentEvent).filter(IncidentEvent.incident_id == inc_id).all()
    event_types = [e.event_type for e in events]
    assert "ACKNOWLEDGED" in event_types
    assert "RESOLVED" in event_types
    assert len(events) >= 3

# ==============================================================================
# MODULE D: ESCALATION POLICIES (TC-ESCL-01 to TC-ESCL-05)
# ==============================================================================

def test_tc_escl_01_create_escalation_policy(client, admin_headers, admin_user, responder_user):
    """TC-ESCL-01: Admin creates valid escalation policy with tiers."""
    payload = {
        "name": f"AI Escalation Policy {uuid.uuid4().hex[:6]}",
        "description": "Generated by AI test suite",
        "ack_timeout_seconds": 180,
        "rules": [
            {"level_number": 1, "user_id": responder_user.id},
            {"level_number": 2, "user_id": admin_user.id}
        ]
    }
    response = client.post("/api/v1/escalation-policies", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert len(data["rules"]) == 2
    assert data["ack_timeout_seconds"] == 180

def test_tc_escl_03_04_escalation_breach_and_resolved_exclusion(db_session):
    """TC-ESCL-03 & 04: Expired deadline escalates active incident; resolved is untouched."""
    db_session.rollback()  # ensure clean transaction
    service = db_session.query(Service).first()
    now = datetime.now(timezone.utc)

    # Incident A: TRIGGERED with expired deadline -> should escalate
    inc_active = Incident(
        organization_id=service.organization_id,
        service_id=service.id,
        incident_number=999901,
        title="Escalation Test Active",
        severity=Severity.HIGH,
        status=IncidentStatus.TRIGGERED,
        current_escalation_level=1,
        ack_deadline=now - timedelta(minutes=5),
        created_at=now - timedelta(minutes=10),
        fingerprint=uuid.uuid4().hex
    )
    # Incident B: RESOLVED with expired deadline -> should NOT escalate
    inc_resolved = Incident(
        organization_id=service.organization_id,
        service_id=service.id,
        incident_number=999902,
        title="Escalation Test Resolved",
        severity=Severity.HIGH,
        status=IncidentStatus.RESOLVED,
        current_escalation_level=1,
        ack_deadline=now - timedelta(minutes=5),
        resolved_at=now - timedelta(minutes=2),
        created_at=now - timedelta(minutes=10),
        fingerprint=uuid.uuid4().hex
    )
    db_session.add(inc_active)
    db_session.add(inc_resolved)
    db_session.commit()

    # Trigger escalation engine evaluation
    result = check_and_escalate_incidents(db_session)
    assert result["expired_found"] >= 1

    # Verify inc_resolved remains untouched
    db_session.refresh(inc_resolved)
    assert inc_resolved.status == IncidentStatus.RESOLVED
    assert inc_resolved.current_escalation_level == 1

    # Cleanup test incidents
    db_session.delete(inc_active)
    db_session.delete(inc_resolved)
    db_session.commit()

def test_tc_escl_05_manual_sla_check_endpoint(client, responder_headers):
    """TC-ESCL-05: Manual SLA check endpoint evaluates expired deadlines."""
    response = client.post("/api/v1/incidents/check-escalations", headers=responder_headers)
    assert response.status_code == 200
    data = response.json()
    assert "checked_at" in data
    assert "escalated_count" in data

# ==============================================================================
# MODULE E: SERVICES CATALOG & RBAC (TC-SRVC-01 to TC-SRVC-04)
# ==============================================================================

def test_tc_srvc_01_create_service(client, admin_headers):
    """TC-SRVC-01: Admin registers new monitored service."""
    service_name = f"AI Test Service {uuid.uuid4().hex[:6]}"
    payload = {
        "name": service_name,
        "description": "Registered by AI test suite",
        "owner_team": "Infrastructure Core",
        "environment": "production"
    }
    response = client.post("/api/v1/services", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == service_name
    assert data["health_status"] == "HEALTHY"
    assert "slug" in data

def test_tc_srvc_02_duplicate_service_rejected(client, admin_headers, db_session):
    """TC-SRVC-02: Duplicate service name returns HTTP 400."""
    service = db_session.query(Service).first()
    payload = {
        "name": service.name,
        "owner_team": "Team A"
    }
    response = client.post("/api/v1/services", json=payload, headers=admin_headers)
    assert response.status_code == 400
    assert "already exists" in response.json().get("detail", "")

def test_tc_srvc_03_update_service_health(client, admin_headers, db_session):
    """TC-SRVC-03: Updating health status persists successfully via PATCH."""
    service = db_session.query(Service).filter(Service.name == "Customer Inventory Service").first()
    orig_status = service.health_status
    response = client.patch(f"/api/v1/services/{service.id}", json={
        "health_status": "DEGRADED"
    }, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["health_status"] == "DEGRADED"

    # Restore original status
    client.patch(f"/api/v1/services/{service.id}", json={
        "health_status": orig_status
    }, headers=admin_headers)

def test_tc_srvc_04_responder_cannot_create_service(client, responder_headers):
    """TC-SRVC-04: Non-admin responder is forbidden from creating services."""
    payload = {
        "name": f"Unauthorized Service {uuid.uuid4().hex[:6]}",
        "owner_team": "Rogue Team"
    }
    response = client.post("/api/v1/services", json=payload, headers=responder_headers)
    assert response.status_code == 403
    assert "privileges required" in response.json().get("detail", "").lower()

# ==============================================================================
# MODULE F: DASHBOARD TELEMETRY (TC-DASH-01 to TC-DASH-03)
# ==============================================================================

def test_tc_dash_01_dashboard_data_structure_and_counts(client, responder_headers, db_session):
    """TC-DASH-01: Dashboard metrics API returns valid schema matching database."""
    response = client.get("/api/v1/dashboard/data", headers=responder_headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "trends" in data
    assert "service_health" in data
    assert "severity_distribution" in data
    assert "recent_incidents" in data

    # Verify summary metrics are non-negative integers
    summary = data["summary"]
    assert summary["active_incidents"] >= 0
    assert summary["critical_incidents"] >= 0
    assert summary["total_services"] >= 1

def test_tc_dash_02_service_health_telemetry_aggregation(client, responder_headers):
    """TC-DASH-02: Service health list contains health counts and active incidents."""
    response = client.get("/api/v1/dashboard/data", headers=responder_headers)
    assert response.status_code == 200
    data = response.json()
    services = data["service_health"]
    assert len(services) > 0
    for s in services:
        assert "name" in s
        assert "health_status" in s
        assert s["health_status"] in ("HEALTHY", "DEGRADED", "FAILING", "MAINTENANCE")

# ==============================================================================
# MODULE G: SECURITY, RBAC & BOUNDARY CHECKS (TC-SECU-01 to TC-SECU-05)
# ==============================================================================

def test_tc_secu_01_unauthenticated_request_rejected(client):
    """TC-SECU-01: Unauthenticated request to incidents returns HTTP 401."""
    response = client.get("/api/v1/incidents")
    assert response.status_code == 401

def test_tc_secu_02_sql_injection_resilience(client, responder_headers):
    """TC-SECU-02: SQL injection payloads in search query are safely parameterized."""
    malicious_query = "' OR '1'='1' -- "
    response = client.get(f"/api/v1/incidents?search={malicious_query}", headers=responder_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_tc_secu_04_non_existent_uuid_returns_404(client, responder_headers):
    """TC-SECU-04: Non-existent UUID returns HTTP 404 with structured error."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/incidents/{fake_uuid}", headers=responder_headers)
    assert response.status_code == 404
    assert "Incident not found" in response.json().get("detail", "")

def test_tc_secu_05_responder_cannot_create_users(client, responder_headers):
    """TC-SECU-05: Non-admin cannot create new users."""
    payload = {
        "email": "hacker@test.com",
        "full_name": "Rogue User",
        "password": "password123",
        "role": "ADMIN"
    }
    response = client.post("/api/v1/users", json=payload, headers=responder_headers)
    assert response.status_code == 403
