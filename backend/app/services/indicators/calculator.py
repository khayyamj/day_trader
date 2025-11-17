"""Technical indicator calculation engine using pandas-ta."""
from typing import Optional
import pandas as pd
import pandas_ta as ta

from app.core.logging import get_logger

logger = get_logger("indicator_calculator")


class IndicatorCalculator:
    """Calculator for technical indicators using pandas-ta library."""

    def __init__(self):
        """Initialize indicator calculator."""
        pass

    def calculate_ema(
        self,
        df: pd.DataFrame,
        period: int,
        column: str = "close"
    ) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            df: DataFrame with OHLCV data
            period: EMA period (e.g., 20, 50, 200)
            column: Column name to calculate EMA on (default: 'close')

        Returns:
            Series with EMA values

        Raises:
            ValueError: If DataFrame is empty or missing required column
        """
        if df.empty:
            raise ValueError("DataFrame is empty")

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")

        if len(df) < period:
            logger.warning(
                f"DataFrame has {len(df)} rows but EMA period is {period}. "
                "EMA will have NaN values."
            )

        logger.debug(f"Calculating EMA({period}) on column '{column}'")
        ema = ta.ema(df[column], length=period)

        return ema

    def calculate_rsi(
        self,
        df: pd.DataFrame,
        period: int = 14,
        column: str = "close"
    ) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            df: DataFrame with OHLCV data
            period: RSI period (default: 14)
            column: Column name to calculate RSI on (default: 'close')

        Returns:
            Series with RSI values (0-100)

        Raises:
            ValueError: If DataFrame is empty or missing required column
        """
        if df.empty:
            raise ValueError("DataFrame is empty")

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")

        if len(df) < period:
            logger.warning(
                f"DataFrame has {len(df)} rows but RSI period is {period}. "
                "RSI will have NaN values."
            )

        logger.debug(f"Calculating RSI({period}) on column '{column}'")
        rsi = ta.rsi(df[column], length=period)

        return rsi

    def calculate_all(
        self,
        df: pd.DataFrame,
        indicators: Optional[dict] = None
    ) -> pd.DataFrame:
        """
        Calculate multiple indicators and add as columns to DataFrame.

        Args:
            df: DataFrame with OHLCV data
            indicators: Dictionary of indicators to calculate with their parameters
                       Example: {
                           'ema_20': {'type': 'ema', 'period': 20},
                           'ema_50': {'type': 'ema', 'period': 50},
                           'rsi': {'type': 'rsi', 'period': 14}
                       }
                       If None, calculates default indicators (EMA 20/50, RSI 14)

        Returns:
            DataFrame with indicator columns added

        Raises:
            ValueError: If DataFrame is empty or invalid indicator type
        """
        if df.empty:
            raise ValueError("DataFrame is empty")

        # Create a copy to avoid modifying original
        result_df = df.copy()

        # Use default indicators if none provided
        if indicators is None:
            indicators = {
                'ema_20': {'type': 'ema', 'period': 20},
                'ema_50': {'type': 'ema', 'period': 50},
                'rsi_14': {'type': 'rsi', 'period': 14}
            }

        logger.info(f"Calculating {len(indicators)} indicators")

        for name, config in indicators.items():
            indicator_type = config.get('type')

            try:
                if indicator_type == 'ema':
                    period = config.get('period')
                    column = config.get('column', 'close')
                    result_df[name] = self.calculate_ema(result_df, period, column)
                    logger.debug(f"Added column '{name}': EMA({period})")

                elif indicator_type == 'rsi':
                    period = config.get('period', 14)
                    column = config.get('column', 'close')
                    result_df[name] = self.calculate_rsi(result_df, period, column)
                    logger.debug(f"Added column '{name}': RSI({period})")

                else:
                    logger.error(f"Unknown indicator type: {indicator_type}")
                    raise ValueError(f"Unsupported indicator type: {indicator_type}")

            except Exception as e:
                logger.error(f"Error calculating indicator '{name}': {str(e)}")
                raise

        logger.info(f"Successfully calculated all indicators. DataFrame shape: {result_df.shape}")
        return result_df
