"""Backtest schemas for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date
from decimal import Decimal


class BacktestRequest(BaseModel):
    """Request to run a backtest."""
    strategy_id: int = Field(..., description="Strategy ID to backtest")
    symbol: str = Field(..., description="Stock symbol to test on")
    start_date: str = Field(..., description="Backtest start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Backtest end date (YYYY-MM-DD)")
    initial_capital: float = Field(default=100000.0, description="Starting capital")
    slippage_pct: float = Field(default=0.001, description="Slippage percentage (0.001 = 0.1%)")
    commission_per_trade: float = Field(default=1.0, description="Commission per trade in dollars")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": 1,
                "symbol": "AAPL",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 100000.0,
                "slippage_pct": 0.001,
                "commission_per_trade": 1.0
            }
        }


class BacktestMetrics(BaseModel):
    """Performance metrics from a backtest."""
    total_return_pct: float = Field(..., description="Total return percentage")
    annualized_return_pct: Optional[float] = Field(None, description="Annualized return percentage")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio (risk-adjusted return)")
    max_drawdown_pct: Optional[float] = Field(None, description="Maximum drawdown percentage")
    win_rate_pct: Optional[float] = Field(None, description="Percentage of winning trades")
    profit_factor: Optional[float] = Field(None, description="Gross profit / gross loss")
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    avg_win: Optional[float] = Field(None, description="Average winning trade P&L")
    avg_loss: Optional[float] = Field(None, description="Average losing trade P&L")
    largest_win: Optional[float] = Field(None, description="Largest winning trade")
    largest_loss: Optional[float] = Field(None, description="Largest losing trade")


class BacktestTradeSchema(BaseModel):
    """Individual trade from a backtest."""
    trade_number: int
    entry_date: date
    entry_price: float
    exit_date: Optional[date]
    exit_price: Optional[float]
    shares: int
    entry_signal: str
    exit_signal: Optional[str]
    gross_pnl: Optional[float]
    net_pnl: Optional[float]
    return_pct: Optional[float]
    holding_period_days: Optional[int]
    is_winner: Optional[bool]


class EquityCurvePoint(BaseModel):
    """Single point on the equity curve."""
    date: date
    equity: float
    cash: float
    position_value: float


class BacktestResponse(BaseModel):
    """Response from a backtest run."""
    backtest_id: int
    symbol: str
    strategy_name: str
    start_date: date
    end_date: date
    initial_capital: float
    final_equity: float
    metrics: BacktestMetrics
    execution_time_seconds: Optional[float]
    bars_processed: int
    status: str = "ok"

    class Config:
        json_schema_extra = {
            "example": {
                "backtest_id": 1,
                "symbol": "AAPL",
                "strategy_name": "MA Crossover + RSI",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "initial_capital": 100000.0,
                "final_equity": 115000.0,
                "metrics": {
                    "total_return_pct": 15.0,
                    "annualized_return_pct": 15.2,
                    "sharpe_ratio": 1.5,
                    "max_drawdown_pct": 12.5,
                    "win_rate_pct": 55.0,
                    "profit_factor": 1.8,
                    "total_trades": 20,
                    "winning_trades": 11,
                    "losing_trades": 9,
                    "avg_win": 2500.0,
                    "avg_loss": -1200.0,
                    "largest_win": 5000.0,
                    "largest_loss": -3000.0
                },
                "execution_time_seconds": 2.5,
                "bars_processed": 252,
                "status": "ok"
            }
        }


class BacktestListItem(BaseModel):
    """Summary item for backtest list."""
    backtest_id: int
    symbol: str
    strategy_name: str
    start_date: date
    end_date: date
    total_return_pct: float
    sharpe_ratio: Optional[float]
    max_drawdown_pct: Optional[float]
    total_trades: int
    created_at: str


class BacktestListResponse(BaseModel):
    """Response for listing backtests."""
    backtests: List[BacktestListItem]
    total: int
    status: str = "ok"


class BacktestTradesResponse(BaseModel):
    """Response for backtest trades."""
    backtest_id: int
    symbol: str
    trades: List[BacktestTradeSchema]
    total_trades: int
    status: str = "ok"


class BacktestEquityCurveResponse(BaseModel):
    """Response for backtest equity curve."""
    backtest_id: int
    symbol: str
    equity_curve: List[EquityCurvePoint]
    total_points: int
    status: str = "ok"
