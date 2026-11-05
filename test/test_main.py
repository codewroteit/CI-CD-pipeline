import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    monkeypatch.delenv("DASH_USER", raising=False)
    monkeypatch.delenv("DASH_PASS", raising=False)
    db.Base.metadata.drop_all(db.engine)
    db.init_db()
    db.add_user("admin", "test-only-pass")


def test_home():
    assert client.get("/").status_code == 200


def test_health():
    assert client.get("/health").json() == {"status": "healthy"}


def test_version():
    assert client.get("/version").json() == {"version": "1.0.0"}


def test_dashboard_requires_login():
    assert client.get("/dashboard").status_code == 401
    bad = client.get("/dashboard", auth=("admin", "wrong"))
    assert bad.status_code == 401
    ok = client.get("/dashboard", auth=("admin", "test-only-pass"))
    assert ok.status_code == 200
    assert "Pipeline" in ok.text


def test_password_is_stored_hashed():
    with Session(db.engine) as session:
        user = session.scalar(select(db.User).where(db.User.username == "admin"))
    assert "test-only-pass" not in user.password_hash
    assert "$" in user.password_hash


def test_change_password():
    r = client.post(
        "/change-password",
        json={"new_password": "brand-new-pass"},
        auth=("admin", "test-only-pass"),
    )
    assert r.status_code == 200
    assert client.get("/dashboard", auth=("admin", "test-only-pass")).status_code == 401
    assert client.get("/dashboard", auth=("admin", "brand-new-pass")).status_code == 200


def test_short_password_rejected():
    r = client.post(
        "/change-password",
        json={"new_password": "short"},
        auth=("admin", "test-only-pass"),
    )
    assert r.status_code == 422


def test_create_user_and_duplicate():
    body = {"username": "elle", "password": "elle-pass-123"}
    r = client.post("/users", json=body, auth=("admin", "test-only-pass"))
    assert r.status_code == 201
    assert client.get("/dashboard", auth=("elle", "elle-pass-123")).status_code == 200
    dup = client.post("/users", json=body, auth=("admin", "test-only-pass"))
    assert dup.status_code == 409