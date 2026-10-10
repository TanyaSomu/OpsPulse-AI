def test_dashboard_summary_metrics_calculated(client, admin_headers):
    res = client.get("/api/v1/dashboard/summary", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "active_incidents" in data
    assert "critical_incidents" in data
    assert "unacknowledged_incidents" in data
    assert "resolved_incidents" in data
    assert "total_services" in data
    assert "degraded_or_failing_services" in data

    assert data["total_services"] >= 5
    assert data["active_incidents"] >= 1

def test_dashboard_bundle_endpoint(client, responder_headers):
    res = client.get("/api/v1/dashboard/data", headers=responder_headers)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "trends" in data
    assert "service_health" in data
    assert "severity_distribution" in data
    assert "recent_incidents" in data
    assert len(data["trends"]) == 7
    assert len(data["severity_distribution"]) == 5
