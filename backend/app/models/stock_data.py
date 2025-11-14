"""StockData model for OHLCV time-series data."""
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class StockData(BaseModel):
    """OHLCV stock data time-series model."""

    __tablename__ = "stock_data"

    # Foreign key
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    # Time
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # OHLCV data
    open_price = Column(Numeric(10, 2), nullable=False)
    high_price = Column(Numeric(10, 2), nullable=False)
    low_price = Column(Numeric(10, 2), nullable=False)
    close_price = Column(Numeric(10, 2), nullable=False)
    volume = Column(BigInteger, nullable=False)

    # Relationship
    stock = relationship("Stock", backref="stock_data")

    def __repr__(self):
        return f"<StockData(id={self.id}, stock_id={self.stock_id}, timestamp={self.timestamp}, close={self.close_price})>"
