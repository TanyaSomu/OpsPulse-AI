def test_health_and_readiness(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"
    assert res.json()["database"] == "connected"

def test_login_successful(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@opspulse.local",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@opspulse.local"
    assert data["user"]["role"] == "ADMIN"

def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@opspulse.local",
        "password": "wrong_password"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

def test_get_me(client, admin_headers):
    res = client.get("/api/v1/auth/me", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@opspulse.local"
    assert data["role"] == "ADMIN"

def test_get_me_unauthorized(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
