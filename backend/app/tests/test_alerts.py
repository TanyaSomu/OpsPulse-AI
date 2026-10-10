import uuid

def test_webhook_alert_ingestion_creates_incident(client, db_session):
    unique_title = f"Disk I/O saturation on worker node {uuid.uuid4().hex[:6]}"
    payload = {
        "service_name": "Analytics Ingestion Stream",
        "title": unique_title,
        "description": "Disk utilization > 95% on mount /data",
        "severity": "CRITICAL",
        "source": "Prometheus Node Exporter",
        "metadata": {"mount": "/data", "iops": 4500}
    }

    res = client.post("/api/v1/alerts/webhook", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    assert data["is_new_incident"] is True
    assert data["deduplicated"] is False
    assert data["incident_id"] is not None
    assert data["incident_number"] >= 1000

    incident_id = data["incident_id"]

    # Ingest DUPLICATE alert with identical signature
    res_dup = client.post("/api/v1/alerts/webhook", json=payload)
    assert res_dup.status_code == 201
    dup_data = res_dup.json()
    assert dup_data["status"] == "success"
    assert dup_data["is_new_incident"] is False
    assert dup_data["deduplicated"] is True
    assert dup_data["incident_id"] == incident_id

def test_webhook_alert_unknown_service_returns_404(client):
    payload = {
        "service_name": "NonExistentService12345",
        "title": "Some alert",
        "severity": "HIGH",
        "source": "Datadog"
    }
    res = client.post("/api/v1/alerts/webhook", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
