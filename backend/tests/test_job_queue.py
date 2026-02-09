"""
Tests for job queue service — InMemoryJobStore and Job serialization
"""

from datetime import datetime, timedelta

import pytest

from app.services.job_queue import InMemoryJobStore, Job, JobStatusType

# ─────────────────────────────────────────────────────────────
# InMemoryJobStore tests
# ─────────────────────────────────────────────────────────────


class TestInMemoryJobStore:
    """Tests for InMemoryJobStore (used via the fresh_job_store autouse fixture)."""

    def test_create_job(self, fresh_job_store):
        """Test creating a job"""
        job = fresh_job_store.create_job(
            job_id="test-job-1",
            project_id="test-project-1",
            agent_type="research",
            input_context={"user_idea": "Test idea"},
        )

        assert job.job_id == "test-job-1"
        assert job.project_id == "test-project-1"
        assert job.status == JobStatusType.QUEUED

    def test_get_job(self, fresh_job_store):
        """Test retrieving a job"""
        fresh_job_store.create_job(
            job_id="test-job-2",
            project_id="test-project-2",
            agent_type="wireframe",
            input_context={},
        )

        job = fresh_job_store.get_job("test-job-2")
        assert job is not None
        assert job.agent_type == "wireframe"

    def test_get_job_not_found(self, fresh_job_store):
        """Test retrieving a non-existent job returns None"""
        assert fresh_job_store.get_job("non-existent") is None

    def test_update_job_status(self, fresh_job_store):
        """Test updating job status"""
        fresh_job_store.create_job(
            job_id="test-job-3",
            project_id="test-project-3",
            agent_type="code",
            input_context={},
        )

        updated_job = fresh_job_store.update_job(
            "test-job-3",
            status=JobStatusType.RUNNING,
            progress=50,
        )

        assert updated_job.status == JobStatusType.RUNNING
        assert updated_job.progress == 50
        assert updated_job.started_at is not None

    def test_update_job_completed(self, fresh_job_store):
        """Test updating job with result"""
        fresh_job_store.create_job(
            job_id="test-job-4",
            project_id="test-project-4",
            agent_type="qa",
            input_context={},
        )

        result = {"issues": []}
        updated_job = fresh_job_store.update_job(
            "test-job-4",
            status=JobStatusType.COMPLETED,
            result=result,
        )

        assert updated_job.result == result
        assert updated_job.completed_at is not None

    def test_update_job_with_error(self, fresh_job_store):
        """Test updating job with error sets FAILED status"""
        fresh_job_store.create_job(
            job_id="test-job-err",
            project_id="test-project-err",
            agent_type="research",
            input_context={},
        )

        updated = fresh_job_store.update_job("test-job-err", error="LLM call failed")

        assert updated.status == JobStatusType.FAILED
        assert updated.error == "LLM call failed"
        assert updated.completed_at is not None

    def test_update_nonexistent_job(self, fresh_job_store):
        """Test updating a non-existent job returns None"""
        assert fresh_job_store.update_job("nope", status=JobStatusType.RUNNING) is None

    def test_progress_clamping(self, fresh_job_store):
        """Test that progress is clamped between 0 and 100"""
        fresh_job_store.create_job(
            job_id="test-clamp",
            project_id="p",
            agent_type="code",
            input_context={},
        )

        j = fresh_job_store.update_job("test-clamp", progress=150)
        assert j.progress == 100.0

        j = fresh_job_store.update_job("test-clamp", progress=-10)
        assert j.progress == 0.0

    def test_get_project_jobs(self, fresh_job_store):
        """Test getting all jobs for a project"""
        project_id = "test-project-5"

        for i in range(3):
            fresh_job_store.create_job(
                job_id=f"test-job-{i}",
                project_id=project_id,
                agent_type="research",
                input_context={},
            )

        jobs = fresh_job_store.get_project_jobs(project_id)
        assert len(jobs) == 3

    def test_get_project_jobs_limit(self, fresh_job_store):
        """Test that the limit parameter caps returned jobs"""
        project_id = "test-project-limit"
        for i in range(10):
            fresh_job_store.create_job(
                job_id=f"limit-job-{i}",
                project_id=project_id,
                agent_type="code",
                input_context={},
            )

        jobs = fresh_job_store.get_project_jobs(project_id, limit=3)
        assert len(jobs) == 3

    def test_get_pending_jobs(self, fresh_job_store):
        """Test getting only pending jobs"""
        fresh_job_store.create_job(
            job_id="pending-1",
            project_id="p1",
            agent_type="research",
            input_context={},
        )
        fresh_job_store.create_job(
            job_id="running-1",
            project_id="p2",
            agent_type="code",
            input_context={},
        )
        fresh_job_store.update_job("running-1", status=JobStatusType.RUNNING)

        pending = fresh_job_store.get_pending_jobs()
        assert len(pending) == 1
        assert pending[0].job_id == "pending-1"

    def test_cleanup_old_jobs(self, fresh_job_store):
        """Test cleanup of old completed jobs"""
        fresh_job_store.create_job(
            job_id="old-job",
            project_id="p-cleanup",
            agent_type="research",
            input_context={},
        )
        job = fresh_job_store._jobs["old-job"]
        job.status = JobStatusType.COMPLETED
        job.completed_at = datetime.utcnow() - timedelta(hours=48)

        removed = fresh_job_store.cleanup_old_jobs(hours=24)
        assert removed == 1
        assert fresh_job_store.get_job("old-job") is None

    def test_cleanup_skips_recent_jobs(self, fresh_job_store):
        """Test cleanup keeps recently completed jobs"""
        fresh_job_store.create_job(
            job_id="recent-job",
            project_id="p-recent",
            agent_type="qa",
            input_context={},
        )
        fresh_job_store.update_job(
            "recent-job", status=JobStatusType.COMPLETED, result={"ok": True}
        )

        removed = fresh_job_store.cleanup_old_jobs(hours=24)
        assert removed == 0
        assert fresh_job_store.get_job("recent-job") is not None


# ─────────────────────────────────────────────────────────────
# Job dataclass tests
# ─────────────────────────────────────────────────────────────


class TestJobSerialization:
    """Tests for Job to_dict / serialize / deserialize"""

    def test_to_dict(self):
        """Test Job.to_dict()"""
        job = Job(
            job_id="ser-1",
            project_id="p-ser",
            agent_type="pedagogy",
            input_context={},
        )

        d = job.to_dict()
        assert d["job_id"] == "ser-1"
        assert d["status"] == "queued"
        assert isinstance(d["created_at"], str)

    def test_serialize_deserialize_roundtrip(self):
        """Test that serialize/deserialize preserves data"""
        original = Job(
            job_id="rt-1",
            project_id="p-rt",
            agent_type="code",
            status=JobStatusType.COMPLETED,
            result={"files": []},
            progress=100.0,
            input_context={"arch": "nextjs"},
        )
        original.started_at = datetime.utcnow()
        original.completed_at = datetime.utcnow()

        restored = Job.deserialize(original.serialize())

        assert restored.job_id == original.job_id
        assert restored.status == original.status
        assert restored.result == original.result
        assert restored.progress == original.progress

    def test_is_complete_property(self):
        """Test is_complete for various statuses"""
        job = Job(job_id="x", project_id="y", agent_type="qa")

        assert not job.is_complete

        job.status = JobStatusType.RUNNING
        assert not job.is_complete

        job.status = JobStatusType.COMPLETED
        assert job.is_complete

        job.status = JobStatusType.FAILED
        assert job.is_complete

    def test_duration_property(self):
        """Test duration calculation"""
        job = Job(job_id="dur", project_id="p", agent_type="code")
        assert job.duration is None

        job.started_at = datetime.utcnow()
        job.completed_at = job.started_at + timedelta(seconds=42)
        assert job.duration == pytest.approx(42.0)
