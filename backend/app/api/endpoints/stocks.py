"""Stock watchlist API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.models.stock import Stock
from app.schemas.stock import StockCreate, StockResponse, StockList
from app.services.data.twelve_data_client import TwelveDataClient, InvalidSymbolError, TwelveDataError
from app.services.data.data_service import DataService
from app.core.logging import get_logger

logger = get_logger("stocks_api")

router = APIRouter(prefix="/stocks", tags=["stocks"])

# Watchlist configuration
MAX_WATCHLIST_STOCKS = 10


def fetch_historical_data_background(symbol: str, db: Session):
    """
    Background task to fetch historical data for a newly added stock.

    Args:
        symbol: Stock symbol
        db: Database session
    """
    try:
        logger.info(f"Starting background data fetch for {symbol}")
        service = DataService(db)
        result = service.fetch_historical_data(symbol=symbol)
        logger.info(f"Background fetch completed for {symbol}: {result['records_stored']} records")
    except Exception as e:
        logger.error(f"Background fetch failed for {symbol}: {e}")


@router.get("/", response_model=StockList)
async def list_stocks(db: Session = Depends(get_db)):
    """
    Get all stocks in the watchlist.

    Returns:
        List of all stocks with metadata
    """
    logger.info("Listing all watchlist stocks")
    stocks = db.query(Stock).all()

    return StockList(
        stocks=[StockResponse.model_validate(stock) for stock in stocks],
        total=len(stocks)
    )


@router.post("/", response_model=StockResponse, status_code=201)
async def add_stock(
    stock_data: StockCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Add a stock to the watchlist.

    Args:
        stock_data: Stock information
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Created stock record

    Raises:
        HTTPException: If watchlist limit exceeded, symbol invalid, or already exists

    After adding the stock, triggers a background task to fetch 1 year of historical data.
    """
    symbol_upper = stock_data.symbol.upper()
    logger.info(f"Adding stock to watchlist: {symbol_upper}")

    # Check watchlist limit
    current_count = db.query(Stock).count()
    if current_count >= MAX_WATCHLIST_STOCKS:
        logger.warning(f"Watchlist limit reached: {current_count}/{MAX_WATCHLIST_STOCKS}")
        raise HTTPException(
            status_code=400,
            detail=f"Watchlist limit reached. Maximum {MAX_WATCHLIST_STOCKS} stocks allowed."
        )

    # Check if stock already exists
    existing = db.query(Stock).filter(Stock.symbol == symbol_upper).first()
    if existing:
        logger.warning(f"Stock {symbol_upper} already in watchlist")
        raise HTTPException(
            status_code=409,
            detail=f"Stock {symbol_upper} already in watchlist"
        )

    # Validate symbol with Twelve Data API
    try:
        client = TwelveDataClient()
        stock_info = client.get_stock_info(symbol_upper)

        # Create stock record
        stock = Stock(
            symbol=symbol_upper,
            name=stock_info.get("name") or stock_data.name,
            exchange=stock_info.get("exchange") or stock_data.exchange
        )

        db.add(stock)
        db.commit()
        db.refresh(stock)

        logger.info(f"Stock {symbol_upper} added to watchlist")

        # Trigger background data fetch
        background_tasks.add_task(fetch_historical_data_background, symbol_upper, db)
        logger.info(f"Background data fetch queued for {symbol_upper}")

        return StockResponse.model_validate(stock)

    except InvalidSymbolError:
        logger.error(f"Invalid symbol: {symbol_upper}")
        raise HTTPException(
            status_code=404,
            detail=f"Symbol '{symbol_upper}' not found on exchange"
        )

    except TwelveDataError as e:
        logger.error(f"Twelve Data API error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Market data service unavailable. Please try again later."
        )


@router.delete("/{symbol}", status_code=204)
async def remove_stock(symbol: str, db: Session = Depends(get_db)):
    """
    Remove a stock from the watchlist.

    Args:
        symbol: Stock symbol to remove
        db: Database session

    Raises:
        HTTPException: If stock not found
    """
    symbol_upper = symbol.upper()
    logger.info(f"Removing stock from watchlist: {symbol_upper}")

    stock = db.query(Stock).filter(Stock.symbol == symbol_upper).first()

    if not stock:
        logger.warning(f"Stock {symbol_upper} not found in watchlist")
        raise HTTPException(
            status_code=404,
            detail=f"Stock {symbol_upper} not in watchlist"
        )

    db.delete(stock)
    db.commit()

    logger.info(f"Stock {symbol_upper} removed from watchlist")
    return None


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(symbol: str, db: Session = Depends(get_db)):
    """
    Get details for a specific stock in the watchlist.

    Args:
        symbol: Stock symbol
        db: Database session

    Returns:
        Stock details
    """
    symbol_upper = symbol.upper()
    stock = db.query(Stock).filter(Stock.symbol == symbol_upper).first()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"Stock {symbol_upper} not in watchlist"
        )

    return StockResponse.model_validate(stock)
