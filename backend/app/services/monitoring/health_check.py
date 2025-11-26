"""Health check service for monitoring system components."""
import logging
import shutil
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class HealthChecker:
    """Service for checking health of various system components."""

    def __init__(self, db: Session):
        """
        Initialize health checker.

        Args:
            db: Database session
        """
        self.db = db

    def check_database(self) -> Dict[str, Any]:
        """
        Check database connection and query.

        Returns:
            Dict with status and details
        """
        try:
            # Test connection with simple query
            result = self.db.execute(text("SELECT 1")).scalar()

            if result == 1:
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "response_time_ms": 0  # Could add timing
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Database query returned unexpected result",
                    "error": f"Expected 1, got {result}"
                }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": "Database connection failed",
                "error": str(e)
            }

    def check_broker_connection(self) -> Dict[str, Any]:
        """
        Check IBKR broker API connection.

        Returns:
            Dict with status and details
        """
        try:
            from app.core.config import settings
            from app.services.trading.ibkr_client import IBKRClient

            # Try to create and connect client
            client = IBKRClient(
                host=settings.IBKR_HOST,
                port=settings.IBKR_PORT,
                client_id=settings.IBKR_CLIENT_ID + 100  # Use different client ID
            )

            try:
                client.connect(timeout=5)
                is_connected = client.is_connected()

                if is_connected:
                    client.disconnect()
                    return {
                        "status": "healthy",
                        "message": "Broker connection successful",
                        "host": settings.IBKR_HOST,
                        "port": settings.IBKR_PORT
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": "Broker connection failed",
                        "error": "Not connected after connection attempt"
                    }

            except Exception as e:
                return {
                    "status": "unhealthy",
                    "message": "Broker connection failed",
                    "error": str(e)
                }

        except Exception as e:
            logger.error(f"Broker health check failed: {e}")
            return {
                "status": "degraded",
                "message": "Broker health check unavailable",
                "error": str(e)
            }

    def check_scheduler(self) -> Dict[str, Any]:
        """
        Check if scheduler is running and jobs are scheduled.

        Returns:
            Dict with status and details
        """
        try:
            from app.services.data.scheduler import data_scheduler

            if not data_scheduler._is_running:
                return {
                    "status": "unhealthy",
                    "message": "Scheduler is not running"
                }

            # Get scheduled jobs
            jobs = data_scheduler.scheduler.get_jobs()
            job_info = [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]

            return {
                "status": "healthy",
                "message": f"Scheduler running with {len(jobs)} jobs",
                "jobs": job_info
            }

        except Exception as e:
            logger.error(f"Scheduler health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": "Scheduler health check failed",
                "error": str(e)
            }

    def check_disk_space(self, warning_threshold_gb: float = 1.0) -> Dict[str, Any]:
        """
        Check available disk space.

        Args:
            warning_threshold_gb: Threshold in GB to warn (default: 1GB)

        Returns:
            Dict with status and details
        """
        try:
            disk_usage = shutil.disk_usage("/")

            total_gb = disk_usage.total / (1024 ** 3)
            used_gb = disk_usage.used / (1024 ** 3)
            free_gb = disk_usage.free / (1024 ** 3)
            percent_used = (disk_usage.used / disk_usage.total) * 100

            status = "healthy"
            message = f"Sufficient disk space available"

            if free_gb < warning_threshold_gb:
                status = "warning"
                message = f"Low disk space: {free_gb:.2f}GB free"

            return {
                "status": status,
                "message": message,
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent_used": round(percent_used, 2)
            }

        except Exception as e:
            logger.error(f"Disk space health check failed: {e}")
            return {
                "status": "unknown",
                "message": "Disk space check failed",
                "error": str(e)
            }

    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health by checking all components.

        Returns:
            Dict with overall status and component details
        """
        timestamp = datetime.utcnow().isoformat()

        # Check all components
        database = self.check_database()
        broker = self.check_broker_connection()
        scheduler = self.check_scheduler()
        disk = self.check_disk_space()

        # Determine overall status
        components = [database, broker, scheduler, disk]
        statuses = [c["status"] for c in components]

        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses or "warning" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "timestamp": timestamp,
            "components": {
                "database": database,
                "broker": broker,
                "scheduler": scheduler,
                "disk": disk
            }
        }

    def get_detailed_metrics(self) -> Dict[str, Any]:
        """
        Get detailed system metrics including uptime and resource usage.

        Returns:
            Dict with detailed system metrics
        """
        try:
            import psutil
            import os

            # Get process info
            process = psutil.Process(os.getpid())

            # Get system info
            cpu_percent = process.cpu_percent(interval=1)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            # Get system uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = (datetime.now() - boot_time).total_seconds()

            # Get database metrics
            from app.models.trade import Trade
            from app.models.signal import Signal

            trade_count = self.db.query(Trade).count()
            signal_count = self.db.query(Signal).count()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "process": {
                    "pid": os.getpid(),
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_mb": round(memory_mb, 2),
                    "threads": process.num_threads()
                },
                "system": {
                    "uptime_hours": round(uptime_seconds / 3600, 2),
                    "cpu_count": psutil.cpu_count()
                },
                "database": {
                    "total_trades": trade_count,
                    "total_signals": signal_count
                }
            }

        except Exception as e:
            logger.error(f"Failed to get detailed metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
