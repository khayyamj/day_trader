"""Signal model for trade signals."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Signal(BaseModel):
    """Trade signal model."""

    __tablename__ = "trade_signals"

    # Foreign keys
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    # Signal details
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    signal_time = Column(DateTime(timezone=True), nullable=False, index=True)
    executed = Column(Boolean, default=False, nullable=False)

    # Signal reasons and context
    reasons = Column(JSON, nullable=True, default=list)  # List of reasons for signal
    indicator_values = Column(JSON, nullable=True, default=dict)  # Indicator values at signal time

    # Relationships
    strategy = relationship("Strategy", backref="signals")
    stock = relationship("Stock", backref="signals")

    def __repr__(self):
        return f"<Signal(id={self.id}, type='{self.signal_type}', executed={self.executed})>"
