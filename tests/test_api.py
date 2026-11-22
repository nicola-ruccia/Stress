import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.v1.endpoints.auth import _password_hash
from app.db.session import Base, get_db
from app.models.entities import Account

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

def test_password_login_for_all_roles():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    test_sessions = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    test_password = "JudgeLoginTest2026!"
    with test_sessions() as db:
        for role in ("hr", "medico", "lavoratore"):
            db.add(Account(
                email=f"{role}@example.test",
                role=role,
                company="azienda-test",
                employee_code="abc1234567" if role == "lavoratore" else None,
                password_hash=_password_hash(test_password),
            ))
        db.commit()

    def override_get_db():
        with test_sessions() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        for role in ("hr", "medico", "lavoratore"):
            response = client.post("/api/v1/auth/login", json={
                "email": f"{role}@example.test",
                "password": test_password,
            })
            assert response.status_code == 200
            assert response.json()["role"] == role
            assert response.json()["access_token"]

        invalid = client.post("/api/v1/auth/login", json={
            "email": "hr@example.test",
            "password": "wrong-password",
        })
        assert invalid.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()
