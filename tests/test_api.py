import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "k_min" in data

def test_config_soglie_endpoint():
    res = client.get("/api/v1/config/soglie")
    assert res.status_code == 200
    data = res.json()
    assert "indicatori" in data
    assert "fasce" in data
    assert "azioni_suggerite" in data

def test_demo_login_endpoint():
    # Login HR
    res = client.post("/api/v1/auth/demo-login", json={"ruolo": "hr"})
    assert res.status_code == 200
    assert res.json()["ruolo"] == "hr"

    # Login Lavoratore senza codice -> 400
    res_bad = client.post("/api/v1/auth/demo-login", json={"ruolo": "lavoratore"})
    assert res_bad.status_code == 400

    # Login Lavoratore con codice -> 200
    res_ok = client.post("/api/v1/auth/demo-login", json={"ruolo": "lavoratore", "codice": "abc1234567"})
    assert res_ok.status_code == 200
    assert res_ok.json()["codice"] == "abc1234567"
