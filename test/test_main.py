def test_dashboard_requires_login(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("DASH_USER", "admin")
    monkeypatch.setenv("DASH_PASS", "test-only-pass")
    client = TestClient(app)
    assert client.get("/dashboard").status_code == 401
    assert client.get("/dashboard", auth=("admin", "wrong")).status_code == 401
    r = client.get("/dashboard", auth=("admin", "test-only-pass"))
    assert r.status_code == 200
    assert "Pipeline" in r.text

from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "DevOps Status App is running"}
def test_health():
    response = client.get("/health")
    assert response.status_code ==200
    assert response.json() == {"status": "healthy"}
def test_version():
    response = client.get("/version")
    assert response.status_code ==200
    assert response.json() == {"version": "1.0.0"}    