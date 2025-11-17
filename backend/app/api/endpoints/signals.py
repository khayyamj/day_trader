"""Signals API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.schemas.signal import (
    EvaluateSignalsRequest,
    EvaluateSignalsResponse,
    SignalListResponse,
    SignalResponse
)
from app.services.strategies.signal_generator import SignalGenerator
from app.models.signal import Signal
from app.models.stock import Stock
from app.core.logging import get_logger

logger = get_logger("signals_api")

router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("/evaluate", response_model=EvaluateSignalsResponse)
async def evaluate_signals(
    request: EvaluateSignalsRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate watchlist stocks or a specific stock and generate trading signals.

    This endpoint triggers the signal generation process for either:
    - All stocks in the watchlist (if symbol not provided)
    - A specific stock (if symbol provided)

    Args:
        request: Evaluation parameters (strategy_id, symbol, lookback_days)
        db: Database session

    Returns:
        Evaluation results with generated signals

    Example request (evaluate all):
    ```json
    {
        "strategy_id": 1,
        "lookback_days": 100
    }
    ```

    Example request (evaluate specific):
    ```json
    {
        "strategy_id": 1,
        "symbol": "AAPL",
        "lookback_days": 100
    }
    ```
    """
    logger.info(
        f"Signal evaluation request: strategy={request.strategy_id}, "
        f"symbol={request.symbol or 'ALL'}"
    )

    try:
        generator = SignalGenerator(db)

        if request.symbol:
            # Evaluate single stock
            result = generator.evaluate_single_stock(
                symbol=request.symbol,
                strategy_id=request.strategy_id,
                lookback_days=request.lookback_days
            )

            # Convert to list format
            if result['signal_generated']:
                signals = [result['signal']]
                stocks_evaluated = 1
                signals_generated = 1
            else:
                signals = []
                stocks_evaluated = 1
                signals_generated = 0

            # Get strategy name
            from app.models.strategy import Strategy
            strategy = db.query(Strategy).filter(
                Strategy.id == request.strategy_id
            ).first()

            response = EvaluateSignalsResponse(
                strategy_id=request.strategy_id,
                strategy_name=strategy.name if strategy else "Unknown",
                stocks_evaluated=stocks_evaluated,
                signals_generated=signals_generated,
                signals=signals,
                status="ok"
            )

        else:
            # Evaluate all watchlist stocks
            result = generator.evaluate_watchlist(
                strategy_id=request.strategy_id,
                lookback_days=request.lookback_days
            )

            response = EvaluateSignalsResponse(
                strategy_id=result['strategy_id'],
                strategy_name=result['strategy_name'],
                stocks_evaluated=result['stocks_evaluated'],
                signals_generated=result['signals_generated'],
                signals=result['signals'],
                status="ok"
            )

        logger.info(
            f"Evaluation complete: {response.stocks_evaluated} stocks, "
            f"{response.signals_generated} signals"
        )

        return response

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error evaluating signals: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate signals: {str(e)}"
        )


@router.get("/", response_model=SignalListResponse)
async def list_signals(
    strategy_id: Optional[int] = Query(None, description="Filter by strategy ID"),
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type (buy, sell, hold)"),
    executed: Optional[bool] = Query(None, description="Filter by executed status"),
    limit: int = Query(default=50, le=200, description="Number of signals to return"),
    db: Session = Depends(get_db)
):
    """
    List trading signals with optional filters.

    Args:
        strategy_id: Filter by strategy ID
        symbol: Filter by stock symbol
        signal_type: Filter by signal type
        executed: Filter by executed status
        limit: Maximum number of signals to return
        db: Database session

    Returns:
        List of signals
    """
    logger.info(f"List signals request: strategy={strategy_id}, symbol={symbol}")

    try:
        # Build query
        query = db.query(Signal).join(Stock)

        if strategy_id:
            query = query.filter(Signal.strategy_id == strategy_id)

        if symbol:
            query = query.filter(Stock.symbol == symbol.upper())

        if signal_type:
            query = query.filter(Signal.signal_type == signal_type.lower())

        if executed is not None:
            query = query.filter(Signal.executed == executed)

        # Order by most recent first
        query = query.order_by(Signal.signal_time.desc())

        # Limit results
        signals = query.limit(limit).all()

        # Convert to response format
        signal_responses = []
        for signal in signals:
            signal_responses.append(SignalResponse(
                signal_id=signal.id,
                symbol=signal.stock.symbol,
                signal_type=signal.signal_type,
                signal_time=signal.signal_time.isoformat(),
                trigger_reason=signal.reasons[0] if signal.reasons else "",
                indicator_values=signal.indicator_values or {},
                market_context=signal.market_context or {},
                executed=signal.executed
            ))

        logger.info(f"Returning {len(signal_responses)} signals")

        return SignalListResponse(
            signals=signal_responses,
            total=len(signal_responses),
            status="ok"
        )

    except Exception as e:
        logger.error(f"Error listing signals: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list signals: {str(e)}"
        )


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific signal by ID.

    Args:
        signal_id: Signal ID
        db: Database session

    Returns:
        Signal details
    """
    logger.info(f"Get signal request: {signal_id}")

    try:
        signal = db.query(Signal).filter(Signal.id == signal_id).first()

        if not signal:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        return SignalResponse(
            signal_id=signal.id,
            symbol=signal.stock.symbol,
            signal_type=signal.signal_type,
            signal_time=signal.signal_time.isoformat(),
            trigger_reason=signal.reasons[0] if signal.reasons else "",
            indicator_values=signal.indicator_values or {},
            market_context=signal.market_context or {},
            executed=signal.executed
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting signal: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get signal: {str(e)}"
        )
