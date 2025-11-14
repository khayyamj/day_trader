"""Trade model for executed trades."""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Trade(BaseModel):
    """Trade execution record model."""

    __tablename__ = "trades"

    # Foreign keys
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    # Entry details
    entry_time = Column(DateTime(timezone=True), nullable=False, index=True)
    entry_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Exit details
    exit_time = Column(DateTime(timezone=True), nullable=True, index=True)
    exit_price = Column(Numeric(10, 2), nullable=True)

    # P&L
    profit_loss = Column(Numeric(12, 2), nullable=True)
    profit_loss_percent = Column(Numeric(8, 4), nullable=True)

    # Risk management
    stop_loss = Column(Numeric(10, 2), nullable=True)
    take_profit = Column(Numeric(10, 2), nullable=True)

    # Trade metadata
    trade_type = Column(String(20), nullable=False)  # LONG, SHORT
    status = Column(String(20), nullable=False)  # OPEN, CLOSED, STOPPED

    # Market context (JSONB for indicators at entry/exit)
    market_context = Column(JSON, nullable=True, default=dict)

    # Relationships
    strategy = relationship("Strategy", backref="trades")
    stock = relationship("Stock", backref="trades")

    def __repr__(self):
        return f"<Trade(id={self.id}, stock_id={self.stock_id}, status='{self.status}', pnl={self.profit_loss})>"
