"""Signal schemas for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class MarketContext(BaseModel):
    """Market context at signal generation time."""
    volatility: Optional[float] = Field(None, description="Price volatility (std dev of returns)")
    volume_vs_avg: Optional[float] = Field(None, description="Current volume vs average ratio")
    trend: Optional[str] = Field(None, description="Trend direction (uptrend, downtrend, sideways)")


class SignalCreate(BaseModel):
    """Schema for creating a signal."""
    strategy_id: int
    stock_id: int
    signal_type: str = Field(..., description="Signal type (buy, sell, hold)")
    signal_time: datetime
    trigger_reason: str
    indicator_values: Dict[str, float]
    market_context: Optional[MarketContext] = None


class SignalResponse(BaseModel):
    """Response schema for a single signal."""
    signal_id: int
    symbol: str
    signal_type: str
    signal_time: str
    trigger_reason: str
    indicator_values: Dict[str, float]
    market_context: Dict[str, any]
    executed: bool

    class Config:
        json_schema_extra = {
            "example": {
                "signal_id": 123,
                "symbol": "AAPL",
                "signal_type": "buy",
                "signal_time": "2025-11-17T16:05:00",
                "trigger_reason": "BUY: Bullish crossover detected (EMA20 crossed above EMA50) with RSI(45.2) < 70",
                "indicator_values": {
                    "ema_20": 150.25,
                    "ema_50": 149.80,
                    "rsi_14": 45.2,
                    "close": 151.00
                },
                "market_context": {
                    "volatility": 0.02,
                    "volume_vs_avg": 1.3,
                    "trend": "uptrend"
                },
                "executed": False
            }
        }


class EvaluateSignalsRequest(BaseModel):
    """Request to evaluate signals for watchlist or specific stock."""
    strategy_id: int = Field(..., description="Strategy ID to use for evaluation")
    symbol: Optional[str] = Field(None, description="Specific stock symbol (if not provided, evaluates all)")
    lookback_days: int = Field(default=100, description="Days of historical data to use")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": 1,
                "symbol": "AAPL",
                "lookback_days": 100
            }
        }


class EvaluateSignalsResponse(BaseModel):
    """Response from signal evaluation."""
    strategy_id: int
    strategy_name: str
    stocks_evaluated: int
    signals_generated: int
    signals: List[SignalResponse]
    status: str = "ok"

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": 1,
                "strategy_name": "MA Crossover + RSI",
                "stocks_evaluated": 10,
                "signals_generated": 2,
                "signals": [
                    {
                        "signal_id": 123,
                        "symbol": "AAPL",
                        "signal_type": "buy",
                        "signal_time": "2025-11-17T16:05:00",
                        "trigger_reason": "BUY: Bullish crossover detected",
                        "indicator_values": {"ema_20": 150.25, "ema_50": 149.80, "rsi_14": 45.2},
                        "market_context": {"volatility": 0.02, "volume_vs_avg": 1.3, "trend": "uptrend"},
                        "executed": False
                    }
                ],
                "status": "ok"
            }
        }


class SignalListResponse(BaseModel):
    """Response for listing signals."""
    signals: List[SignalResponse]
    total: int
    status: str = "ok"
