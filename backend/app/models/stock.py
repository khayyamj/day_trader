"""Stock model for traded stocks."""
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Stock(BaseModel):
    """Stock/symbol model."""

    __tablename__ = "stocks"

    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=True)
    exchange = Column(String(50), nullable=True)

    # Relationships
    trades = relationship("Trade", back_populates="stock")
    orders = relationship("Order", back_populates="stock")

    def __repr__(self):
        return f"<Stock(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"
