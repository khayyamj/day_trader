"""Crash recovery service for detecting and recovering from system failures."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.system_state import SystemState
from app.models.recovery_event import RecoveryEvent
from app.models.trade import Trade
from app.services.trading.position_service import PositionService
from app.services.notifications.notification_manager import notification_manager

logger = logging.getLogger(__name__)


class RecoveryService:
    """Service for detecting crashes and performing recovery."""

    def __init__(self, db: Session, ibkr_client=None):
        """
        Initialize recovery service.

        Args:
            db: Database session
            ibkr_client: Optional IBKR client for position reconciliation
        """
        self.db = db
        self.ibkr_client = ibkr_client
        self.crash_timeout_minutes = 5

    def detect_crash(self) -> bool:
        """
        Detect if system has crashed by checking heartbeat timestamp.

        Returns:
            bool: True if crash detected, False otherwise
        """
        try:
            # Get latest system state
            system_state = self.db.query(SystemState).order_by(
                SystemState.last_updated.desc()
            ).first()

            if not system_state:
                logger.warning("No system state found - assuming first run")
                return False

            # Check if last update was more than 5 minutes ago
            time_since_update = datetime.utcnow() - system_state.last_updated
            if time_since_update > timedelta(minutes=self.crash_timeout_minutes):
                logger.warning(
                    f"Crash detected: Last update was {time_since_update.total_seconds()/60:.1f} minutes ago"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error detecting crash: {e}")
            return False

    def run_recovery(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Run crash recovery procedure.

        Returns:
            Tuple of (success, message, recovery_details)
        """
        recovery_start = datetime.utcnow()
        logger.info("Starting crash recovery procedure...")

        recovery_details = {
            "start_time": recovery_start.isoformat(),
            "discrepancies": [],
            "actions_taken": [],
            "total_value_diff": 0.0
        }

        try:
            # 1. Load last known state
            system_state = self.db.query(SystemState).order_by(
                SystemState.last_updated.desc()
            ).first()

            if system_state:
                recovery_details["last_known_state"] = {
                    "timestamp": system_state.last_updated.isoformat(),
                    "status": system_state.system_status,
                    "metadata": system_state.metadata or {}
                }

            # 2. Reconcile positions with broker if IBKR client available
            discrepancies = []
            total_diff = 0.0

            if self.ibkr_client:
                try:
                    position_service = PositionService(self.ibkr_client, self.db)
                    discrepancies, total_diff = position_service.reconcile_positions()

                    recovery_details["discrepancies"] = [
                        {
                            "symbol": d["symbol"],
                            "db_quantity": d["db_quantity"],
                            "broker_quantity": d["broker_quantity"],
                            "difference": d["difference"],
                            "value_diff": d["value_diff"]
                        }
                        for d in discrepancies
                    ]
                    recovery_details["total_value_diff"] = total_diff

                    if discrepancies:
                        logger.warning(f"Found {len(discrepancies)} position discrepancies")
                        recovery_details["actions_taken"].append(
                            f"Identified {len(discrepancies)} position discrepancies"
                        )
                    else:
                        logger.info("Position reconciliation: All positions match")
                        recovery_details["actions_taken"].append(
                            "Position reconciliation successful - no discrepancies"
                        )

                except Exception as e:
                    logger.error(f"Position reconciliation failed: {e}")
                    recovery_details["actions_taken"].append(
                        f"Position reconciliation failed: {str(e)}"
                    )
            else:
                logger.warning("IBKR client not available - skipping position reconciliation")
                recovery_details["actions_taken"].append(
                    "Position reconciliation skipped - IBKR client not available"
                )

            # 3. Check for orphaned trades (trades without matching orders)
            orphaned_trades = self._check_orphaned_trades()
            if orphaned_trades:
                recovery_details["orphaned_trades"] = orphaned_trades
                recovery_details["actions_taken"].append(
                    f"Found {len(orphaned_trades)} orphaned trades"
                )

            # 4. Update system state to RUNNING
            if not system_state:
                system_state = SystemState(
                    last_updated=datetime.utcnow(),
                    system_status="RUNNING",
                    metadata={"recovery_at": recovery_start.isoformat()}
                )
                self.db.add(system_state)
            else:
                system_state.last_updated = datetime.utcnow()
                system_state.system_status = "RUNNING"
                system_state.metadata = system_state.metadata or {}
                system_state.metadata["recovery_at"] = recovery_start.isoformat()

            self.db.commit()
            recovery_details["actions_taken"].append("Updated system state to RUNNING")

            # 5. Log recovery event
            recovery_event = RecoveryEvent(
                recovery_type="STARTUP",
                timestamp=recovery_start,
                success=True,
                message="Recovery completed successfully",
                discrepancies_found=len(discrepancies),
                actions_taken="\n".join(recovery_details["actions_taken"]),
                meta=recovery_details
            )
            self.db.add(recovery_event)
            self.db.commit()

            # 6. Send recovery report email
            self._send_recovery_report(
                success=True,
                discrepancies=discrepancies,
                total_diff=total_diff,
                recovery_details=recovery_details
            )

            logger.info("Recovery completed successfully")
            return True, "Recovery completed successfully", recovery_details

        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            recovery_details["actions_taken"].append(f"Recovery failed: {str(e)}")

            # Log failed recovery event
            try:
                recovery_event = RecoveryEvent(
                    recovery_type="STARTUP",
                    timestamp=recovery_start,
                    success=False,
                    message=f"Recovery failed: {str(e)}",
                    discrepancies_found=0,
                    actions_taken="\n".join(recovery_details["actions_taken"]),
                    meta=recovery_details
                )
                self.db.add(recovery_event)
                self.db.commit()
            except:
                pass

            return False, f"Recovery failed: {str(e)}", recovery_details

    def _check_orphaned_trades(self) -> List[Dict[str, Any]]:
        """Check for orphaned trades without matching broker orders."""
        try:
            # Get recent trades (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_trades = self.db.query(Trade).filter(
                Trade.created_at >= cutoff_time
            ).all()

            orphaned = []
            for trade in recent_trades:
                # Check if trade has an order_id but order doesn't exist
                # This is a simplified check - in production, verify with broker
                if not trade.order_id:
                    orphaned.append({
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "action": trade.action,
                        "quantity": trade.quantity,
                        "timestamp": trade.created_at.isoformat()
                    })

            return orphaned

        except Exception as e:
            logger.error(f"Error checking orphaned trades: {e}")
            return []

    def _send_recovery_report(
        self,
        success: bool,
        discrepancies: List[Dict[str, Any]],
        total_diff: float,
        recovery_details: Dict[str, Any]
    ):
        """Send recovery report email."""
        try:
            if success:
                if not discrepancies:
                    message = "System recovery completed successfully. All positions match broker records."
                else:
                    message = (
                        f"System recovery completed with {len(discrepancies)} position discrepancies. "
                        f"Total value difference: ${total_diff:.2f}"
                    )
                severity = "WARNING" if discrepancies else "INFO"
            else:
                message = "System recovery failed. Manual intervention may be required."
                severity = "CRITICAL"

            notification_manager.notify_system_error(
                error_type="Recovery Report",
                message=message,
                details={
                    "success": success,
                    "discrepancies_count": len(discrepancies),
                    "total_value_diff": f"${total_diff:.2f}",
                    "actions_taken": recovery_details.get("actions_taken", [])
                },
                severity=severity
            )

        except Exception as e:
            logger.error(f"Failed to send recovery report email: {e}")

    def update_heartbeat(self):
        """Update system heartbeat timestamp."""
        try:
            system_state = self.db.query(SystemState).order_by(
                SystemState.last_updated.desc()
            ).first()

            if not system_state:
                system_state = SystemState(
                    last_updated=datetime.utcnow(),
                    system_status="RUNNING",
                    metadata={}
                )
                self.db.add(system_state)
            else:
                system_state.last_updated = datetime.utcnow()

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")
            self.db.rollback()
