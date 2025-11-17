"""Strategy schemas for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, Dict


class StrategyCreate(BaseModel):
    """Schema for creating a strategy."""
    name: str = Field(..., description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    parameters: Dict = Field(..., description="Strategy parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "MA Crossover + RSI",
                "description": "Moving average crossover with RSI confirmation",
                "parameters": {
                    "ema_fast": 20,
                    "ema_slow": 50,
                    "rsi_period": 14,
                    "rsi_threshold": 70
                }
            }
        }


class StrategyUpdate(BaseModel):
    """Schema for updating strategy parameters."""
    parameters: Dict = Field(..., description="Updated strategy parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "parameters": {
                    "ema_fast": 12,
                    "ema_slow": 26,
                    "rsi_period": 14,
                    "rsi_threshold": 75
                }
            }
        }


class StrategyResponse(BaseModel):
    """Response schema for a strategy."""
    strategy_id: int
    name: str
    description: Optional[str]
    parameters: Dict
    status: str
    active: bool
    warm_up_bars_remaining: int

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": 1,
                "name": "MA Crossover + RSI",
                "description": "Moving average crossover with RSI confirmation",
                "parameters": {
                    "ema_fast": 20,
                    "ema_slow": 50,
                    "rsi_period": 14,
                    "rsi_threshold": 70
                },
                "status": "active",
                "active": True,
                "warm_up_bars_remaining": 0
            }
        }


class StrategyListResponse(BaseModel):
    """Response for listing strategies."""
    strategies: list[StrategyResponse]
    total: int
    status: str = "ok"


class StrategyStatusResponse(BaseModel):
    """Response for strategy status check."""
    strategy_id: int
    name: str
    status: str
    active: bool
    warm_up_bars_remaining: int
    parameters: Dict


class StrategyActivateResponse(BaseModel):
    """Response for strategy activation."""
    strategy_id: int
    name: str
    status: str
    warm_up_complete: bool
    warm_up_bars_remaining: int
    message: str


class StrategyPauseResponse(BaseModel):
    """Response for strategy pause."""
    strategy_id: int
    name: str
    previous_status: str
    current_status: str
    reason: Optional[str]
    message: str
