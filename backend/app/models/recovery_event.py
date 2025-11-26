"""RecoveryEvent model for logging crash recovery attempts."""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from app.models.base import BaseModel


class RecoveryEvent(BaseModel):
    """Recovery event logging model."""

    __tablename__ = "recovery_events"

    # Recovery details
    recovery_type = Column(String(50), nullable=False)  # STARTUP, CRASH, MANUAL
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    success = Column(Boolean, nullable=False, default=False)

    # Recovery information
    message = Column(Text, nullable=False)
    discrepancies_found = Column(Integer, nullable=False, default=0)
    actions_taken = Column(Text, nullable=True)

    # Additional metadata
    meta = Column(JSON, nullable=True, default=dict)

    def __repr__(self):
        return f"<RecoveryEvent(id={self.id}, type='{self.recovery_type}', success={self.success})>"
