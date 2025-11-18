#!/usr/bin/env python
"""
Script to fetch historical data for validation backtest stocks.
"""
from datetime import date, timedelta

from app.db.session import SessionLocal
from app.services.data.data_service import DataService
from app.core.logging import get_logger

logger = get_logger("fetch_historical_data")

# 5 diverse stocks for testing
VALIDATION_STOCKS = ["AAPL", "MSFT", "GOOGL", "JPM", "XOM"]

# Date range: ~1.5 years to ensure we have enough data with warmup
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=550)  # ~1.5 years


def fetch_data_for_stocks():
    """Fetch historical data for all validation stocks."""
    db = SessionLocal()

    try:
        service = DataService(db)

        print(f"\nFetching historical data for {len(VALIDATION_STOCKS)} stocks")
        print(f"Date range: {START_DATE} to {END_DATE}")
        print(f"{'='*60}\n")

        for symbol in VALIDATION_STOCKS:
            try:
                print(f"Fetching {symbol}...")
                result = service.fetch_historical_data(
                    symbol=symbol,
                    start_date=START_DATE,
                    end_date=END_DATE
                )

                print(f"  ✓ Fetched {result['records_stored']} records for {symbol}")
                print(f"    Date range: {result['start_date']} to {result['end_date']}\n")

            except Exception as e:
                logger.error(f"Error fetching {symbol}: {str(e)}")
                print(f"  ✗ Error fetching {symbol}: {str(e)}\n")

        print(f"{'='*60}")
        print("Data fetching complete!")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    fetch_data_for_stocks()
