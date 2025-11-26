"""API endpoints for system health monitoring."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.monitoring.health_check import HealthChecker
from app.db.database import get_db

router = APIRouter()


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    """
    Get overall system health status.

    Returns a quick health check of critical components:
    - Database connectivity
    - Broker connection
    - Scheduler status
    - Disk space

    Returns:
        Overall system health with component status
    """
    health_checker = HealthChecker(db)
    return health_checker.get_overall_health()


@router.get("/health/detailed")
def get_health_detailed(db: Session = Depends(get_db)):
    """
    Get detailed system health metrics.

    Returns comprehensive metrics including:
    - Process metrics (CPU, memory, threads)
    - System metrics (uptime, CPU count)
    - Database metrics (trade count, signal count)
    - All component health checks

    Returns:
        Detailed system metrics and health status
    """
    health_checker = HealthChecker(db)

    # Get basic health
    health = health_checker.get_overall_health()

    # Get detailed metrics
    metrics = health_checker.get_detailed_metrics()

    return {
        "health": health,
        "metrics": metrics
    }


@router.get("/health/database")
def get_database_health(db: Session = Depends(get_db)):
    """
    Check database connectivity and performance.

    Returns:
        Database health status
    """
    health_checker = HealthChecker(db)
    return health_checker.check_database()


@router.get("/health/broker")
def get_broker_health(db: Session = Depends(get_db)):
    """
    Check broker (IBKR) API connectivity.

    Returns:
        Broker connection health status
    """
    health_checker = HealthChecker(db)
    return health_checker.check_broker_connection()


@router.get("/health/scheduler")
def get_scheduler_health(db: Session = Depends(get_db)):
    """
    Check scheduler status and scheduled jobs.

    Returns:
        Scheduler health status with job list
    """
    health_checker = HealthChecker(db)
    return health_checker.check_scheduler()


@router.get("/health/disk")
def get_disk_health(db: Session = Depends(get_db)):
    """
    Check disk space availability.

    Returns:
        Disk space metrics and status
    """
    health_checker = HealthChecker(db)
    return health_checker.check_disk_space()
