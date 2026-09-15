import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine

# Create tables in test DB if needed (using SQLite memory or default)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "max_file_size_mb" in data

def test_job_not_found():
    response = client.get("/api/jobs/not-a-uuid")
    # Our API might return 400 for bad UUID or 404 for not found
    assert response.status_code in (404, 400)
