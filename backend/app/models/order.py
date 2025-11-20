"""Order model for order management."""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Order(BaseModel):
    """Order management model."""

    __tablename__ = "orders"

    # Foreign keys
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    # Order details
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)

    # Prices
    limit_price = Column(Numeric(10, 2), nullable=True)
    stop_price = Column(Numeric(10, 2), nullable=True)
    filled_price = Column(Numeric(10, 2), nullable=True)

    # Status
    status = Column(String(20), nullable=False)  # PENDING, FILLED, CANCELLED, REJECTED
    broker_order_id = Column(String(100), nullable=True, unique=True, index=True)

    # Timestamps
    submitted_at = Column(DateTime(timezone=True), nullable=False)
    filled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    trade = relationship("Trade", back_populates="orders", lazy="select")
    stock = relationship("Stock", back_populates="orders", lazy="select")

    def __repr__(self):
        return f"<Order(id={self.id}, type='{self.order_type}', status='{self.status}')>"
