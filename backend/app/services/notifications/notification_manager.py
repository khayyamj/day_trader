"""Notification manager that coordinates all notification types."""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from .email_service import email_service

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages and coordinates all system notifications."""

    def __init__(self):
        """Initialize notification manager."""
        self.email_service = email_service

    def notify_trade_execution(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        strategy_name: str,
        order_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Send notification when a trade is executed.

        Args:
            symbol: Stock ticker symbol
            action: Trade action (BUY, SELL, ENTRY, EXIT)
            quantity: Number of shares
            price: Execution price
            strategy_name: Name of the strategy that triggered the trade
            order_id: Broker order ID (optional)
            reason: Reason for the trade (optional)

        Returns:
            bool: True if notification sent successfully
        """
        try:
            context = {
                "symbol": symbol,
                "action": action.upper(),
                "quantity": quantity,
                "price": price,
                "strategy_name": strategy_name,
                "order_id": order_id,
                "reason": reason,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            html_body = self.email_service.render_template("trade_execution.html", context)
            subject = f"Trade Executed: {action} {quantity} {symbol} @ ${price:.2f}"

            return self.email_service.send_email(
                subject=subject,
                html_body=html_body
            )

        except Exception as e:
            logger.error(f"Failed to send trade execution notification: {e}")
            return False

    def notify_risk_warning(
        self,
        warning_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        action_required: Optional[str] = None
    ) -> bool:
        """
        Send notification for risk warnings (e.g., daily loss limit approaching).

        Args:
            warning_type: Type of warning (e.g., "Daily Loss Limit Warning")
            message: Warning message
            details: Additional details as key-value pairs
            action_required: Description of required action (if any)

        Returns:
            bool: True if notification sent successfully
        """
        try:
            context = {
                "alert_type": warning_type,
                "severity": "WARNING",
                "message": message,
                "details": details or {},
                "action_required": action_required,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            html_body = self.email_service.render_template("alert.html", context)
            subject = f"⚠️ Risk Warning: {warning_type}"

            return self.email_service.send_email(
                subject=subject,
                html_body=html_body
            )

        except Exception as e:
            logger.error(f"Failed to send risk warning notification: {e}")
            return False

    def notify_system_error(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "CRITICAL"
    ) -> bool:
        """
        Send notification for critical system errors and crashes.

        Args:
            error_type: Type of error (e.g., "Database Connection Failed")
            message: Error message
            details: Additional error details as key-value pairs
            severity: Error severity (CRITICAL, WARNING, INFO)

        Returns:
            bool: True if notification sent successfully
        """
        try:
            context = {
                "alert_type": error_type,
                "severity": severity.upper(),
                "message": message,
                "details": details or {},
                "action_required": "Please check the system logs and resolve the issue.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            html_body = self.email_service.render_template("alert.html", context)
            subject = f"🚨 System Error: {error_type}"

            return self.email_service.send_email(
                subject=subject,
                html_body=html_body
            )

        except Exception as e:
            logger.error(f"Failed to send system error notification: {e}")
            return False

    def send_daily_summary(
        self,
        date: str,
        total_pnl: float,
        trades_count: int,
        win_rate: float,
        open_positions: int,
        trades: List[Dict[str, Any]],
        positions: Optional[List[Dict[str, Any]]] = None,
        watchlist: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send daily trading summary email.

        Args:
            date: Summary date
            total_pnl: Total profit/loss for the day
            trades_count: Number of trades executed
            win_rate: Win rate percentage
            open_positions: Number of open positions
            trades: List of trades with details
            positions: List of current open positions
            watchlist: Tomorrow's watchlist with stocks near signals

        Returns:
            bool: True if notification sent successfully
        """
        try:
            context = {
                "date": date,
                "total_pnl": total_pnl,
                "trades_count": trades_count,
                "win_rate": win_rate,
                "open_positions": open_positions,
                "trades": trades,
                "positions": positions or [],
                "watchlist": watchlist or [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            html_body = self.email_service.render_template("daily_summary.html", context)
            subject = f"Daily Trading Summary - {date}"

            return self.email_service.send_email(
                subject=subject,
                html_body=html_body
            )

        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False


# Global notification manager instance
notification_manager = NotificationManager()
