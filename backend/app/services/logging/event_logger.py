"""Enhanced event logging with structured JSON format and database persistence."""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.strategy_event import StrategyEvent

logger = logging.getLogger(__name__)


class StructuredLogger:
    """
    Enhanced logger with structured JSON output and database persistence.
    """

    def __init__(self, name: str = "trading_bot"):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self._setup_json_formatter()

    def _setup_json_formatter(self):
        """Set up JSON formatter for structured logging."""
        # Create custom formatter that outputs JSON
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }

                # Add context data if present
                if hasattr(record, "trade_id"):
                    log_data["trade_id"] = record.trade_id
                if hasattr(record, "strategy_id"):
                    log_data["strategy_id"] = record.strategy_id
                if hasattr(record, "user_id"):
                    log_data["user_id"] = record.user_id
                if hasattr(record, "context"):
                    log_data["context"] = record.context

                # Add exception info if present
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)

                return json.dumps(log_data)

        # Apply JSON formatter to all handlers
        for handler in self.logger.handlers:
            handler.setFormatter(JsonFormatter())

    def log_with_context(
        self,
        level: str,
        message: str,
        trade_id: Optional[int] = None,
        strategy_id: Optional[int] = None,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log message with contextual information.

        Args:
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            trade_id: Optional trade ID
            strategy_id: Optional strategy ID
            user_id: Optional user ID
            context: Optional additional context dict
        """
        extra = {}
        if trade_id is not None:
            extra["trade_id"] = trade_id
        if strategy_id is not None:
            extra["strategy_id"] = strategy_id
        if user_id is not None:
            extra["user_id"] = user_id
        if context:
            extra["context"] = context

        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=extra)


class EventLogger:
    """
    Event logger that logs to both files and database.
    """

    def __init__(self):
        """Initialize event logger."""
        self.structured_logger = StructuredLogger()
        self.logger = logging.getLogger(__name__)

    def log_event(
        self,
        db: Session,
        event_type: str,
        message: str,
        strategy_id: Optional[int] = None,
        severity: str = "INFO",
        trade_id: Optional[int] = None,
        user_id: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None
    ):
        """
        Log event to both file/console and database.

        Args:
            db: Database session
            event_type: Type of event (TRADE, SIGNAL, ORDER, RISK, ERROR, etc.)
            message: Event message
            strategy_id: Optional strategy ID
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            trade_id: Optional trade ID for context
            user_id: Optional user ID for context
            meta: Optional metadata dictionary
        """
        # Log to file/console with structured format
        context = {
            "event_type": event_type,
            "severity": severity
        }
        if meta:
            context.update(meta)

        self.structured_logger.log_with_context(
            level=severity,
            message=message,
            trade_id=trade_id,
            strategy_id=strategy_id,
            user_id=user_id,
            context=context
        )

        # Log critical events to database
        if severity in ["ERROR", "CRITICAL"] or event_type in ["TRADE", "SIGNAL", "ORDER", "RISK"]:
            try:
                if strategy_id:
                    event = StrategyEvent(
                        strategy_id=strategy_id,
                        event_type=event_type,
                        severity=severity,
                        timestamp=datetime.utcnow(),
                        message=message,
                        meta=meta or {}
                    )
                    db.add(event)
                    db.commit()
            except Exception as e:
                self.logger.error(f"Failed to log event to database: {e}")
                db.rollback()

    def log_trade_execution(
        self,
        db: Session,
        strategy_id: int,
        trade_id: int,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        meta: Optional[Dict[str, Any]] = None
    ):
        """Log trade execution event."""
        message = f"Trade executed: {action} {quantity} {symbol} @ ${price:.2f}"
        trade_meta = {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price
        }
        if meta:
            trade_meta.update(meta)

        self.log_event(
            db=db,
            event_type="TRADE",
            message=message,
            strategy_id=strategy_id,
            trade_id=trade_id,
            severity="INFO",
            meta=trade_meta
        )

    def log_signal_generation(
        self,
        db: Session,
        strategy_id: int,
        symbol: str,
        signal_type: str,
        meta: Optional[Dict[str, Any]] = None
    ):
        """Log signal generation event."""
        message = f"Signal generated: {signal_type} for {symbol}"
        signal_meta = {
            "symbol": symbol,
            "signal_type": signal_type
        }
        if meta:
            signal_meta.update(meta)

        self.log_event(
            db=db,
            event_type="SIGNAL",
            message=message,
            strategy_id=strategy_id,
            severity="INFO",
            meta=signal_meta
        )

    def log_order_placement(
        self,
        db: Session,
        strategy_id: int,
        order_id: str,
        symbol: str,
        action: str,
        quantity: int,
        meta: Optional[Dict[str, Any]] = None
    ):
        """Log order placement event."""
        message = f"Order placed: {order_id} - {action} {quantity} {symbol}"
        order_meta = {
            "order_id": order_id,
            "symbol": symbol,
            "action": action,
            "quantity": quantity
        }
        if meta:
            order_meta.update(meta)

        self.log_event(
            db=db,
            event_type="ORDER",
            message=message,
            strategy_id=strategy_id,
            severity="INFO",
            meta=order_meta
        )

    def log_risk_rejection(
        self,
        db: Session,
        strategy_id: int,
        symbol: str,
        reason: str,
        meta: Optional[Dict[str, Any]] = None
    ):
        """Log risk management rejection event."""
        message = f"Trade rejected by risk management: {symbol} - {reason}"
        risk_meta = {
            "symbol": symbol,
            "reason": reason
        }
        if meta:
            risk_meta.update(meta)

        self.log_event(
            db=db,
            event_type="RISK",
            message=message,
            strategy_id=strategy_id,
            severity="WARNING",
            meta=risk_meta
        )


# Global event logger instance
event_logger = EventLogger()
