"""
Job queue and state management service
Handles async task scheduling and monitoring
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from uuid import UUID
from app.core.logging import logger
from app.schemas.protocol import JobStatusType


@dataclass
class Job:
    """Represents an agent job"""

    job_id: str
    project_id: str
    agent_type: str
    status: JobStatusType = JobStatusType.QUEUED
    input_context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        data = asdict(self)
        # Convert datetime to ISO format strings
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        data["status"] = self.status.value
        return data

    @property
    def is_complete(self) -> bool:
        """Check if job is complete"""
        return self.status in [JobStatusType.COMPLETED, JobStatusType.FAILED]

    @property
    def duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()


class JobStore:
    """
    In-memory job store
    In production, replace with Redis or database
    """

    def __init__(self):
        """Initialize job store"""
        self._jobs: Dict[str, Job] = {}
        self._project_jobs: Dict[str, List[str]] = {}  # project_id -> [job_ids]

    def create_job(
        self,
        job_id: str,
        project_id: str,
        agent_type: str,
        input_context: Dict[str, Any],
    ) -> Job:
        """Create and store a new job"""
        job = Job(
            job_id=job_id,
            project_id=project_id,
            agent_type=agent_type,
            input_context=input_context,
        )

        self._jobs[job_id] = job

        if project_id not in self._project_jobs:
            self._project_jobs[project_id] = []
        self._project_jobs[project_id].append(job_id)

        logger.info(f"Created job: {job_id} for project {project_id}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by ID"""
        return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatusType] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Job]:
        """Update job status and progress"""
        job = self._jobs.get(job_id)
        if not job:
            return None

        if status:
            job.status = status
            if status == JobStatusType.RUNNING and not job.started_at:
                job.started_at = datetime.utcnow()
            if job.is_complete:
                job.completed_at = datetime.utcnow()

        if progress is not None:
            job.progress = max(0.0, min(100.0, progress))

        if result:
            job.result = result

        if error:
            job.error = error
            job.status = JobStatusType.FAILED

        logger.info(f"Updated job {job_id}: status={status}, progress={progress}")
        return job

    def get_project_jobs(self, project_id: str, limit: int = 50) -> List[Job]:
        """Get all jobs for a project"""
        job_ids = self._project_jobs.get(project_id, [])
        jobs = [self._jobs[jid] for jid in job_ids[-limit:] if jid in self._jobs]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def get_pending_jobs(self) -> List[Job]:
        """Get all pending (queued) jobs"""
        return [j for j in self._jobs.values() if j.status == JobStatusType.QUEUED]

    def cleanup_old_jobs(self, hours: int = 24) -> int:
        """Remove jobs older than specified hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        to_remove = [
            job_id
            for job_id, job in self._jobs.items()
            if job.is_complete and job.completed_at < cutoff
        ]

        for job_id in to_remove:
            job = self._jobs.pop(job_id)
            if job.project_id in self._project_jobs:
                self._project_jobs[job.project_id] = [
                    jid for jid in self._project_jobs[job.project_id] if jid != job_id
                ]

        logger.info(f"Cleaned up {len(to_remove)} old jobs")
        return len(to_remove)


# Global job store instance
job_store = JobStore()
