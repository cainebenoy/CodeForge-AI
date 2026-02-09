"""
Tests for job queue service
"""
import pytest
from app.services.job_queue import job_store, JobStatusType
from datetime import datetime


def test_create_job():
    """Test creating a job"""
    job = job_store.create_job(
        job_id="test-job-1",
        project_id="test-project-1",
        agent_type="research",
        input_context={"user_idea": "Test idea"}
    )
    
    assert job.job_id == "test-job-1"
    assert job.project_id == "test-project-1"
    assert job.status == JobStatusType.QUEUED


def test_get_job():
    """Test retrieving a job"""
    job_store.create_job(
        job_id="test-job-2",
        project_id="test-project-2",
        agent_type="wireframe",
        input_context={}
    )
    
    job = job_store.get_job("test-job-2")
    assert job is not None
    assert job.agent_type == "wireframe"


def test_update_job_status():
    """Test updating job status"""
    job_store.create_job(
        job_id="test-job-3",
        project_id="test-project-3",
        agent_type="code",
        input_context={}
    )
    
    updated_job = job_store.update_job(
        "test-job-3",
        status=JobStatusType.RUNNING,
        progress=50
    )
    
    assert updated_job.status == JobStatusType.RUNNING
    assert updated_job.progress == 50


def test_update_job_with_result():
    """Test updating job with result"""
    job_store.create_job(
        job_id="test-job-4",
        project_id="test-project-4",
        agent_type="qa",
        input_context={}
    )
    
    result = {"issues": []}
    updated_job = job_store.update_job(
        "test-job-4",
        status=JobStatusType.COMPLETED,
        result=result
    )
    
    assert updated_job.result == result
    assert updated_job.completed_at is not None


def test_get_project_jobs():
    """Test getting all jobs for a project"""
    project_id = "test-project-5"
    
    for i in range(3):
        job_store.create_job(
            job_id=f"test-job-{i}",
            project_id=project_id,
            agent_type="research",
            input_context={}
        )
    
    jobs = job_store.get_project_jobs(project_id)
    assert len(jobs) == 3


def test_get_pending_jobs():
    """Test getting all pending jobs"""
    job_store.create_job(
        job_id="test-job-pending",
        project_id="test-project-6",
        agent_type="research",
        input_context={}
    )
    
    pending = job_store.get_pending_jobs()
    assert len(pending) > 0
    assert any(j.job_id == "test-job-pending" for j in pending)


def test_job_to_dict():
    """Test job serialization"""
    job = job_store.create_job(
        job_id="test-job-serialize",
        project_id="test-project-7",
        agent_type="pedagogy",
        input_context={}
    )
    
    job_dict = job.to_dict()
    assert job_dict["job_id"] == "test-job-serialize"
    assert job_dict["status"] == "queued"
    assert isinstance(job_dict["created_at"], str)
