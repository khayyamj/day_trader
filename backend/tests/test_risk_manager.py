"""Tests for RiskManager validation rules."""
import pytest
from unittest.mock import Mock
from datetime import datetime, timezone

from app.services.risk.risk_manager import RiskManager, ValidationResult
from app.models.strategy import Strategy
from app.models.stock import Stock
from app.models.trade import Trade


@pytest.fixture
def mock_ibkr_client():
    """Create mocked IBKR client."""
    client = Mock()
    client.is_connected = True
    return client


@pytest.fixture
def mock_position_sizer():
    """Create mocked PositionSizer."""
    sizer = Mock()
    sizer.get_portfolio_value = Mock(return_value=100000.0)
    sizer.get_available_cash = Mock(return_value=400000.0)
    return sizer


@pytest.fixture
def sample_strategy(db_session):
    """Create sample strategy."""
    strategy = Strategy(
        name="Test Strategy",
        description="Test",
        parameters={},
        status="active"
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


@pytest.fixture
def sample_stock(db_session):
    """Create sample stock."""
    stock = Stock(symbol="AAPL", name="Apple Inc.")
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


@pytest.fixture
def risk_manager(mock_ibkr_client, mock_position_sizer, db_session):
    """Create RiskManager instance."""
    return RiskManager(mock_ibkr_client, mock_position_sizer, db_session)


class TestValidationResult:
    """Test ValidationResult class."""

    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert result.reason is None

    def test_invalid_result_with_reason(self):
        """Test invalid result with reason."""
        result = ValidationResult(is_valid=False, reason="Test failure")

        assert result.is_valid is False
        assert result.reason == "Test failure"


class TestDuplicatePositionCheck:
    """Test duplicate position validation."""

    def test_no_duplicate_position(self, risk_manager, sample_strategy, sample_stock):
        """Test allowing position when no duplicate exists."""
        result = risk_manager.check_duplicate_position(sample_strategy.id, "AAPL")

        assert result.is_valid is True

    def test_reject_duplicate_position(self, risk_manager, sample_strategy, sample_stock, db_session):
        """Test rejecting duplicate position."""
        # Create existing position
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        result = risk_manager.check_duplicate_position(sample_strategy.id, "AAPL")

        assert result.is_valid is False
        assert "Duplicate position" in result.reason

    def test_different_symbol_allowed(self, risk_manager, sample_strategy, sample_stock, db_session):
        """Test that different symbol is allowed."""
        # Create MSFT stock
        msft_stock = Stock(symbol="MSFT", name="Microsoft Corp.")
        db_session.add(msft_stock)
        db_session.commit()

        # Create position in AAPL
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        # Try to open position in MSFT - should be allowed
        result = risk_manager.check_duplicate_position(sample_strategy.id, "MSFT")

        assert result.is_valid is True


class TestCapitalCheck:
    """Test capital sufficiency validation."""

    def test_sufficient_capital(self, risk_manager):
        """Test with sufficient capital."""
        result = risk_manager.check_sufficient_capital(10000.0)

        assert result.is_valid is True

    def test_insufficient_capital(self, risk_manager, mock_position_sizer):
        """Test with insufficient capital."""
        mock_position_sizer.get_available_cash.return_value = 5000.0

        result = risk_manager.check_sufficient_capital(10000.0)

        assert result.is_valid is False
        assert "Insufficient capital" in result.reason


class TestPositionSizeLimit:
    """Test 20% position size limit."""

    def test_position_within_limit(self, risk_manager, mock_position_sizer):
        """Test position within 20% limit."""
        mock_position_sizer.get_portfolio_value.return_value = 100000.0

        # $15,000 position = 15% of portfolio
        result = risk_manager.check_position_size_limit(15000.0)

        assert result.is_valid is True

    def test_position_exceeds_limit(self, risk_manager, mock_position_sizer):
        """Test position exceeding 20% limit."""
        mock_position_sizer.get_portfolio_value.return_value = 100000.0

        # $25,000 position = 25% of portfolio
        result = risk_manager.check_position_size_limit(25000.0)

        assert result.is_valid is False
        assert "exceeds 20% limit" in result.reason

    def test_position_exactly_at_limit(self, risk_manager, mock_position_sizer):
        """Test position exactly at 20% limit."""
        mock_position_sizer.get_portfolio_value.return_value = 100000.0

        # $20,000 position = exactly 20%
        result = risk_manager.check_position_size_limit(20000.0)

        assert result.is_valid is True


class TestStrategyAllocationLimit:
    """Test 50% strategy allocation limit."""

    def test_allocation_within_limit(self, risk_manager, sample_strategy, mock_position_sizer):
        """Test allocation within 50% limit."""
        mock_position_sizer.get_portfolio_value.return_value = 100000.0

        # Adding $20k to strategy (20% of portfolio)
        result = risk_manager.check_portfolio_allocation(sample_strategy.id, 20000.0)

        assert result.is_valid is True

    def test_allocation_exceeds_limit(self, risk_manager, sample_strategy, sample_stock, db_session, mock_position_sizer):
        """Test allocation exceeding 50% limit."""
        mock_position_sizer.get_portfolio_value.return_value = 100000.0

        # Create existing position worth $30k
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=300,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        # Try to add $25k more (total would be $55k = 55%)
        result = risk_manager.check_portfolio_allocation(sample_strategy.id, 25000.0)

        assert result.is_valid is False
        assert "exceeds 50% limit" in result.reason


class TestDailyLossLimit:
    """Test daily loss limit check."""

    def test_strategy_active(self, risk_manager, sample_strategy):
        """Test with active strategy."""
        result = risk_manager.check_daily_loss_limit(sample_strategy.id)

        assert result.is_valid is True

    def test_strategy_paused(self, risk_manager, sample_strategy, db_session):
        """Test with paused strategy."""
        sample_strategy.status = "paused"
        db_session.commit()

        result = risk_manager.check_daily_loss_limit(sample_strategy.id)

        assert result.is_valid is False
        assert "paused" in result.reason


class TestValidateTrade:
    """Test complete trade validation."""

    def test_validate_trade_all_pass(self, risk_manager, sample_strategy, db_session):
        """Test trade validation when all checks pass."""
        # Create MSFT stock
        msft_stock = Stock(symbol="MSFT", name="Microsoft Corp.")
        db_session.add(msft_stock)
        db_session.commit()

        position_size = {
            'quantity': 10,
            'position_value': 1000.0,
            'risk_amount': 50.0,
            'risk_percent': 0.5,
            'position_percent': 1.0
        }

        result = risk_manager.validate_trade(
            strategy_id=sample_strategy.id,
            symbol="MSFT",
            position_size=position_size
        )

        assert result.is_valid is True

    def test_validate_trade_duplicate_fails(self, risk_manager, sample_strategy, sample_stock, db_session):
        """Test that duplicate position fails validation."""
        # Create existing position
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        position_size = {
            'quantity': 10,
            'position_value': 1000.0
        }

        result = risk_manager.validate_trade(
            strategy_id=sample_strategy.id,
            symbol="AAPL",
            position_size=position_size
        )

        assert result.is_valid is False
        assert "Duplicate position" in result.reason

    def test_validate_trade_paused_strategy_fails(self, risk_manager, sample_strategy, db_session):
        """Test that paused strategy fails validation."""
        sample_strategy.status = "paused"
        db_session.commit()

        position_size = {
            'quantity': 10,
            'position_value': 1000.0
        }

        result = risk_manager.validate_trade(
            strategy_id=sample_strategy.id,
            symbol="MSFT",
            position_size=position_size
        )

        assert result.is_valid is False
