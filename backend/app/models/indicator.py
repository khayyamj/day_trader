"""Indicator model for calculated technical indicators."""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Indicator(BaseModel):
    """Technical indicator values model."""

    __tablename__ = "indicators"

    # Foreign key
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    # Indicator details
    indicator_name = Column(String(50), nullable=False, index=True)  # MACD, RSI, SMA, EMA, etc.
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Numeric(20, 8), nullable=False)

    # Additional metadata (e.g., MACD line, signal line, histogram)
    meta = Column(JSON, nullable=True, default=dict)

    # Relationship
    stock = relationship("Stock", backref="indicators")

    def __repr__(self):
        return f"<Indicator(id={self.id}, name='{self.indicator_name}', value={self.value})>"
