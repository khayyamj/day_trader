"""Tests for PositionSizer with 2% risk rule."""
import pytest
from unittest.mock import Mock
from decimal import Decimal

from app.services.risk.position_sizer import PositionSizer


@pytest.fixture
def mock_ibkr_client():
    """Create a mocked IBKR client with account data."""
    client = Mock()
    client.is_connected = True

    # Mock account summary
    client.get_account_summary = Mock(return_value={
        'NetLiquidation': 100000.00,
        'BuyingPower': 400000.00
    })

    return client


@pytest.fixture
def position_sizer(mock_ibkr_client):
    """Create PositionSizer instance."""
    return PositionSizer(mock_ibkr_client)


class TestPositionSizerBasicCalculations:
    """Test basic position sizing calculations."""

    def test_2_percent_risk_rule(self, position_sizer):
        """Test standard 2% risk calculation."""
        # Portfolio: $10,000, Entry: $100, Stop: $95, Risk per share: $5
        # Expected: (10000 * 0.02) / 5 = 40 shares
        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            portfolio_value=10000.0
        )

        # Should be capped at 20% = 20 shares (because 40 * $100 = $4000 = 40%)
        assert result['quantity'] == 20
        assert result['position_value'] == 2000.0
        assert result['capped'] is True
        assert result['cap_reason'] == 'MAX_POSITION_SIZE'

    def test_small_position_not_capped(self, position_sizer):
        """Test position that doesn't hit 20% cap."""
        # Portfolio: $100,000, Entry: $100, Stop: $95, Risk per share: $5
        # Expected: (100000 * 0.02) / 5 = 400 shares = $40,000 = 40% (capped at 20%)
        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            portfolio_value=100000.0
        )

        # Should be capped at 20% = $20,000 / $100 = 200 shares
        assert result['quantity'] == 200
        assert result['position_value'] == 20000.0
        assert result['position_percent'] == 20.0

    def test_high_risk_per_share(self, position_sizer):
        """Test with high risk per share (large stop distance)."""
        # Portfolio: $10,000, Entry: $100, Stop: $50, Risk per share: $50
        # Expected: (10000 * 0.02) / 50 = 4 shares
        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=50.0,
            portfolio_value=10000.0
        )

        assert result['quantity'] == 4
        assert result['position_value'] == 400.0
        assert result['risk_amount'] == 200.0
        assert result['capped'] is False

    def test_minimum_one_share(self, position_sizer):
        """Test that minimum position is 1 share."""
        # Very small portfolio with high risk
        result = position_sizer.calculate_position_size(
            entry_price=1000.0,
            stop_loss=900.0,
            portfolio_value=500.0  # Only $500
        )

        assert result['quantity'] >= 1


class TestPositionSizer20PercentCap:
    """Test 20% position size cap."""

    def test_position_capped_at_20_percent(self, position_sizer):
        """Test that positions are capped at 20% of portfolio."""
        # Tight stop that would normally give large position
        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=99.5,  # Only $0.50 risk per share
            portfolio_value=10000.0
        )

        # 20% cap = $2000 / $100 = 20 shares
        assert result['quantity'] == 20
        assert result['position_percent'] <= 20.0
        assert result['capped'] is True

    def test_various_portfolio_sizes(self, position_sizer):
        """Test 20% cap with different portfolio sizes."""
        test_cases = [
            (5000.0, 10),    # $5k portfolio -> max 10 shares @ $100
            (10000.0, 20),   # $10k portfolio -> max 20 shares
            (50000.0, 100),  # $50k portfolio -> max 100 shares
        ]

        for portfolio, expected_max in test_cases:
            result = position_sizer.calculate_position_size(
                entry_price=100.0,
                stop_loss=99.0,
                portfolio_value=portfolio
            )

            assert result['quantity'] <= expected_max
            assert result['position_percent'] <= 20.0


class TestPositionSizerValidation:
    """Test position validation."""

    def test_validate_sufficient_capital(self, position_sizer):
        """Test validation with sufficient capital."""
        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            portfolio_value=10000.0
        )

        is_valid, error = position_sizer.validate_position(result)

        assert is_valid is True
        assert error is None

    def test_validate_insufficient_capital(self, position_sizer, mock_ibkr_client):
        """Test validation with insufficient capital."""
        # Mock low buying power
        mock_ibkr_client.get_account_summary.return_value = {
            'NetLiquidation': 100000.00,
            'BuyingPower': 1000.00  # Low buying power
        }

        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            portfolio_value=10000.0
        )

        is_valid, error = position_sizer.validate_position(result)

        assert is_valid is False
        assert "Insufficient buying power" in error


class TestPositionSizerInputValidation:
    """Test input validation."""

    def test_invalid_entry_price(self, position_sizer):
        """Test with invalid entry price."""
        with pytest.raises(ValueError, match="Invalid entry price"):
            position_sizer.calculate_position_size(
                entry_price=0.0,
                stop_loss=95.0,
                portfolio_value=10000.0
            )

    def test_invalid_stop_loss(self, position_sizer):
        """Test with invalid stop loss."""
        with pytest.raises(ValueError, match="Invalid stop loss"):
            position_sizer.calculate_position_size(
                entry_price=100.0,
                stop_loss=0.0,
                portfolio_value=10000.0
            )

    def test_stop_above_entry(self, position_sizer):
        """Test with stop loss above entry price."""
        with pytest.raises(ValueError, match="Stop loss .* must be below entry price"):
            position_sizer.calculate_position_size(
                entry_price=100.0,
                stop_loss=105.0,
                portfolio_value=10000.0
            )

    def test_negative_entry_price(self, position_sizer):
        """Test with negative entry price."""
        with pytest.raises(ValueError):
            position_sizer.calculate_position_size(
                entry_price=-100.0,
                stop_loss=95.0,
                portfolio_value=10000.0
            )


class TestPositionSizerPortfolioValue:
    """Test portfolio value retrieval."""

    def test_get_portfolio_value(self, position_sizer, mock_ibkr_client):
        """Test getting portfolio value from IBKR."""
        portfolio_value = position_sizer.get_portfolio_value()

        assert portfolio_value == 100000.00
        mock_ibkr_client.get_account_summary.assert_called_once()

    def test_get_portfolio_value_not_connected(self, position_sizer):
        """Test getting portfolio value when not connected."""
        position_sizer.ibkr_client.is_connected = False

        with pytest.raises(ConnectionError, match="Not connected to IBKR"):
            position_sizer.get_portfolio_value()

    def test_get_available_cash(self, position_sizer, mock_ibkr_client):
        """Test getting available cash."""
        cash = position_sizer.get_available_cash()

        assert cash == 400000.00
        mock_ibkr_client.get_account_summary.assert_called()


class TestPositionSizerRiskCalculations:
    """Test risk calculation details."""

    def test_risk_amount_calculation(self, position_sizer):
        """Test that risk amount is calculated correctly."""
        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            portfolio_value=10000.0
        )

        # Risk per share = $5, Quantity = 20 shares (capped)
        # Risk amount = 20 * $5 = $100
        assert result['risk_amount'] == 100.0

    def test_risk_percent_calculation(self, position_sizer):
        """Test that risk percent is calculated correctly."""
        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            portfolio_value=10000.0
        )

        # Risk = $100, Portfolio = $10,000
        # Risk % = (100 / 10000) * 100 = 1%
        assert result['risk_percent'] == 1.0

    def test_position_percent_calculation(self, position_sizer):
        """Test that position percent is calculated correctly."""
        result = position_sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            portfolio_value=10000.0
        )

        # Position = 20 * $100 = $2000, Portfolio = $10,000
        # Position % = (2000 / 10000) * 100 = 20%
        assert result['position_percent'] == 20.0
