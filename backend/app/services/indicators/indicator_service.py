"""Indicator service for managing technical indicator calculations and storage."""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.services.indicators.calculator import IndicatorCalculator
from app.models.stock import Stock
from app.models.stock_data import StockData
from app.models.indicator import Indicator
from app.core.logging import get_logger

logger = get_logger("indicator_service")


class IndicatorService:
    """Service for calculating and managing technical indicators."""

    def __init__(self, db: Session):
        """
        Initialize indicator service.

        Args:
            db: Database session
        """
        self.db = db
        self.calculator = IndicatorCalculator()

    def get_indicators_for_stock(
        self,
        symbol: str,
        indicators: Optional[Dict] = None,
        lookback_days: int = 100,
        save_to_db: bool = False
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data and calculate indicators for a stock.

        Args:
            symbol: Stock symbol
            indicators: Dictionary of indicators to calculate (see IndicatorCalculator.calculate_all)
            lookback_days: Number of days to look back for data
            save_to_db: Whether to save calculated indicators to database

        Returns:
            DataFrame with OHLCV data and calculated indicators

        Raises:
            ValueError: If stock not found or insufficient data
        """
        logger.info(f"Calculating indicators for {symbol} (lookback: {lookback_days} days)")

        # Get stock from database
        stock = self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            logger.error(f"Stock {symbol} not found in database")
            raise ValueError(f"Stock {symbol} not found")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Fetch OHLCV data
        stock_data = self.db.query(StockData).filter(
            and_(
                StockData.stock_id == stock.id,
                StockData.timestamp >= start_date,
                StockData.timestamp <= end_date
            )
        ).order_by(StockData.timestamp).all()

        if not stock_data:
            logger.error(f"No data found for {symbol}")
            raise ValueError(f"No OHLCV data found for {symbol}")

        logger.info(f"Found {len(stock_data)} data points for {symbol}")

        # Convert to DataFrame
        data = []
        for sd in stock_data:
            data.append({
                'timestamp': sd.timestamp,
                'open': float(sd.open_price),
                'high': float(sd.high_price),
                'low': float(sd.low_price),
                'close': float(sd.close_price),
                'volume': int(sd.volume)
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)

        # Calculate indicators
        df_with_indicators = self.calculator.calculate_all(df, indicators)

        # Check for warm-up period
        warm_up_status = self._check_warm_up(df_with_indicators, indicators)
        logger.info(f"Warm-up status: {warm_up_status}")

        # Optionally save to database
        if save_to_db:
            self._save_indicators(stock.id, df_with_indicators, indicators)

        return df_with_indicators

    def _check_warm_up(
        self,
        df: pd.DataFrame,
        indicators: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """
        Check if there's enough data for reliable indicator calculations.

        Args:
            df: DataFrame with indicators
            indicators: Dictionary of indicators that were calculated

        Returns:
            Dictionary with warm-up status for each indicator
        """
        if indicators is None:
            indicators = {
                'ema_20': {'type': 'ema', 'period': 20},
                'ema_50': {'type': 'ema', 'period': 50},
                'rsi_14': {'type': 'rsi', 'period': 14}
            }

        warm_up_status = {}
        total_bars = len(df)

        for name, config in indicators.items():
            period = config.get('period', 14)
            # Typically need at least 2-3x the period for reliable indicators
            min_bars = period * 2

            is_ready = total_bars >= min_bars
            warm_up_status[name] = is_ready

            if not is_ready:
                logger.warning(
                    f"Indicator {name} may not be reliable: "
                    f"only {total_bars} bars available, recommend {min_bars}+"
                )

        # Overall warm-up check (100+ bars is generally safe for most strategies)
        warm_up_status['overall'] = total_bars >= 100

        return warm_up_status

    def _save_indicators(
        self,
        stock_id: int,
        df: pd.DataFrame,
        indicators: Optional[Dict] = None
    ) -> int:
        """
        Save calculated indicators to database (recent 90 days only).

        Args:
            stock_id: Stock ID
            df: DataFrame with indicators
            indicators: Dictionary of indicators to save

        Returns:
            Number of indicator records saved
        """
        if indicators is None:
            indicators = {
                'ema_20': {'type': 'ema', 'period': 20},
                'ema_50': {'type': 'ema', 'period': 50},
                'rsi_14': {'type': 'rsi', 'period': 14}
            }

        # Only save last 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        df_recent = df[df.index >= cutoff_date]

        saved_count = 0

        try:
            for indicator_name in indicators.keys():
                if indicator_name not in df_recent.columns:
                    continue

                for timestamp, row in df_recent.iterrows():
                    value = row[indicator_name]

                    # Skip NaN values
                    if pd.isna(value):
                        continue

                    # Check if indicator already exists
                    existing = self.db.query(Indicator).filter(
                        and_(
                            Indicator.stock_id == stock_id,
                            Indicator.indicator_name == indicator_name,
                            Indicator.timestamp == timestamp
                        )
                    ).first()

                    if existing:
                        # Update existing
                        existing.value = float(value)
                    else:
                        # Create new
                        indicator = Indicator(
                            stock_id=stock_id,
                            indicator_name=indicator_name,
                            timestamp=timestamp,
                            value=float(value),
                            meta=indicators[indicator_name]
                        )
                        self.db.add(indicator)
                        saved_count += 1

            self.db.commit()
            logger.info(f"Saved {saved_count} new indicator records")

        except Exception as e:
            logger.error(f"Error saving indicators: {str(e)}")
            self.db.rollback()
            raise

        return saved_count

    def has_sufficient_data(
        self,
        symbol: str,
        min_bars: int = 100
    ) -> bool:
        """
        Check if a stock has sufficient data for indicator calculation.

        Args:
            symbol: Stock symbol
            min_bars: Minimum number of bars required

        Returns:
            True if sufficient data available
        """
        stock = self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            return False

        bar_count = self.db.query(StockData).filter(
            StockData.stock_id == stock.id
        ).count()

        has_sufficient = bar_count >= min_bars
        logger.debug(f"{symbol} has {bar_count} bars (required: {min_bars}): {has_sufficient}")

        return has_sufficient
