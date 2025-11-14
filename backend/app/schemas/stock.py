"""Stock schemas for request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StockBase(BaseModel):
    """Base stock schema."""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol (e.g., AAPL)")
    name: Optional[str] = Field(None, max_length=200, description="Company name")
    exchange: Optional[str] = Field(None, max_length=50, description="Exchange (NASDAQ, NYSE, etc.)")


class StockCreate(StockBase):
    """Schema for creating a new stock."""
    pass


class StockResponse(StockBase):
    """Schema for stock response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy models


class StockList(BaseModel):
    """Schema for list of stocks."""
    stocks: list[StockResponse]
    total: int
