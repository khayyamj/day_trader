"""Daily loss limit detector for strategy risk management."""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, time, timezone
from decimal import Decimal

from app.models.strategy import Strategy
from app.models.trade import Trade

logger = logging.getLogger(__name__)


class LossLimitDetector:
    """
    Detector for tracking consecutive losses and enforcing daily loss limits.

    Rules:
    - Track consecutive losses per strategy
    - Pause strategy after 3 consecutive losses in a day
    - Reset counter at start of each trading day (9:30 AM ET)
    - Send alerts when limit is hit
    """

    MAX_CONSECUTIVE_LOSSES = 3
    TRADING_DAY_START_HOUR = 9  # 9:30 AM ET
    TRADING_DAY_START_MINUTE = 30

    def __init__(self, db: Session):
        """
        Initialize LossLimitDetector.

        Args:
            db: Database session
        """
        self.db = db
        logger.info("LossLimitDetector initialized")

    def track_trade_outcome(self, trade_id: int) -> None:
        """
        Track trade outcome and update consecutive loss counter.

        Args:
            trade_id: Trade ID to track

        Raises:
            ValueError: If trade not found or still open
        """
        try:
            trade = self.db.query(Trade).filter(Trade.id == trade_id).first()

            if not trade:
                raise ValueError(f"Trade not found: {trade_id}")

            if trade.status != 'CLOSED':
                logger.warning(f"Trade {trade_id} is not closed, cannot track outcome")
                return

            if trade.profit_loss is None:
                logger.warning(f"Trade {trade_id} has no P&L recorded")
                return

            # Get strategy
            strategy = self.db.query(Strategy).filter(
                Strategy.id == trade.strategy_id
            ).first()

            if not strategy:
                raise ValueError(f"Strategy not found: {trade.strategy_id}")

            # Check if trade was a loss
            is_loss = float(trade.profit_loss) < 0

            if is_loss:
                # Increment consecutive loss counter
                strategy.consecutive_losses_today += 1
                logger.warning(
                    f"Strategy {strategy.name} loss #{strategy.consecutive_losses_today}: "
                    f"${trade.profit_loss:.2f}"
                )

                # Check if loss limit reached
                if self.check_loss_limit(strategy.id):
                    self.pause_strategy_on_limit(strategy.id)
            else:
                # Win - reset consecutive loss counter
                previous_losses = strategy.consecutive_losses_today
                strategy.consecutive_losses_today = 0
                logger.info(
                    f"Strategy {strategy.name} win: ${trade.profit_loss:.2f}. "
                    f"Reset loss counter (was {previous_losses})"
                )

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to track trade outcome: {str(e)}")
            self.db.rollback()
            raise

    def check_loss_limit(self, strategy_id: int) -> bool:
        """
        Check if strategy has hit daily loss limit (3 consecutive losses).

        Args:
            strategy_id: Strategy ID to check

        Returns:
            bool: True if loss limit reached
        """
        try:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id
            ).first()

            if not strategy:
                raise ValueError(f"Strategy not found: {strategy_id}")

            limit_reached = strategy.consecutive_losses_today >= self.MAX_CONSECUTIVE_LOSSES

            if limit_reached:
                logger.error(
                    f"DAILY LOSS LIMIT REACHED: Strategy {strategy.name} "
                    f"({strategy.consecutive_losses_today} consecutive losses)"
                )
            else:
                logger.info(
                    f"Strategy {strategy.name} loss count: "
                    f"{strategy.consecutive_losses_today}/{self.MAX_CONSECUTIVE_LOSSES}"
                )

            return limit_reached

        except Exception as e:
            logger.error(f"Failed to check loss limit: {str(e)}")
            raise

    def pause_strategy_on_limit(self, strategy_id: int) -> None:
        """
        Pause strategy when daily loss limit is hit.

        Args:
            strategy_id: Strategy ID to pause

        Raises:
            ValueError: If strategy not found
        """
        try:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id
            ).first()

            if not strategy:
                raise ValueError(f"Strategy not found: {strategy_id}")

            # Set strategy status to paused
            strategy.status = 'paused'
            self.db.commit()

            logger.error(
                f"Strategy {strategy.name} PAUSED due to {strategy.consecutive_losses_today} "
                f"consecutive losses"
            )

            # Send alert (implementation depends on notification system)
            self._send_alert(strategy)

        except Exception as e:
            logger.error(f"Failed to pause strategy: {str(e)}")
            self.db.rollback()
            raise

    def _send_alert(self, strategy: Strategy) -> None:
        """
        Send alert when daily loss limit is hit.

        Args:
            strategy: Strategy that hit limit

        Note:
            This is a placeholder. In production, integrate with email service
            or notification system (e.g., SendGrid, AWS SES, Slack).
        """
        alert_message = (
            f"TRADING ALERT: Daily Loss Limit Hit\n"
            f"Strategy: {strategy.name}\n"
            f"Consecutive Losses: {strategy.consecutive_losses_today}\n"
            f"Status: PAUSED\n"
            f"Time: {datetime.now(timezone.utc).isoformat()}\n"
            f"Action Required: Review strategy performance before re-enabling"
        )

        # Log alert (in production, send email/SMS/Slack notification)
        logger.critical(alert_message)

        # TODO: Implement actual email/notification sending
        # Example:
        # send_email(
        #     to=settings.ALERT_EMAIL,
        #     subject=f"Trading Alert: {strategy.name} Paused",
        #     body=alert_message
        # )

    def reset_daily_counters(self) -> None:
        """
        Reset consecutive loss counters for all strategies at start of trading day.

        Should be called at 9:30 AM ET each trading day.
        """
        try:
            strategies = self.db.query(Strategy).filter(
                Strategy.consecutive_losses_today > 0
            ).all()

            reset_count = 0
            for strategy in strategies:
                logger.info(
                    f"Resetting loss counter for {strategy.name} "
                    f"(was {strategy.consecutive_losses_today})"
                )
                strategy.consecutive_losses_today = 0
                reset_count += 1

            self.db.commit()

            logger.info(
                f"Daily reset complete: {reset_count} strategies reset at "
                f"{datetime.now(timezone.utc).isoformat()}"
            )

        except Exception as e:
            logger.error(f"Failed to reset daily counters: {str(e)}")
            self.db.rollback()
            raise

    def should_reset_counters(self, current_time: datetime) -> bool:
        """
        Check if it's time to reset daily counters.

        Args:
            current_time: Current datetime (UTC)

        Returns:
            bool: True if current time is at or past trading day start (9:30 AM ET)

        Note:
            This is a simplified check. In production, consider:
            - Market holidays
            - Daylight saving time changes
            - Ensuring reset happens only once per day
        """
        # Convert to ET timezone (simplified - doesn't handle DST)
        # In production, use pytz or zoneinfo for proper timezone handling
        current_hour = current_time.hour
        current_minute = current_time.minute

        is_reset_time = (
            current_hour == self.TRADING_DAY_START_HOUR and
            current_minute >= self.TRADING_DAY_START_MINUTE
        )

        return is_reset_time

    def get_strategy_status(self, strategy_id: int) -> dict:
        """
        Get current loss tracking status for strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            dict: Status information
        """
        try:
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id
            ).first()

            if not strategy:
                raise ValueError(f"Strategy not found: {strategy_id}")

            return {
                'strategy_id': strategy.id,
                'strategy_name': strategy.name,
                'status': strategy.status,
                'consecutive_losses_today': strategy.consecutive_losses_today,
                'loss_limit': self.MAX_CONSECUTIVE_LOSSES,
                'is_paused': strategy.status == 'paused',
                'losses_until_pause': max(
                    0,
                    self.MAX_CONSECUTIVE_LOSSES - strategy.consecutive_losses_today
                )
            }

        except Exception as e:
            logger.error(f"Failed to get strategy status: {str(e)}")
            raise
