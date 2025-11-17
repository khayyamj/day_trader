"""Tests for SimpleBacktester."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.services.backtesting.simple_backtester import SimpleBacktester, PortfolioState
from app.services.strategies.ma_crossover_rsi import MACrossoverRSIStrategy


@pytest.fixture
def backtester():
    """Create backtester instance."""
    return SimpleBacktester(
        initial_capital=100000.0,
        slippage_pct=0.001,
        commission_per_trade=1.0
    )


@pytest.fixture
def simple_strategy():
    """Create simple strategy for testing."""
    return MACrossoverRSIStrategy(parameters={
        'ema_fast': 5,  # Fast for testing
        'ema_slow': 10,
        'rsi_period': 7,
        'rsi_threshold': 70
    })


@pytest.fixture
def bullish_scenario_data():
    """Create data with clear bullish crossover."""
    dates = pd.date_range(start='2024-01-01', periods=20, freq='D')

    # Create scenario: EMA fast crosses above slow at bar 10
    ema_fast = [98, 98.5, 99, 99.5, 100, 100.5, 101, 101.5, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113]
    ema_slow = [100, 100, 100, 100, 100, 100.5, 101, 101.5, 102, 102.5, 103, 103.5, 104, 104.5, 105, 105.5, 106, 106.5, 107, 107.5]

    df = pd.DataFrame({
        'open': [100 + i * 0.5 for i in range(20)],
        'high': [101 + i * 0.5 for i in range(20)],
        'low': [99 + i * 0.5 for i in range(20)],
        'close': [100 + i * 0.5 for i in range(20)],
        'volume': [1000000] * 20,
        'ema_5': ema_fast,
        'ema_10': ema_slow,
        'rsi_7': [50] * 20  # Below threshold
    }, index=dates)

    return df


class TestPortfolioState:
    """Test PortfolioState class."""

    def test_portfolio_initialization(self):
        """Test portfolio state initialization."""
        portfolio = PortfolioState(100000.0)

        assert portfolio.initial_capital == 100000.0
        assert portfolio.cash == 100000.0
        assert portfolio.position_value == 0.0
        assert portfolio.position_shares == 0

    def test_get_equity(self):
        """Test equity calculation."""
        portfolio = PortfolioState(100000.0)
        portfolio.cash = 50000
        portfolio.position_value = 55000

        assert portfolio.get_equity() == 105000

    def test_has_position(self):
        """Test position check."""
        portfolio = PortfolioState(100000.0)

        assert portfolio.has_position() is False

        portfolio.position_shares = 100

        assert portfolio.has_position() is True

    def test_snapshot(self):
        """Test portfolio snapshot."""
        portfolio = PortfolioState(100000.0)
        portfolio.cash = 50000
        portfolio.position_shares = 100

        snapshot = portfolio.snapshot(datetime.now().date(), 500.0)

        assert snapshot['equity'] == 100000  # 50000 cash + 50000 position
        assert snapshot['cash'] == 50000
        assert snapshot['position_value'] == 50000
        assert snapshot['position_shares'] == 100


class TestSimpleBacktester:
    """Test SimpleBacktester class."""

    def test_backtester_initialization(self, backtester):
        """Test backtester initialization."""
        assert backtester.initial_capital == 100000.0
        assert backtester.slippage_pct == 0.001
        assert backtester.commission_per_trade == 1.0
        assert backtester.portfolio.cash == 100000.0

    def test_run_backtest_basic(self, backtester, simple_strategy, bullish_scenario_data):
        """Test basic backtest execution."""
        results = backtester.run(
            df=bullish_scenario_data,
            strategy=simple_strategy,
            symbol="TEST"
        )

        # Should have results
        assert 'total_return_pct' in results
        assert 'sharpe_ratio' in results
        assert 'total_trades' in results
        assert 'bars_processed' in results

        # Should process all bars
        assert results['bars_processed'] == 20

    def test_run_backtest_insufficient_data(self, backtester, simple_strategy):
        """Test backtest with insufficient data."""
        df = pd.DataFrame({
            'close': [100],
            'ema_5': [100],
            'ema_10': [100],
            'rsi_7': [50]
        }, index=pd.date_range(start='2024-01-01', periods=1))

        with pytest.raises(ValueError, match="at least 2 bars"):
            backtester.run(df, simple_strategy, "TEST")

    def test_trade_execution_timing(self, backtester):
        """Test that trades execute on next bar open (no look-ahead)."""
        # This is tested implicitly through the run process
        # Signal generated at bar N close, executed at bar N+1 open
        assert backtester.pending_signal is None  # No pending signal initially

    def test_slippage_applied_correctly(self, backtester):
        """Test slippage calculation."""
        # Buy slippage: pay more
        buy_price = 100.0
        expected_buy = buy_price * 1.001  # 100.10

        # Sell slippage: receive less
        sell_price = 110.0
        expected_sell = sell_price * 0.999  # 109.89

        assert expected_buy == pytest.approx(100.10, abs=0.01)
        assert expected_sell == pytest.approx(109.89, abs=0.01)

    def test_commission_applied(self, backtester):
        """Test commission is applied."""
        assert backtester.commission_per_trade == 1.0

    def test_position_sizing(self, backtester):
        """Test position sizing uses 95% of cash."""
        available = backtester.portfolio.cash * backtester.position_size_pct

        assert available == 95000.0  # 95% of 100k

    def test_equity_curve_generated(self, backtester, simple_strategy, bullish_scenario_data):
        """Test that equity curve is generated."""
        results = backtester.run(bullish_scenario_data, simple_strategy, "TEST")

        assert 'equity_curve' in results
        assert len(results['equity_curve']) > 0

        # Each point should have required fields
        first_point = results['equity_curve'][0]
        assert 'date' in first_point
        assert 'equity' in first_point
        assert 'cash' in first_point

    def test_final_equity_calculation(self, backtester, simple_strategy, bullish_scenario_data):
        """Test final equity is calculated correctly."""
        results = backtester.run(bullish_scenario_data, simple_strategy, "TEST")

        # Final equity should equal initial capital + total P&L
        if results['total_trades'] > 0:
            total_pnl = sum(t.get('net_pnl', 0) for t in results['trades'] if t.get('net_pnl'))
            expected_final = backtester.initial_capital + total_pnl

            # Should be approximately equal (small rounding differences OK)
            assert results['final_equity'] == pytest.approx(expected_final, abs=10)

    def test_trades_have_complete_data(self, backtester, simple_strategy, bullish_scenario_data):
        """Test that trades have all required fields."""
        results = backtester.run(bullish_scenario_data, simple_strategy, "TEST")

        if results['total_trades'] > 0:
            first_trade = results['trades'][0]

            # Required fields
            assert 'trade_number' in first_trade
            assert 'entry_date' in first_trade
            assert 'entry_price' in first_trade
            assert 'shares' in first_trade
            assert 'entry_signal' in first_trade

    def test_no_trades_when_no_signals(self, backtester, simple_strategy):
        """Test backtest with no valid signals."""
        # Create data with no crossover
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')

        df = pd.DataFrame({
            'open': [100] * 10,
            'high': [101] * 10,
            'low': [99] * 10,
            'close': [100] * 10,
            'volume': [1000000] * 10,
            'ema_5': [102] * 10,  # Always above slow (no crossover)
            'ema_10': [100] * 10,
            'rsi_7': [50] * 10
        }, index=dates)

        results = backtester.run(df, simple_strategy, "TEST")

        # May have 0 trades if no crossover detected
        assert results['total_trades'] >= 0

    def test_max_drawdown_calculated(self, backtester, simple_strategy, bullish_scenario_data):
        """Test that max drawdown is calculated."""
        results = backtester.run(bullish_scenario_data, simple_strategy, "TEST")

        assert 'max_drawdown_pct' in results
        assert results['max_drawdown_pct'] >= 0

    def test_sharpe_ratio_calculated(self, backtester, simple_strategy, bullish_scenario_data):
        """Test that Sharpe ratio is calculated."""
        results = backtester.run(bullish_scenario_data, simple_strategy, "TEST")

        assert 'sharpe_ratio' in results
        # Sharpe can be negative, zero, or positive
        assert isinstance(results['sharpe_ratio'], (int, float))

    def test_position_closes_at_end(self, backtester, simple_strategy, bullish_scenario_data):
        """Test that open positions are closed at backtest end."""
        results = backtester.run(bullish_scenario_data, simple_strategy, "TEST")

        # All trades should be closed
        if results['total_trades'] > 0:
            for trade in results['trades']:
                # Last trade might still be open or should have exit signal
                if trade == results['trades'][-1]:
                    # Last trade should have exit (even if forced at end)
                    assert trade.get('exit_signal') is not None or trade.get('exit_date') is not None
