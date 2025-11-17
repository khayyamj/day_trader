"""Strategy model for trading strategies."""
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON
from app.models.base import BaseModel


class Strategy(BaseModel):
    """Trading strategy model."""

    __tablename__ = "strategies"

    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False, default=dict)
    active = Column(Boolean, default=True, nullable=False)

    # State management
    status = Column(String(20), default="active", nullable=False)  # active, paused, warming, error
    warm_up_bars_remaining = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}', status='{self.status}')>"
