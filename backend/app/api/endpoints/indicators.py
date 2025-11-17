"""Indicator API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.indicator import IndicatorRequest, IndicatorResponse, WarmUpStatus
from app.services.indicators.indicator_service import IndicatorService
from app.core.logging import get_logger

logger = get_logger("indicators_api")

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.post("/calculate", response_model=IndicatorResponse)
async def calculate_indicators(
    request: IndicatorRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate technical indicators for a stock.

    Args:
        request: Indicator calculation parameters
        db: Database session

    Returns:
        Calculated indicators with warm-up status

    Example request:
    ```json
    {
        "symbol": "AAPL",
        "indicators": {
            "ema_20": {"type": "ema", "period": 20},
            "ema_50": {"type": "ema", "period": 50},
            "rsi_14": {"type": "rsi", "period": 14}
        },
        "lookback_days": 100,
        "save_to_db": false
    }
    ```
    """
    logger.info(f"Calculate indicators request for {request.symbol}")

    try:
        service = IndicatorService(db)

        # Convert IndicatorConfig models to dict format
        indicators_dict = None
        if request.indicators:
            indicators_dict = {}
            for name, config in request.indicators.items():
                indicators_dict[name] = {
                    'type': config.type,
                    'period': config.period,
                    'column': config.column
                }

        # Calculate indicators
        df = service.get_indicators_for_stock(
            symbol=request.symbol,
            indicators=indicators_dict,
            lookback_days=request.lookback_days,
            save_to_db=request.save_to_db
        )

        # Build response
        indicator_columns = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]

        # Extract indicator values
        indicators_data = {}
        latest_values = {}

        for col in indicator_columns:
            # Get non-NaN values
            values = df[col].dropna().tolist()
            indicators_data[col] = values

            # Get latest value
            if len(values) > 0:
                latest_values[col] = float(values[-1])

        # Add latest close price
        if 'close' in df.columns:
            close_values = df['close'].dropna().tolist()
            if len(close_values) > 0:
                latest_values['close'] = float(close_values[-1])

        # Check warm-up status
        warm_up = service._check_warm_up(df, indicators_dict)

        response = IndicatorResponse(
            symbol=request.symbol,
            total_bars=len(df),
            date_range={
                "start": str(df.index[0]),
                "end": str(df.index[-1])
            },
            warm_up_status=WarmUpStatus(
                overall=warm_up['overall'],
                indicators={k: v for k, v in warm_up.items() if k != 'overall'}
            ),
            indicators=indicators_data,
            latest_values=latest_values,
            status="ok"
        )

        logger.info(f"Successfully calculated indicators for {request.symbol}")
        return response

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate indicators: {str(e)}")


@router.get("/{symbol}/status")
async def check_indicator_status(
    symbol: str,
    min_bars: int = Query(default=100, description="Minimum number of bars required"),
    db: Session = Depends(get_db)
):
    """
    Check if a stock has sufficient data for indicator calculation.

    Args:
        symbol: Stock symbol
        min_bars: Minimum number of bars required
        db: Database session

    Returns:
        Status indicating if sufficient data is available
    """
    logger.info(f"Checking indicator status for {symbol}")

    try:
        service = IndicatorService(db)
        has_data = service.has_sufficient_data(symbol, min_bars)

        return {
            "symbol": symbol,
            "has_sufficient_data": has_data,
            "min_bars_required": min_bars,
            "status": "ok"
        }

    except Exception as e:
        logger.error(f"Error checking indicator status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
