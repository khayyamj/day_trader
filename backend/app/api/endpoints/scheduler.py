"""Scheduler API endpoints."""
from fastapi import APIRouter, HTTPException

from app.services.data.scheduler import data_scheduler
from app.core.logging import get_logger

logger = get_logger("scheduler_api")

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_scheduler_status():
    """
    Get scheduler status and job information.

    Returns:
        Scheduler state, job list, and next run times
    """
    logger.info("Scheduler status requested")
    status = data_scheduler.get_status()
    return status


@router.post("/trigger/{job_id}")
async def trigger_job(job_id: str):
    """
    Manually trigger a scheduled job.

    Args:
        job_id: Job identifier (e.g., 'daily_bar_update')

    Returns:
        Success message

    Use this to test the daily bar update job without waiting until 4:05 PM.
    """
    logger.info(f"Manual job trigger requested: {job_id}")

    try:
        data_scheduler.trigger_job_now(job_id)
        return {
            "status": "success",
            "message": f"Job '{job_id}' triggered successfully"
        }
    except ValueError as e:
        logger.error(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail=str(e))
