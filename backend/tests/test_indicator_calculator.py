"""Tests for IndicatorCalculator."""
import pytest
import pandas as pd
import numpy as np
from app.services.indicators.calculator import IndicatorCalculator


@pytest.fixture
def calculator():
    """Create calculator instance."""
    return IndicatorCalculator()


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data."""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Generate realistic price data
    close_prices = 150 + np.cumsum(np.random.randn(100) * 2)

    return pd.DataFrame({
        'open': close_prices + np.random.randn(100) * 0.5,
        'high': close_prices + np.abs(np.random.randn(100) * 1),
        'low': close_prices - np.abs(np.random.randn(100) * 1),
        'close': close_prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)


class TestIndicatorCalculator:
    """Test IndicatorCalculator class."""

    def test_calculator_initialization(self, calculator):
        """Test calculator can be initialized."""
        assert calculator is not None

    def test_calculate_ema_basic(self, calculator, sample_ohlcv_data):
        """Test EMA calculation with valid data."""
        ema = calculator.calculate_ema(sample_ohlcv_data, period=20)

        assert len(ema) == len(sample_ohlcv_data)
        assert isinstance(ema, pd.Series)

        # First 19 values should be NaN (warm-up period)
        assert pd.isna(ema.iloc[:19]).all()

        # Later values should be numeric
        assert not pd.isna(ema.iloc[19:]).any()

    def test_calculate_ema_different_periods(self, calculator, sample_ohlcv_data):
        """Test EMA with different periods."""
        ema_10 = calculator.calculate_ema(sample_ohlcv_data, period=10)
        ema_50 = calculator.calculate_ema(sample_ohlcv_data, period=50)

        # EMA 10 should have values sooner
        assert not pd.isna(ema_10.iloc[9])

        # EMA 50 should have more NaN values initially
        assert pd.isna(ema_50.iloc[49])
        assert not pd.isna(ema_50.iloc[50])

    def test_calculate_ema_empty_dataframe(self, calculator):
        """Test EMA with empty DataFrame."""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="DataFrame is empty"):
            calculator.calculate_ema(empty_df, period=20)

    def test_calculate_ema_missing_column(self, calculator):
        """Test EMA with missing column."""
        df = pd.DataFrame({'open': [1, 2, 3]})

        with pytest.raises(ValueError, match="Column 'close' not found"):
            calculator.calculate_ema(df, period=2)

    def test_calculate_ema_insufficient_data(self, calculator):
        """Test EMA with insufficient data."""
        df = pd.DataFrame({'close': [100, 101, 102]})

        # Should not raise error but log warning
        ema = calculator.calculate_ema(df, period=10)

        # All values should be NaN due to insufficient data
        assert pd.isna(ema).all()

    def test_calculate_rsi_basic(self, calculator, sample_ohlcv_data):
        """Test RSI calculation with valid data."""
        rsi = calculator.calculate_rsi(sample_ohlcv_data, period=14)

        assert len(rsi) == len(sample_ohlcv_data)
        assert isinstance(rsi, pd.Series)

        # RSI values should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_calculate_rsi_custom_period(self, calculator, sample_ohlcv_data):
        """Test RSI with custom period."""
        rsi_7 = calculator.calculate_rsi(sample_ohlcv_data, period=7)
        rsi_21 = calculator.calculate_rsi(sample_ohlcv_data, period=21)

        # Both should have valid values
        assert not rsi_7.dropna().empty
        assert not rsi_21.dropna().empty

    def test_calculate_rsi_empty_dataframe(self, calculator):
        """Test RSI with empty DataFrame."""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="DataFrame is empty"):
            calculator.calculate_rsi(empty_df, period=14)

    def test_calculate_rsi_missing_column(self, calculator):
        """Test RSI with missing column."""
        df = pd.DataFrame({'open': [1, 2, 3]})

        with pytest.raises(ValueError, match="Column 'close' not found"):
            calculator.calculate_rsi(df, period=14)

    def test_calculate_all_default_indicators(self, calculator, sample_ohlcv_data):
        """Test calculate_all with default indicators."""
        result = calculator.calculate_all(sample_ohlcv_data)

        # Should have original columns plus indicators
        assert 'ema_20' in result.columns
        assert 'ema_50' in result.columns
        assert 'rsi_14' in result.columns

        # Original columns should still be there
        assert 'close' in result.columns
        assert 'volume' in result.columns

    def test_calculate_all_custom_indicators(self, calculator, sample_ohlcv_data):
        """Test calculate_all with custom indicators."""
        indicators = {
            'ema_12': {'type': 'ema', 'period': 12},
            'ema_26': {'type': 'ema', 'period': 26},
            'rsi_7': {'type': 'rsi', 'period': 7}
        }

        result = calculator.calculate_all(sample_ohlcv_data, indicators)

        assert 'ema_12' in result.columns
        assert 'ema_26' in result.columns
        assert 'rsi_7' in result.columns

    def test_calculate_all_invalid_indicator_type(self, calculator, sample_ohlcv_data):
        """Test calculate_all with invalid indicator type."""
        indicators = {
            'invalid': {'type': 'macd', 'period': 12}
        }

        with pytest.raises(ValueError, match="Unsupported indicator type"):
            calculator.calculate_all(sample_ohlcv_data, indicators)

    def test_calculate_all_empty_dataframe(self, calculator):
        """Test calculate_all with empty DataFrame."""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="DataFrame is empty"):
            calculator.calculate_all(empty_df)

    def test_ema_values_are_smoothed(self, calculator):
        """Test that EMA values are properly smoothed."""
        # Create data with a spike
        data = pd.DataFrame({
            'close': [100, 100, 100, 150, 100, 100, 100]  # Spike in middle
        })

        ema = calculator.calculate_ema(data, period=3)

        # EMA should smooth the spike
        valid_ema = ema.dropna()

        # The spike should be dampened in EMA
        # (EMA at spike should be less than actual spike value)
        if len(valid_ema) > 0:
            assert valid_ema.iloc[1] < 150  # EMA at spike should be smoothed

    def test_rsi_extreme_values(self, calculator):
        """Test RSI with extreme price movements."""
        # All rising prices (should give high RSI)
        rising = pd.DataFrame({
            'close': list(range(100, 200))
        })

        rsi_rising = calculator.calculate_rsi(rising, period=14)

        # RSI should be high (>50) for consistently rising prices
        valid_rsi = rsi_rising.dropna()
        if len(valid_rsi) > 0:
            assert valid_rsi.mean() > 50

    def test_calculate_all_preserves_index(self, calculator, sample_ohlcv_data):
        """Test that calculate_all preserves DataFrame index."""
        result = calculator.calculate_all(sample_ohlcv_data)

        assert result.index.equals(sample_ohlcv_data.index)

    def test_calculate_all_does_not_modify_original(self, calculator, sample_ohlcv_data):
        """Test that calculate_all doesn't modify original DataFrame."""
        original_columns = set(sample_ohlcv_data.columns)

        calculator.calculate_all(sample_ohlcv_data)

        # Original should be unchanged
        assert set(sample_ohlcv_data.columns) == original_columns
