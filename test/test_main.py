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