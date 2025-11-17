"""Job manager for async backtest execution."""
from typing import Dict, Optional
from datetime import datetime
from uuid import uuid4
from enum import Enum

from app.core.logging import get_logger

logger = get_logger("backtest_job_manager")


class JobStatus(Enum):
    """Backtest job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BacktestJob:
    """Backtest job tracker."""

    def __init__(
        self,
        job_id: str,
        request_params: Dict,
        user_id: Optional[str] = None
    ):
        self.job_id = job_id
        self.request_params = request_params
        self.user_id = user_id
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.backtest_run_id: Optional[int] = None
        self.error_message: Optional[str] = None
        self.progress_pct: int = 0

    def start(self):
        """Mark job as running."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()
        logger.info(f"Job {self.job_id} started")

    def complete(self, backtest_run_id: int):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.backtest_run_id = backtest_run_id
        self.progress_pct = 100
        logger.info(f"Job {self.job_id} completed: backtest_id={backtest_run_id}")

    def fail(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        logger.error(f"Job {self.job_id} failed: {error_message}")

    def update_progress(self, progress_pct: int):
        """Update job progress."""
        self.progress_pct = min(100, max(0, progress_pct))

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'backtest_run_id': self.backtest_run_id,
            'error_message': self.error_message,
            'progress_pct': self.progress_pct,
            'request_params': self.request_params
        }


class BacktestJobManager:
    """
    Manager for async backtest jobs.

    Note: This is an in-memory implementation for MVP.
    For production, use Redis or a proper job queue (Celery).
    """

    def __init__(self):
        self._jobs: Dict[str, BacktestJob] = {}
        logger.info("BacktestJobManager initialized (in-memory)")

    def create_job(self, request_params: Dict, user_id: Optional[str] = None) -> str:
        """
        Create a new backtest job.

        Args:
            request_params: Backtest request parameters
            user_id: Optional user identifier

        Returns:
            Job ID (UUID)
        """
        job_id = str(uuid4())
        job = BacktestJob(job_id, request_params, user_id)
        self._jobs[job_id] = job

        logger.info(f"Created job {job_id}: {request_params.get('symbol')}")

        return job_id

    def get_job(self, job_id: str) -> Optional[BacktestJob]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            BacktestJob or None
        """
        return self._jobs.get(job_id)

    def start_job(self, job_id: str):
        """Mark job as running."""
        job = self.get_job(job_id)
        if job:
            job.start()

    def complete_job(self, job_id: str, backtest_run_id: int):
        """Mark job as completed."""
        job = self.get_job(job_id)
        if job:
            job.complete(backtest_run_id)

    def fail_job(self, job_id: str, error_message: str):
        """Mark job as failed."""
        job = self.get_job(job_id)
        if job:
            job.fail(error_message)

    def update_progress(self, job_id: str, progress_pct: int):
        """Update job progress."""
        job = self.get_job(job_id)
        if job:
            job.update_progress(progress_pct)

    def list_jobs(self, user_id: Optional[str] = None, limit: int = 50) -> list:
        """
        List recent jobs.

        Args:
            user_id: Filter by user
            limit: Maximum jobs to return

        Returns:
            List of job dictionaries
        """
        jobs = list(self._jobs.values())

        if user_id:
            jobs = [j for j in jobs if j.user_id == user_id]

        # Sort by created time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return [j.to_dict() for j in jobs[:limit]]

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Remove jobs older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        old_job_ids = [
            job_id for job_id, job in self._jobs.items()
            if job.created_at < cutoff
        ]

        for job_id in old_job_ids:
            del self._jobs[job_id]

        if old_job_ids:
            logger.info(f"Cleaned up {len(old_job_ids)} old jobs")


# Global job manager instance
backtest_job_manager = BacktestJobManager()


from datetime import timedelta
