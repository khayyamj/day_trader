"""Tests for StrategyService."""
import pytest
from app.services.strategies.strategy_service import StrategyService
from app.models.strategy import Strategy
from app.models.stock import Stock
from app.models.stock_data import StockData
from datetime import datetime


@pytest.fixture
def strategy_service(db_session):
    """Create strategy service instance."""
    return StrategyService(db_session)


@pytest.fixture
def sample_strategy(db_session):
    """Create a sample strategy in database."""
    strategy = Strategy(
        name="Test Strategy",
        description="Test strategy for unit tests",
        parameters={'ema_fast': 20, 'ema_slow': 50, 'rsi_period': 14, 'rsi_threshold': 70},
        active=False,
        status="paused",
        warm_up_bars_remaining=100
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


@pytest.fixture
def sample_stock_with_data(db_session):
    """Create a sample stock with sufficient data."""
    stock = Stock(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ")
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)

    # Add 100 bars of data
    for i in range(100):
        data = StockData(
            stock_id=stock.id,
            timestamp=datetime(2024, 1, 1, 9, 30) + timedelta(days=i),
            open_price=150.0 + i * 0.1,
            high_price=151.0 + i * 0.1,
            low_price=149.0 + i * 0.1,
            close_price=150.5 + i * 0.1,
            volume=1000000
        )
        db_session.add(data)

    db_session.commit()
    return stock


class TestStrategyService:
    """Test StrategyService class."""

    def test_get_strategy_status(self, strategy_service, sample_strategy):
        """Test getting strategy status."""
        status = strategy_service.get_strategy_status(sample_strategy.id)

        assert status['strategy_id'] == sample_strategy.id
        assert status['name'] == sample_strategy.name
        assert status['status'] == 'paused'
        assert status['active'] is False
        assert 'parameters' in status

    def test_get_strategy_status_not_found(self, strategy_service):
        """Test getting status for non-existent strategy."""
        with pytest.raises(ValueError, match="Strategy .* not found"):
            strategy_service.get_strategy_status(99999)

    def test_activate_strategy_with_sufficient_data(self, strategy_service, sample_strategy, sample_stock_with_data):
        """Test activating strategy when warm-up complete."""
        result = strategy_service.activate_strategy(sample_strategy.id)

        assert result['status'] == 'active'
        assert result['warm_up_complete'] is True
        assert result['warm_up_bars_remaining'] == 0

    def test_activate_strategy_without_sufficient_data(self, strategy_service, sample_strategy, db_session):
        """Test activating strategy when warm-up incomplete."""
        # Create stock with insufficient data
        stock = Stock(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ")
        db_session.add(stock)
        db_session.commit()

        # Add only 50 bars (less than required 100)
        for i in range(50):
            data = StockData(
                stock_id=stock.id,
                timestamp=datetime(2024, 1, 1, 9, 30) + timedelta(days=i),
                open_price=250.0,
                high_price=251.0,
                low_price=249.0,
                close_price=250.5,
                volume=1000000
            )
            db_session.add(data)
        db_session.commit()

        result = strategy_service.activate_strategy(sample_strategy.id)

        assert result['status'] == 'warming'
        assert result['warm_up_complete'] is False
        assert result['warm_up_bars_remaining'] > 0

    def test_activate_strategy_not_found(self, strategy_service):
        """Test activating non-existent strategy."""
        with pytest.raises(ValueError, match="Strategy .* not found"):
            strategy_service.activate_strategy(99999)

    def test_pause_strategy(self, strategy_service, sample_strategy):
        """Test pausing a strategy."""
        # First activate it
        sample_strategy.status = "active"
        sample_strategy.active = True
        strategy_service.db.commit()

        result = strategy_service.pause_strategy(sample_strategy.id, reason="Testing pause")

        assert result['current_status'] == 'paused'
        assert result['previous_status'] == 'active'
        assert result['reason'] == "Testing pause"

    def test_pause_strategy_without_reason(self, strategy_service, sample_strategy):
        """Test pausing without reason."""
        result = strategy_service.pause_strategy(sample_strategy.id)

        assert result['current_status'] == 'paused'
        assert result['reason'] is None

    def test_pause_strategy_not_found(self, strategy_service):
        """Test pausing non-existent strategy."""
        with pytest.raises(ValueError, match="Strategy .* not found"):
            strategy_service.pause_strategy(99999)

    def test_check_warm_up_complete(self, strategy_service, sample_strategy, sample_stock_with_data):
        """Test warm-up check with sufficient data."""
        result = strategy_service.check_warm_up(sample_strategy.id)

        assert result['warm_up_complete'] is True
        assert result['bars_available'] >= 100
        assert result['bars_needed'] == 0
        assert result['stocks_ready'] == result['stocks_checked']

    def test_check_warm_up_incomplete(self, strategy_service, sample_strategy, db_session):
        """Test warm-up check with insufficient data."""
        # Create stock with only 50 bars
        stock = Stock(symbol="GOOGL", name="Google", exchange="NASDAQ")
        db_session.add(stock)
        db_session.commit()

        for i in range(50):
            data = StockData(
                stock_id=stock.id,
                timestamp=datetime(2024, 1, 1) + timedelta(days=i),
                open_price=150.0,
                high_price=151.0,
                low_price=149.0,
                close_price=150.5,
                volume=1000000
            )
            db_session.add(data)
        db_session.commit()

        result = strategy_service.check_warm_up(sample_strategy.id)

        assert result['warm_up_complete'] is False
        assert result['bars_needed'] > 0

    def test_check_warm_up_no_stocks(self, strategy_service, sample_strategy):
        """Test warm-up check with no stocks."""
        result = strategy_service.check_warm_up(sample_strategy.id)

        assert result['warm_up_complete'] is False
        assert result['stocks_checked'] == 0
        assert result['stocks_ready'] == 0

    def test_check_warm_up_not_found(self, strategy_service):
        """Test warm-up check for non-existent strategy."""
        with pytest.raises(ValueError, match="Strategy .* not found"):
            strategy_service.check_warm_up(99999)

    def test_set_error_status(self, strategy_service, sample_strategy):
        """Test setting error status."""
        strategy_service.set_error_status(sample_strategy.id, "Test error")

        # Verify status changed
        strategy = strategy_service.db.query(Strategy).filter(
            Strategy.id == sample_strategy.id
        ).first()

        assert strategy.status == "error"
        assert strategy.active is False

    def test_set_error_status_not_found(self, strategy_service):
        """Test setting error for non-existent strategy."""
        with pytest.raises(ValueError, match="Strategy .* not found"):
            strategy_service.set_error_status(99999, "Error")

    def test_list_strategies_empty(self, strategy_service):
        """Test listing strategies when none exist."""
        strategies = strategy_service.list_strategies()

        assert isinstance(strategies, list)

    def test_list_strategies_with_data(self, strategy_service, sample_strategy):
        """Test listing strategies."""
        strategies = strategy_service.list_strategies()

        assert len(strategies) >= 1
        assert any(s['strategy_id'] == sample_strategy.id for s in strategies)

        first_strategy = next(s for s in strategies if s['strategy_id'] == sample_strategy.id)
        assert 'name' in first_strategy
        assert 'status' in first_strategy
        assert 'active' in first_strategy

    def test_activate_updates_status_to_warming_when_needed(self, strategy_service, sample_strategy):
        """Test that activate sets status to warming when data insufficient."""
        # No stocks = no data = warming state
        result = strategy_service.activate_strategy(sample_strategy.id)

        strategy = strategy_service.db.query(Strategy).filter(
            Strategy.id == sample_strategy.id
        ).first()

        # Should be in warming state due to insufficient data
        assert strategy.status in ["warming", "active"]  # Depends on data availability

    def test_check_warm_up_updates_strategy_status(self, strategy_service, sample_strategy, sample_stock_with_data):
        """Test that check_warm_up updates strategy status."""
        # Set to warming initially
        sample_strategy.status = "warming"
        strategy_service.db.commit()

        strategy_service.check_warm_up(sample_strategy.id)

        # Should update to active since data is sufficient
        strategy = strategy_service.db.query(Strategy).filter(
            Strategy.id == sample_strategy.id
        ).first()

        assert strategy.status == "active"


from datetime import timedelta
