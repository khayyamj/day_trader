"""SystemState model for tracking application health and heartbeat."""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.models.base import BaseModel


class SystemState(BaseModel):
    """System state tracking model."""

    __tablename__ = "system_state"

    # Heartbeat tracking
    last_updated = Column(DateTime(timezone=True), nullable=False, index=True)
    system_status = Column(String(20), nullable=False, default="RUNNING")  # RUNNING, STOPPED, ERROR

    # System metadata
    metadata = Column(JSON, nullable=True, default=dict)

    def __repr__(self):
        return f"<SystemState(id={self.id}, status='{self.system_status}', last_updated={self.last_updated})>"
