import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set mock AWS credentials and config for CI test execution
os.environ.setdefault("AWS_ACCESS_KEY_ID", "mock-test-key-id")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "mock-test-secret-key")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("POLICY_STORE_ID", "mock-policy-store")
os.environ.setdefault("OPENSEARCH_ENDPOINT", "https://mock-vector.us-east-1.aoss.amazonaws.com")

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
