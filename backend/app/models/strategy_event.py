"""StrategyEvent model for strategy execution events and logging."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class StrategyEvent(BaseModel):
    """Strategy event logging model."""

    __tablename__ = "strategy_events"

    # Foreign key
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # START, STOP, ERROR, TRADE, SIGNAL
    severity = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Additional event metadata
    meta = Column(JSON, nullable=True, default=dict)

    # Relationship
    strategy = relationship("Strategy", backref="events")

    def __repr__(self):
        return f"<StrategyEvent(id={self.id}, type='{self.event_type}', severity='{self.severity}')>"
