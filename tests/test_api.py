import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture
def api_key():
    return "your-secret-key"

def test_submit_and_get_task(api_key):
    response = client.post("/tasks", json={"input": "test"}, headers={"x-api-key": api_key})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    task_id = data["id"]
    response = client.get(f"/tasks/{task_id}", headers={"x-api-key": api_key})
    assert response.status_code == 200
    assert response.json()["result"].startswith("Processed:")