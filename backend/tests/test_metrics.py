"""Tests for MetricsCalculator."""
import pytest
from app.services.backtesting.metrics import MetricsCalculator


@pytest.fixture
def calculator():
    """Create metrics calculator."""
    return MetricsCalculator()


@pytest.fixture
def sample_trades():
    """Sample trade data."""
    return [
        {'net_pnl': 1000, 'is_winner': True, 'holding_period_days': 5},
        {'net_pnl': -500, 'is_winner': False, 'holding_period_days': 3},
        {'net_pnl': 1500, 'is_winner': True, 'holding_period_days': 7},
        {'net_pnl': -300, 'is_winner': False, 'holding_period_days': 2},
        {'net_pnl': 800, 'is_winner': True, 'holding_period_days': 4}
    ]


@pytest.fixture
def sample_equity_curve():
    """Sample equity curve."""
    return [100000, 101000, 100500, 102000, 101700, 103200, 102900, 104500]


class TestMetricsCalculator:
    """Test MetricsCalculator class."""

    def test_calculate_returns_positive(self, calculator):
        """Test returns calculation with profit."""
        result = calculator.calculate_returns(
            initial_capital=100000,
            final_equity=115000,
            days=365
        )

        assert result['total_return'] == 15000
        assert result['total_return_pct'] == 15.0
        assert result['annualized_return_pct'] == pytest.approx(15.0, abs=0.1)

    def test_calculate_returns_negative(self, calculator):
        """Test returns calculation with loss."""
        result = calculator.calculate_returns(
            initial_capital=100000,
            final_equity=90000,
            days=365
        )

        assert result['total_return'] == -10000
        assert result['total_return_pct'] == -10.0

    def test_calculate_returns_multi_year(self, calculator):
        """Test annualized returns over multiple years."""
        result = calculator.calculate_returns(
            initial_capital=100000,
            final_equity=130000,
            days=730  # 2 years
        )

        # Should compound properly
        assert result['total_return_pct'] == 30.0
        # Annualized should be ~14% (sqrt(1.3) - 1)
        assert 13 < result['annualized_return_pct'] < 15

    def test_calculate_sharpe_ratio(self, calculator, sample_equity_curve):
        """Test Sharpe ratio calculation."""
        sharpe = calculator.calculate_sharpe_ratio(sample_equity_curve)

        # Should be positive for profitable curve
        assert sharpe > 0
        assert isinstance(sharpe, float)

    def test_calculate_sharpe_ratio_empty(self, calculator):
        """Test Sharpe with empty data."""
        sharpe = calculator.calculate_sharpe_ratio([])

        assert sharpe == 0.0

    def test_calculate_sharpe_ratio_single_value(self, calculator):
        """Test Sharpe with single value."""
        sharpe = calculator.calculate_sharpe_ratio([100000])

        assert sharpe == 0.0

    def test_calculate_sharpe_ratio_no_volatility(self, calculator):
        """Test Sharpe with constant equity."""
        sharpe = calculator.calculate_sharpe_ratio([100000, 100000, 100000])

        assert sharpe == 0.0

    def test_calculate_max_drawdown(self, calculator):
        """Test max drawdown calculation."""
        # Curve with peak at 102000, trough at 100500
        equity = [100000, 101000, 102000, 100500, 101500]

        result = calculator.calculate_max_drawdown(equity)

        # Drawdown = (100500 - 102000) / 102000 = -1.47%
        assert result['max_drawdown_pct'] == pytest.approx(1.47, abs=0.01)
        assert result['max_drawdown_value'] == pytest.approx(1500, abs=1)

    def test_calculate_max_drawdown_no_drawdown(self, calculator):
        """Test with always increasing equity."""
        equity = [100000, 101000, 102000, 103000]

        result = calculator.calculate_max_drawdown(equity)

        assert result['max_drawdown_pct'] == 0.0

    def test_calculate_win_rate(self, calculator, sample_trades):
        """Test win rate calculation."""
        win_rate = calculator.calculate_win_rate(sample_trades)

        # 3 wins out of 5 trades = 60%
        assert win_rate == 60.0

    def test_calculate_win_rate_all_winners(self, calculator):
        """Test win rate with all winning trades."""
        trades = [{'net_pnl': 100}, {'net_pnl': 200}, {'net_pnl': 150}]

        win_rate = calculator.calculate_win_rate(trades)

        assert win_rate == 100.0

    def test_calculate_win_rate_all_losers(self, calculator):
        """Test win rate with all losing trades."""
        trades = [{'net_pnl': -100}, {'net_pnl': -200}]

        win_rate = calculator.calculate_win_rate(trades)

        assert win_rate == 0.0

    def test_calculate_win_rate_empty(self, calculator):
        """Test win rate with no trades."""
        win_rate = calculator.calculate_win_rate([])

        assert win_rate == 0.0

    def test_calculate_profit_factor(self, calculator, sample_trades):
        """Test profit factor calculation."""
        profit_factor = calculator.calculate_profit_factor(sample_trades)

        # Gross profit = 1000 + 1500 + 800 = 3300
        # Gross loss = 500 + 300 = 800
        # PF = 3300 / 800 = 4.125
        assert profit_factor == pytest.approx(4.125, abs=0.01)

    def test_calculate_profit_factor_no_losses(self, calculator):
        """Test profit factor with only wins."""
        trades = [{'net_pnl': 100}, {'net_pnl': 200}]

        profit_factor = calculator.calculate_profit_factor(trades)

        assert profit_factor == float('inf')

    def test_calculate_profit_factor_no_wins(self, calculator):
        """Test profit factor with only losses."""
        trades = [{'net_pnl': -100}, {'net_pnl': -200}]

        profit_factor = calculator.calculate_profit_factor(trades)

        assert profit_factor == 0.0

    def test_calculate_avg_win_loss(self, calculator, sample_trades):
        """Test average win/loss calculation."""
        result = calculator.calculate_avg_win_loss(sample_trades)

        # Avg win = (1000 + 1500 + 800) / 3 = 1100
        # Avg loss = (-500 + -300) / 2 = -400
        # Ratio = 1100 / 400 = 2.75
        assert result['avg_win'] == pytest.approx(1100, abs=1)
        assert result['avg_loss'] == pytest.approx(-400, abs=1)
        assert result['win_loss_ratio'] == pytest.approx(2.75, abs=0.01)

    def test_calculate_trade_stats(self, calculator, sample_trades):
        """Test comprehensive trade statistics."""
        stats = calculator.calculate_trade_stats(sample_trades)

        assert stats['total_trades'] == 5
        assert stats['winning_trades'] == 3
        assert stats['losing_trades'] == 2
        assert stats['win_rate_pct'] == 60.0
        assert stats['avg_holding_period_days'] == pytest.approx(4.2, abs=0.1)
        assert stats['largest_win'] == 1500
        assert stats['largest_loss'] == -500

    def test_calculate_trade_stats_empty(self, calculator):
        """Test trade stats with no trades."""
        stats = calculator.calculate_trade_stats([])

        assert stats['total_trades'] == 0
        assert stats['winning_trades'] == 0
        assert stats['losing_trades'] == 0

    def test_calculate_all_metrics(self, calculator, sample_equity_curve, sample_trades):
        """Test calculating all metrics together."""
        all_metrics = calculator.calculate_all_metrics(
            initial_capital=100000,
            final_equity=104500,
            equity_curve=sample_equity_curve,
            trades=sample_trades,
            days=365
        )

        # Verify all metrics present
        assert 'total_return_pct' in all_metrics
        assert 'annualized_return_pct' in all_metrics
        assert 'sharpe_ratio' in all_metrics
        assert 'max_drawdown_pct' in all_metrics
        assert 'win_rate_pct' in all_metrics
        assert 'profit_factor' in all_metrics
        assert 'avg_win' in all_metrics
        assert 'avg_loss' in all_metrics
        assert 'total_trades' in all_metrics

    def test_calculate_consecutive_wins_losses(self, calculator):
        """Test consecutive streak calculation."""
        trades = [
            {'is_winner': True},   # Win 1
            {'is_winner': True},   # Win 2
            {'is_winner': True},   # Win 3 (max streak)
            {'is_winner': False},  # Loss 1
            {'is_winner': False},  # Loss 2 (max streak)
            {'is_winner': True},   # Win 1
        ]

        result = calculator.calculate_consecutive_wins_losses(trades)

        assert result['max_consecutive_wins'] == 3
        assert result['max_consecutive_losses'] == 2

    def test_risk_free_rate_impact(self):
        """Test that risk-free rate affects Sharpe calculation."""
        calc_zero = MetricsCalculator(risk_free_rate=0.0)
        calc_five = MetricsCalculator(risk_free_rate=0.05)

        equity = [100000, 101000, 102000, 103000]

        sharpe_zero = calc_zero.calculate_sharpe_ratio(equity)
        sharpe_five = calc_five.calculate_sharpe_ratio(equity)

        # Higher risk-free rate should reduce Sharpe
        assert sharpe_five < sharpe_zero
