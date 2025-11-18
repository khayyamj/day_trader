"""Strategies API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.api.deps import get_db
from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    StrategyStatusResponse,
    StrategyActivateResponse,
    StrategyPauseResponse
)
from app.services.strategies.strategy_service import StrategyService
from app.models.strategy import Strategy
from app.core.logging import get_logger

logger = get_logger("strategies_api")

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.post("/", response_model=StrategyResponse, status_code=201)
async def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new trading strategy.

    Args:
        strategy: Strategy creation parameters
        db: Database session

    Returns:
        Created strategy

    Example request:
    ```json
    {
        "name": "MA Crossover + RSI",
        "description": "Moving average crossover with RSI confirmation",
        "parameters": {
            "ema_fast": 20,
            "ema_slow": 50,
            "rsi_period": 14,
            "rsi_threshold": 70
        }
    }
    ```
    """
    logger.info(f"Create strategy request: {strategy.name}")

    try:
        # Check if strategy with same name exists
        existing = db.query(Strategy).filter(
            Strategy.name == strategy.name
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Strategy with name '{strategy.name}' already exists"
            )

        # Create strategy
        new_strategy = Strategy(
            name=strategy.name,
            description=strategy.description,
            parameters=strategy.parameters,
            active=False,  # Start inactive
            status="paused",  # Start in paused state
            warm_up_bars_remaining=100  # Default warm-up requirement
        )

        db.add(new_strategy)
        db.commit()
        db.refresh(new_strategy)

        logger.info(f"Strategy created: {new_strategy.id}")

        # Parse parameters if JSON string
        params = new_strategy.parameters
        if isinstance(params, str):
            params = json.loads(params)

        return StrategyResponse(
            strategy_id=new_strategy.id,
            name=new_strategy.name,
            description=new_strategy.description,
            parameters=params,
            status=new_strategy.status,
            active=new_strategy.active,
            warm_up_bars_remaining=new_strategy.warm_up_bars_remaining
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error creating strategy: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create strategy: {str(e)}"
        )


@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    db: Session = Depends(get_db)
):
    """
    List all trading strategies.

    Args:
        db: Database session

    Returns:
        List of strategies with their current status
    """
    logger.info("List strategies request")

    try:
        service = StrategyService(db)
        strategies_data = service.list_strategies()

        strategy_responses = []
        for s in strategies_data:
            # Parse parameters if JSON string
            params = s['parameters']
            if isinstance(params, str):
                params = json.loads(params)

            strategy_responses.append(
                StrategyResponse(
                    strategy_id=s['strategy_id'],
                    name=s['name'],
                    description=s['description'],
                    parameters=params,
                    status=s['status'],
                    active=s['active'],
                    warm_up_bars_remaining=s['warm_up_bars_remaining']
                )
            )

        logger.info(f"Returning {len(strategy_responses)} strategies")

        return StrategyListResponse(
            strategies=strategy_responses,
            total=len(strategy_responses),
            status="ok"
        )

    except Exception as e:
        logger.error(f"Error listing strategies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list strategies: {str(e)}"
        )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific strategy by ID.

    Args:
        strategy_id: Strategy ID
        db: Database session

    Returns:
        Strategy details
    """
    logger.info(f"Get strategy request: {strategy_id}")

    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy {strategy_id} not found"
            )

        # Parse parameters if JSON string
        params = strategy.parameters
        if isinstance(params, str):
            params = json.loads(params)

        return StrategyResponse(
            strategy_id=strategy.id,
            name=strategy.name,
            description=strategy.description,
            parameters=params,
            status=strategy.status,
            active=strategy.active,
            warm_up_bars_remaining=strategy.warm_up_bars_remaining
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting strategy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get strategy: {str(e)}"
        )


@router.put("/{strategy_id}/parameters", response_model=StrategyResponse)
async def update_strategy_parameters(
    strategy_id: int,
    update: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update strategy parameters.

    Args:
        strategy_id: Strategy ID
        update: Updated parameters
        db: Database session

    Returns:
        Updated strategy

    Example request:
    ```json
    {
        "parameters": {
            "ema_fast": 12,
            "ema_slow": 26,
            "rsi_period": 14,
            "rsi_threshold": 75
        }
    }
    ```
    """
    logger.info(f"Update strategy parameters: {strategy_id}")

    try:
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy {strategy_id} not found"
            )

        # Update parameters
        strategy.parameters = update.parameters

        db.commit()
        db.refresh(strategy)

        logger.info(f"Strategy {strategy_id} parameters updated")

        return StrategyResponse(
            strategy_id=strategy.id,
            name=strategy.name,
            description=strategy.description,
            parameters=strategy.parameters,
            status=strategy.status,
            active=strategy.active,
            warm_up_bars_remaining=strategy.warm_up_bars_remaining
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error updating strategy: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update strategy: {str(e)}"
        )


@router.post("/{strategy_id}/activate", response_model=StrategyActivateResponse)
async def activate_strategy(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """
    Activate a strategy.

    This will check if the strategy has sufficient warm-up data and
    set the status accordingly (active if warm-up complete, warming if not).

    Args:
        strategy_id: Strategy ID
        db: Database session

    Returns:
        Activation result with warm-up status
    """
    logger.info(f"Activate strategy request: {strategy_id}")

    try:
        service = StrategyService(db)
        result = service.activate_strategy(strategy_id)

        return StrategyActivateResponse(**result)

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error activating strategy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to activate strategy: {str(e)}"
        )


@router.post("/{strategy_id}/pause", response_model=StrategyPauseResponse)
async def pause_strategy(
    strategy_id: int,
    reason: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """
    Pause a strategy.

    Args:
        strategy_id: Strategy ID
        reason: Optional reason for pausing
        db: Database session

    Returns:
        Pause result

    Example request:
    ```json
    {
        "reason": "Market volatility too high"
    }
    ```
    """
    logger.info(f"Pause strategy request: {strategy_id}")

    try:
        service = StrategyService(db)
        result = service.pause_strategy(strategy_id, reason)

        return StrategyPauseResponse(**result)

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error pausing strategy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause strategy: {str(e)}"
        )


@router.get("/{strategy_id}/status", response_model=StrategyStatusResponse)
async def get_strategy_status(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed status of a strategy including warm-up information.

    Args:
        strategy_id: Strategy ID
        db: Database session

    Returns:
        Strategy status details
    """
    logger.info(f"Get strategy status: {strategy_id}")

    try:
        service = StrategyService(db)
        status = service.get_strategy_status(strategy_id)

        return StrategyStatusResponse(**status)

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error getting strategy status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get strategy status: {str(e)}"
        )
