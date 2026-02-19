from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_employee_requests_invalid_status_returns_422():
    r = client.get("/api/leave/requests", params={"employeeId": "any", "status": "APPROVAL"})
    assert r.status_code == 422


def test_admin_requests_invalid_status_returns_422():
    r = client.get("/api/admin/leave/requests", params={"status": "APPROVAL"})
    assert r.status_code == 422
