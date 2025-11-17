"""Indicator schemas for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class IndicatorConfig(BaseModel):
    """Configuration for a single indicator."""
    type: str = Field(..., description="Indicator type (ema, rsi, etc.)")
    period: int = Field(..., description="Indicator period")
    column: str = Field(default="close", description="Column to calculate on")


class IndicatorRequest(BaseModel):
    """Request to calculate indicators for a stock."""
    symbol: str = Field(..., description="Stock symbol")
    indicators: Optional[Dict[str, IndicatorConfig]] = Field(
        None,
        description="Dictionary of indicators to calculate. If not provided, uses defaults (EMA 20/50, RSI 14)"
    )
    lookback_days: int = Field(
        default=100,
        description="Number of days to look back for historical data"
    )
    save_to_db: bool = Field(
        default=False,
        description="Whether to save calculated indicators to database"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "indicators": {
                    "ema_20": {"type": "ema", "period": 20},
                    "ema_50": {"type": "ema", "period": 50},
                    "rsi_14": {"type": "rsi", "period": 14}
                },
                "lookback_days": 100,
                "save_to_db": False
            }
        }


class IndicatorValue(BaseModel):
    """Single indicator value at a point in time."""
    timestamp: datetime
    value: float


class IndicatorSeries(BaseModel):
    """Time series of indicator values."""
    name: str
    type: str
    period: int
    values: List[IndicatorValue]


class WarmUpStatus(BaseModel):
    """Warm-up status for indicators."""
    overall: bool = Field(..., description="Whether overall warm-up is complete (100+ bars)")
    indicators: Dict[str, bool] = Field(..., description="Warm-up status for each indicator")


class IndicatorResponse(BaseModel):
    """Response containing calculated indicators."""
    symbol: str
    total_bars: int
    date_range: Dict[str, str] = Field(..., description="Start and end dates")
    warm_up_status: WarmUpStatus
    indicators: Dict[str, List[float]] = Field(..., description="Calculated indicator values")
    latest_values: Dict[str, float] = Field(..., description="Most recent indicator values")
    status: str = "ok"

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "total_bars": 100,
                "date_range": {
                    "start": "2025-08-09",
                    "end": "2025-11-17"
                },
                "warm_up_status": {
                    "overall": True,
                    "indicators": {
                        "ema_20": True,
                        "ema_50": True,
                        "rsi_14": True
                    }
                },
                "indicators": {
                    "ema_20": [150.25, 150.50, 151.00],
                    "ema_50": [148.75, 149.00, 149.25],
                    "rsi_14": [55.2, 56.8, 58.1]
                },
                "latest_values": {
                    "close": 151.00,
                    "ema_20": 151.00,
                    "ema_50": 149.25,
                    "rsi_14": 58.1
                },
                "status": "ok"
            }
        }
