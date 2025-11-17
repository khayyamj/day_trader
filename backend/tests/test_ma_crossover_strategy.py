"""Tests for MACrossoverRSIStrategy."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.services.strategies.ma_crossover_rsi import MACrossoverRSIStrategy
from app.services.strategies.base_strategy import SignalType


@pytest.fixture
def strategy():
    """Create strategy instance with default parameters."""
    return MACrossoverRSIStrategy()


@pytest.fixture
def custom_strategy():
    """Create strategy with custom parameters."""
    return MACrossoverRSIStrategy(parameters={
        'ema_fast': 12,
        'ema_slow': 26,
        'rsi_period': 14,
        'rsi_threshold': 75
    })


@pytest.fixture
def sample_data_with_indicators():
    """Create sample data with indicators already calculated."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    np.random.seed(42)
    close_prices = 150 + np.cumsum(np.random.randn(100) * 2)

    df = pd.DataFrame({
        'close': close_prices,
        'open': close_prices + np.random.randn(100) * 0.5,
        'high': close_prices + np.abs(np.random.randn(100) * 1),
        'low': close_prices - np.abs(np.random.randn(100) * 1),
        'volume': np.random.randint(1000000, 10000000, 100),
        'ema_20': close_prices + np.random.randn(100) * 0.3,
        'ema_50': close_prices + np.random.randn(100) * 0.5,
        'rsi_14': np.random.uniform(30, 70, 100)
    }, index=dates)

    return df


class TestMACrossoverRSIStrategy:
    """Test MACrossoverRSIStrategy class."""

    def test_strategy_initialization_default(self, strategy):
        """Test strategy initialization with defaults."""
        assert strategy.name == "MA Crossover + RSI"
        assert strategy.ema_fast == 20
        assert strategy.ema_slow == 50
        assert strategy.rsi_period == 14
        assert strategy.rsi_threshold == 70

    def test_strategy_initialization_custom(self, custom_strategy):
        """Test strategy initialization with custom parameters."""
        assert custom_strategy.ema_fast == 12
        assert custom_strategy.ema_slow == 26
        assert custom_strategy.rsi_threshold == 75

    def test_validate_parameters_valid(self, strategy):
        """Test parameter validation with valid parameters."""
        params = {
            'ema_fast': 10,
            'ema_slow': 20,
            'rsi_period': 14,
            'rsi_threshold': 70
        }

        assert strategy.validate_parameters(params) is True

    def test_validate_parameters_missing_required(self, strategy):
        """Test parameter validation with missing parameters."""
        params = {'ema_fast': 10}

        with pytest.raises(ValueError, match="Missing required parameters"):
            strategy.validate_parameters(params)

    def test_validate_parameters_invalid_fast_slow(self, strategy):
        """Test that fast must be less than slow."""
        params = {
            'ema_fast': 50,
            'ema_slow': 20,
            'rsi_period': 14,
            'rsi_threshold': 70
        }

        with pytest.raises(ValueError, match="ema_fast must be less than ema_slow"):
            strategy.validate_parameters(params)

    def test_validate_parameters_invalid_rsi_threshold(self, strategy):
        """Test invalid RSI threshold."""
        params = {
            'ema_fast': 20,
            'ema_slow': 50,
            'rsi_period': 14,
            'rsi_threshold': 150  # Invalid (>100)
        }

        with pytest.raises(ValueError, match="rsi_threshold must be between 0 and 100"):
            strategy.validate_parameters(params)

    def test_get_required_indicators(self, strategy):
        """Test getting required indicators."""
        indicators = strategy.get_required_indicators()

        assert 'ema_20' in indicators
        assert 'ema_50' in indicators
        assert 'rsi_14' in indicators

        assert indicators['ema_20']['type'] == 'ema'
        assert indicators['ema_20']['period'] == 20

    def test_check_data_sufficiency_valid(self, strategy, sample_data_with_indicators):
        """Test data sufficiency check with valid data."""
        is_sufficient, message = strategy.check_data_sufficiency(sample_data_with_indicators)

        assert is_sufficient is True
        assert message == "Data is sufficient"

    def test_check_data_sufficiency_empty(self, strategy):
        """Test data sufficiency with empty DataFrame."""
        empty_df = pd.DataFrame()

        is_sufficient, message = strategy.check_data_sufficiency(empty_df)

        assert is_sufficient is False
        assert "empty" in message.lower()

    def test_check_data_sufficiency_missing_indicators(self, strategy):
        """Test data sufficiency with missing indicators."""
        df = pd.DataFrame({
            'close': [100, 101, 102],
            'open': [99, 100, 101],
            'high': [101, 102, 103],
            'low': [98, 99, 100],
            'volume': [1000, 1000, 1000]
        })

        is_sufficient, message = strategy.check_data_sufficiency(df)

        assert is_sufficient is False
        assert "missing required indicators" in message.lower()

    def test_bullish_crossover_detection(self, strategy):
        """Test bullish crossover detection."""
        # Previous: fast below slow, Current: fast above slow
        is_bullish = strategy._detect_bullish_crossover(
            current_fast=51, current_slow=50,
            previous_fast=49, previous_slow=50
        )

        assert is_bullish is True

    def test_bullish_crossover_not_detected(self, strategy):
        """Test no bullish crossover when already above."""
        # Already crossed - no new crossover
        is_bullish = strategy._detect_bullish_crossover(
            current_fast=52, current_slow=50,
            previous_fast=51, previous_slow=50
        )

        assert is_bullish is False

    def test_bearish_crossover_detection(self, strategy):
        """Test bearish crossover detection."""
        # Previous: fast above slow, Current: fast below slow
        is_bearish = strategy._detect_bearish_crossover(
            current_fast=49, current_slow=50,
            previous_fast=51, previous_slow=50
        )

        assert is_bearish is True

    def test_bearish_crossover_not_detected(self, strategy):
        """Test no bearish crossover when already below."""
        is_bearish = strategy._detect_bearish_crossover(
            current_fast=48, current_slow=50,
            previous_fast=49, previous_slow=50
        )

        assert is_bearish is False

    def test_generate_signal_bullish_buy(self, strategy):
        """Test BUY signal generation on bullish crossover."""
        # Create data with bullish crossover and low RSI
        df = pd.DataFrame({
            'close': [100, 101],
            'open': [99, 100],
            'high': [101, 102],
            'low': [98, 99],
            'volume': [1000, 1000],
            'ema_20': [99, 101],  # Crosses above
            'ema_50': [100, 100],
            'rsi_14': [50, 50]  # Below threshold
        }, index=pd.date_range(start='2024-01-01', periods=2))

        signal = strategy.generate_signal(df, current_position=None)

        assert signal.signal_type == SignalType.BUY
        assert "bullish crossover" in signal.trigger_reason.lower()

    def test_generate_signal_no_buy_overbought(self, strategy):
        """Test no BUY signal when RSI is overbought."""
        # Bullish crossover but RSI too high
        df = pd.DataFrame({
            'close': [100, 101],
            'open': [99, 100],
            'high': [101, 102],
            'low': [98, 99],
            'volume': [1000, 1000],
            'ema_20': [99, 101],  # Crosses above
            'ema_50': [100, 100],
            'rsi_14': [75, 75]  # Above threshold
        }, index=pd.date_range(start='2024-01-01', periods=2))

        signal = strategy.generate_signal(df, current_position=None)

        assert signal.signal_type == SignalType.HOLD

    def test_generate_signal_no_buy_already_in_position(self, strategy):
        """Test no BUY signal when already have position."""
        df = pd.DataFrame({
            'close': [100, 101],
            'open': [99, 100],
            'high': [101, 102],
            'low': [98, 99],
            'volume': [1000, 1000],
            'ema_20': [99, 101],  # Crosses above
            'ema_50': [100, 100],
            'rsi_14': [50, 50]
        }, index=pd.date_range(start='2024-01-01', periods=2))

        signal = strategy.generate_signal(df, current_position='long')

        assert signal.signal_type == SignalType.HOLD

    def test_generate_signal_sell_on_bearish_crossover(self, strategy):
        """Test SELL signal on bearish crossover with position."""
        df = pd.DataFrame({
            'close': [100, 101],
            'open': [99, 100],
            'high': [101, 102],
            'low': [98, 99],
            'volume': [1000, 1000],
            'ema_20': [101, 99],  # Crosses below
            'ema_50': [100, 100],
            'rsi_14': [50, 50]
        }, index=pd.date_range(start='2024-01-01', periods=2))

        signal = strategy.generate_signal(df, current_position='long')

        assert signal.signal_type == SignalType.SELL
        assert "bearish crossover" in signal.trigger_reason.lower()

    def test_generate_signal_sell_on_overbought(self, strategy):
        """Test SELL signal when RSI overbought with position."""
        df = pd.DataFrame({
            'close': [100, 101],
            'open': [99, 100],
            'high': [101, 102],
            'low': [98, 99],
            'volume': [1000, 1000],
            'ema_20': [101, 102],  # No crossover
            'ema_50': [100, 100],
            'rsi_14': [75, 75]  # Overbought
        }, index=pd.date_range(start='2024-01-01', periods=2))

        signal = strategy.generate_signal(df, current_position='long')

        assert signal.signal_type == SignalType.SELL
        assert "overbought" in signal.trigger_reason.lower()

    def test_generate_signal_hold(self, strategy):
        """Test HOLD signal when no conditions met."""
        df = pd.DataFrame({
            'close': [100, 101],
            'open': [99, 100],
            'high': [101, 102],
            'low': [98, 99],
            'volume': [1000, 1000],
            'ema_20': [101, 102],  # No crossover
            'ema_50': [100, 100],
            'rsi_14': [50, 50]
        }, index=pd.date_range(start='2024-01-01', periods=2))

        signal = strategy.generate_signal(df, current_position=None)

        assert signal.signal_type == SignalType.HOLD

    def test_generate_signal_with_nan_values(self, strategy):
        """Test signal generation with NaN indicator values."""
        df = pd.DataFrame({
            'close': [100, 101],
            'open': [99, 100],
            'high': [101, 102],
            'low': [98, 99],
            'volume': [1000, 1000],
            'ema_20': [np.nan, np.nan],
            'ema_50': [np.nan, np.nan],
            'rsi_14': [np.nan, np.nan]
        }, index=pd.date_range(start='2024-01-01', periods=2))

        signal = strategy.generate_signal(df, current_position=None)

        assert signal.signal_type == SignalType.HOLD
        assert "insufficient warm-up" in signal.trigger_reason.lower()

    def test_market_context_calculation(self, strategy, sample_data_with_indicators):
        """Test market context is calculated correctly."""
        context = strategy._calculate_market_context(sample_data_with_indicators)

        assert 'volatility' in context
        assert 'volume_vs_avg' in context
        assert 'trend' in context

        assert isinstance(context['volatility'], float)
        assert isinstance(context['volume_vs_avg'], float)
        assert context['trend'] in ['uptrend', 'downtrend', 'sideways']

    def test_get_parameters(self, strategy):
        """Test getting strategy parameters."""
        params = strategy.get_parameters()

        assert params['ema_fast'] == 20
        assert params['ema_slow'] == 50
        assert params['rsi_period'] == 14
        assert params['rsi_threshold'] == 70
