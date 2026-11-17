"""Integration tests for Job persistence and status retrieval."""

import uuid
from fastapi.testclient import TestClient
from app.db.models import JobOperation, JobRecord, JobRepository, JobStatus
from app.main import app

client = TestClient(app)


def test_job_retrieval_and_listing():
    """Verify jobs can be retrieved and listed via API."""
    job_id = f"test-job-{uuid.uuid4()}"
    # Create test job record
    record = JobRecord(
        id=job_id,
        status=JobStatus.COMPLETED,
        operation=JobOperation.ENCODE_TEXT,
        carrier_type="IMAGE",
        payload_type="TEXT",
        carrier_size=5000,
        payload_size=100,
        progress=100,
        output_filename="output.png",
        output_file_id=job_id,
    )
    JobRepository.create(record)

    # 1. Get job by ID
    resp = client.get(f"/api/v1/jobs/{record.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == record.id
    assert data["status"] == "COMPLETED"
    assert data["operation"] == "ENCODE_TEXT"
    assert data["progress"] == 100
    assert data["download_url"] == f"/api/v1/download/{record.id}/output.png"

    # 2. List jobs
    list_resp = client.get("/api/v1/jobs")
    assert list_resp.status_code == 200
    jobs = list_resp.json()
    assert isinstance(jobs, list)
    assert any(j["id"] == record.id for j in jobs)


def test_job_not_found_returns_404():
    """Requesting non-existent job ID must return 404 JOB_NOT_FOUND."""
    resp = client.get("/api/v1/jobs/non-existent-job-id-999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "JOB_NOT_FOUND"
