"""
Job queue and state management service
Handles async task scheduling and monitoring

Supports two backends:
- Redis (production): Persistent, survives restarts, shared across instances
- In-memory (development fallback): Used when Redis is unavailable
"""

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

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
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["completed_at"] = (
            self.completed_at.isoformat() if self.completed_at else None
        )
        data["status"] = self.status.value
        return data

    def serialize(self) -> str:
        """Serialize to JSON string for Redis storage"""
        return json.dumps(self.to_dict())

    @classmethod
    def deserialize(cls, data: str) -> "Job":
        """Deserialize from JSON string (Redis retrieval)"""
        d = json.loads(data)
        d["status"] = JobStatusType(d["status"])
        d["created_at"] = (
            datetime.fromisoformat(d["created_at"])
            if d.get("created_at")
            else datetime.utcnow()
        )
        d["started_at"] = (
            datetime.fromisoformat(d["started_at"]) if d.get("started_at") else None
        )
        d["completed_at"] = (
            datetime.fromisoformat(d["completed_at"]) if d.get("completed_at") else None
        )
        return cls(**d)

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


class BaseJobStore(ABC):
    """Abstract interface for job storage backends"""

    @abstractmethod
    def create_job(
        self,
        job_id: str,
        project_id: str,
        agent_type: str,
        input_context: Dict[str, Any],
    ) -> Job: ...

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]: ...

    @abstractmethod
    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatusType] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Job]: ...

    @abstractmethod
    def get_project_jobs(self, project_id: str, limit: int = 50) -> List[Job]: ...

    @abstractmethod
    def get_pending_jobs(self) -> List[Job]: ...

    @abstractmethod
    def cleanup_old_jobs(self, hours: int = 24) -> int: ...


class InMemoryJobStore(BaseJobStore):
    """
    In-memory job store — development fallback.
    Data is lost on restart.
    """

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._project_jobs: Dict[str, List[str]] = {}

    def create_job(
        self,
        job_id: str,
        project_id: str,
        agent_type: str,
        input_context: Dict[str, Any],
    ) -> Job:
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
        logger.info(f"[InMemory] Created job: {job_id} for project {project_id}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatusType] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Job]:
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

        if result is not None:
            job.result = result

        if error:
            job.error = error
            job.status = JobStatusType.FAILED
            job.completed_at = datetime.utcnow()

        logger.info(
            f"[InMemory] Updated job {job_id}: status={job.status.value}, progress={job.progress}"
        )
        return job

    def get_project_jobs(self, project_id: str, limit: int = 50) -> List[Job]:
        job_ids = self._project_jobs.get(project_id, [])
        jobs = [self._jobs[jid] for jid in job_ids[-limit:] if jid in self._jobs]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def get_pending_jobs(self) -> List[Job]:
        return [j for j in self._jobs.values() if j.status == JobStatusType.QUEUED]

    def cleanup_old_jobs(self, hours: int = 24) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        to_remove = [
            job_id
            for job_id, job in self._jobs.items()
            if job.is_complete
            and job.completed_at is not None
            and job.completed_at < cutoff
        ]
        for job_id in to_remove:
            job = self._jobs.pop(job_id)
            if job.project_id in self._project_jobs:
                self._project_jobs[job.project_id] = [
                    jid for jid in self._project_jobs[job.project_id] if jid != job_id
                ]
        logger.info(f"[InMemory] Cleaned up {len(to_remove)} old jobs")
        return len(to_remove)


class RedisJobStore(BaseJobStore):
    """
    Redis-backed job store — production backend.
    Jobs persist across restarts and are shared across instances.

    Redis key structure:
    - job:{job_id} → serialized Job (STRING with TTL)
    - project_jobs:{project_id} → sorted set of job_ids (scored by created_at timestamp)
    - pending_jobs → set of job_ids with QUEUED status
    """

    COMPLETED_JOB_TTL = 48 * 3600  # 48 hours

    def __init__(self, redis_url: str):
        import redis as redis_lib

        self._redis = redis_lib.Redis.from_url(redis_url, decode_responses=True)
        try:
            self._redis.ping()
            logger.info("[Redis] Connected to Redis")
        except redis_lib.ConnectionError as e:
            logger.error(f"[Redis] Connection failed: {e}")
            raise

    def create_job(
        self,
        job_id: str,
        project_id: str,
        agent_type: str,
        input_context: Dict[str, Any],
    ) -> Job:
        job = Job(
            job_id=job_id,
            project_id=project_id,
            agent_type=agent_type,
            input_context=input_context,
        )
        pipe = self._redis.pipeline()
        pipe.set(f"job:{job_id}", job.serialize())
        pipe.zadd(f"project_jobs:{project_id}", {job_id: job.created_at.timestamp()})
        pipe.sadd("pending_jobs", job_id)
        pipe.execute()
        logger.info(f"[Redis] Created job: {job_id} for project {project_id}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        data = self._redis.get(f"job:{job_id}")
        if not data:
            return None
        return Job.deserialize(data)

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatusType] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Job]:
        job = self.get_job(job_id)
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

        if result is not None:
            job.result = result

        if error:
            job.error = error
            job.status = JobStatusType.FAILED
            job.completed_at = datetime.utcnow()

        pipe = self._redis.pipeline()
        pipe.set(f"job:{job_id}", job.serialize())
        if job.is_complete:
            pipe.srem("pending_jobs", job_id)
            pipe.expire(f"job:{job_id}", self.COMPLETED_JOB_TTL)
        elif status == JobStatusType.RUNNING:
            pipe.srem("pending_jobs", job_id)
        pipe.execute()

        logger.info(
            f"[Redis] Updated job {job_id}: status={job.status.value}, progress={job.progress}"
        )
        return job

    def get_project_jobs(self, project_id: str, limit: int = 50) -> List[Job]:
        job_ids = self._redis.zrevrange(f"project_jobs:{project_id}", 0, limit - 1)
        jobs = []
        if job_ids:
            pipe = self._redis.pipeline()
            for jid in job_ids:
                pipe.get(f"job:{jid}")
            results = pipe.execute()
            for data in results:
                if data:
                    jobs.append(Job.deserialize(data))
        return jobs

    def get_pending_jobs(self) -> List[Job]:
        job_ids = self._redis.smembers("pending_jobs")
        jobs = []
        if job_ids:
            pipe = self._redis.pipeline()
            for jid in job_ids:
                pipe.get(f"job:{jid}")
            results = pipe.execute()
            for data in results:
                if data:
                    jobs.append(Job.deserialize(data))
        return jobs

    def cleanup_old_jobs(self, hours: int = 24) -> int:
        """
        Remove completed jobs older than specified hours.
        Redis TTL handles most cleanup; this cleans sorted set references.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_ts = cutoff.timestamp()
        removed = 0
        cursor = 0
        while True:
            cursor, keys = self._redis.scan(cursor, match="project_jobs:*", count=100)
            for key in keys:
                old_ids = self._redis.zrangebyscore(key, "-inf", cutoff_ts)
                if old_ids:
                    pipe = self._redis.pipeline()
                    for jid in old_ids:
                        if not self._redis.exists(f"job:{jid}"):
                            pipe.zrem(key, jid)
                            removed += 1
                    pipe.execute()
            if cursor == 0:
                break
        logger.info(f"[Redis] Cleaned up {removed} old job references")
        return removed


def _create_job_store() -> BaseJobStore:
    """
    Factory: create the appropriate job store backend.
    Uses Redis if available, falls back to in-memory for development.
    """
    from app.core.config import settings

    if settings.REDIS_URL:
        try:
            store = RedisJobStore(settings.REDIS_URL)
            return store
        except Exception as e:
            logger.warning(
                f"Redis unavailable ({e}), falling back to in-memory job store"
            )

    logger.info("Using in-memory job store (data will be lost on restart)")
    return InMemoryJobStore()


# Global job store — lazily initialized
_job_store: Optional[BaseJobStore] = None


def get_job_store() -> BaseJobStore:
    """Get or create the global job store instance"""
    global _job_store
    if _job_store is None:
        _job_store = _create_job_store()
    return _job_store


class _JobStoreProxy:
    """Lazy proxy so `from app.services.job_queue import job_store` still works"""

    def __getattr__(self, name: str):
        return getattr(get_job_store(), name)


# Backward-compatible module-level import
job_store = _JobStoreProxy()
