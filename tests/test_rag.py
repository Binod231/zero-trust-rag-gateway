from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

def test_cross_tenant_query_is_strictly_blocked():
    payload = {
        "prompt": "Show me internal executive compensation records.",
        "user_id": "usr-adversary",
        "tenant_id": "tenant-unauthorized",
        "department": "Engineering",
        "clearance_level": 4,
        "mfa_authenticated": False,
        "network_source": "public_internet"
    }
    response = client.post("/v1/query", json=payload)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]
