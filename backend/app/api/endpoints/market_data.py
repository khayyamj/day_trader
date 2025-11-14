"""Market data API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.market_data import FetchHistoricalRequest, FetchHistoricalResponse
from app.services.data.data_service import DataService
from app.services.data.twelve_data_client import InvalidSymbolError, TwelveDataError
from app.core.logging import get_logger
from datetime import date

logger = get_logger("market_data_api")

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.post("/fetch-historical", response_model=FetchHistoricalResponse)
async def fetch_historical_data(
    request: FetchHistoricalRequest,
    db: Session = Depends(get_db)
):
    """
    Fetch historical OHLCV data for a symbol.

    Args:
        request: Fetch parameters (symbol, dates, interval)
        db: Database session

    Returns:
        Fetch results with count of records stored

    Example request:
    ```json
    {
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "interval": "1day"
    }
    ```
    """
    logger.info(f"Fetch historical data request for {request.symbol}")

    try:
        # Parse dates if provided
        start = date.fromisoformat(request.start_date) if request.start_date else None
        end = date.fromisoformat(request.end_date) if request.end_date else None

        # Create service and fetch data
        service = DataService(db)
        result = service.fetch_historical_data(
            symbol=request.symbol,
            start_date=start,
            end_date=end
        )

        logger.info(f"Historical data fetch completed for {request.symbol}")
        return FetchHistoricalResponse(**result)

    except InvalidSymbolError as e:
        logger.warning(f"Invalid symbol: {request.symbol}")
        raise HTTPException(status_code=404, detail=f"Symbol not found: {request.symbol}")

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except TwelveDataError as e:
        logger.error(f"Twelve Data API error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Market data service unavailable: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching historical data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
