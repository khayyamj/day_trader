"""Market data schemas for API responses."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class OHLCVBar(BaseModel):
    """Single OHLCV bar/candle."""
    datetime: str = Field(..., description="Timestamp of the bar")
    open: str = Field(..., description="Opening price")
    high: str = Field(..., description="High price")
    low: str = Field(..., description="Low price")
    close: str = Field(..., description="Closing price")
    volume: str = Field(..., description="Volume")


class TimeSeriesResponse(BaseModel):
    """Response from time series API."""
    meta: dict
    values: list[OHLCVBar]
    status: str = "ok"


class QuoteData(BaseModel):
    """Real-time quote data."""
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = "USD"
    datetime: Optional[str] = None
    timestamp: Optional[int] = None
    open: Optional[str] = None
    high: Optional[str] = None
    low: Optional[str] = None
    close: Optional[str] = None
    volume: Optional[str] = None
    previous_close: Optional[str] = None
    change: Optional[str] = None
    percent_change: Optional[str] = None
    is_market_open: Optional[bool] = None


class StockDataCreate(BaseModel):
    """Schema for creating stock data record."""
    stock_id: int
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int


class FetchHistoricalRequest(BaseModel):
    """Request to fetch historical data."""
    symbol: str = Field(..., description="Stock symbol")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    interval: str = Field(default="1day", description="Time interval")


class FetchHistoricalResponse(BaseModel):
    """Response from historical data fetch."""
    symbol: str
    records_fetched: int
    records_stored: int
    start_date: str
    end_date: str
    status: str
