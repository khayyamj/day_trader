"""Tests for LossLimitDetector."""
import pytest
from datetime import datetime, timezone

from app.services.risk.loss_limit_detector import LossLimitDetector
from app.models.strategy import Strategy
from app.models.stock import Stock
from app.models.trade import Trade


@pytest.fixture
def sample_strategy(db_session):
    """Create sample strategy."""
    strategy = Strategy(
        name="Test Strategy",
        description="Test",
        parameters={},
        status="active",
        consecutive_losses_today=0
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
def loss_detector(db_session):
    """Create LossLimitDetector instance."""
    return LossLimitDetector(db_session)


class TestTrackTradeOutcome:
    """Test trade outcome tracking."""

    def test_track_losing_trade(self, loss_detector, sample_strategy, sample_stock, db_session):
        """Test tracking a losing trade."""
        # Create losing trade
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            exit_time=datetime.now(timezone.utc),
            exit_price=95.0,
            profit_loss=-50.0,
            trade_type="LONG",
            status="CLOSED"
        )
        db_session.add(trade)
        db_session.commit()
        db_session.refresh(trade)

        # Track outcome
        loss_detector.track_trade_outcome(trade.id)

        # Check strategy
        db_session.refresh(sample_strategy)
        assert sample_strategy.consecutive_losses_today == 1

    def test_track_winning_trade_resets_counter(self, loss_detector, sample_strategy, sample_stock, db_session):
        """Test that winning trade resets counter."""
        # Set initial losses
        sample_strategy.consecutive_losses_today = 2
        db_session.commit()

        # Create winning trade
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            exit_time=datetime.now(timezone.utc),
            exit_price=110.0,
            profit_loss=100.0,
            trade_type="LONG",
            status="CLOSED"
        )
        db_session.add(trade)
        db_session.commit()
        db_session.refresh(trade)

        # Track outcome
        loss_detector.track_trade_outcome(trade.id)

        # Check counter reset
        db_session.refresh(sample_strategy)
        assert sample_strategy.consecutive_losses_today == 0

    def test_track_multiple_consecutive_losses(self, loss_detector, sample_strategy, sample_stock, db_session):
        """Test tracking multiple consecutive losses."""
        for i in range(3):
            trade = Trade(
                strategy_id=sample_strategy.id,
                stock_id=sample_stock.id,
                entry_time=datetime.now(timezone.utc),
                entry_price=100.0,
                quantity=10,
                exit_time=datetime.now(timezone.utc),
                exit_price=95.0,
                profit_loss=-50.0,
                trade_type="LONG",
                status="CLOSED"
            )
            db_session.add(trade)
            db_session.commit()
            db_session.refresh(trade)

            loss_detector.track_trade_outcome(trade.id)

        db_session.refresh(sample_strategy)
        assert sample_strategy.consecutive_losses_today == 3

    def test_track_open_trade_ignored(self, loss_detector, sample_strategy, sample_stock, db_session):
        """Test that open trades are ignored."""
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            trade_type="LONG",
            status="OPEN"  # Not closed yet
        )
        db_session.add(trade)
        db_session.commit()
        db_session.refresh(trade)

        initial_count = sample_strategy.consecutive_losses_today

        # This should not change the counter
        loss_detector.track_trade_outcome(trade.id)

        db_session.refresh(sample_strategy)
        assert sample_strategy.consecutive_losses_today == initial_count


class TestCheckLossLimit:
    """Test loss limit checking."""

    def test_under_limit(self, loss_detector, sample_strategy):
        """Test when under loss limit."""
        sample_strategy.consecutive_losses_today = 2

        limit_reached = loss_detector.check_loss_limit(sample_strategy.id)

        assert limit_reached is False

    def test_at_limit(self, loss_detector, sample_strategy, db_session):
        """Test when at loss limit."""
        sample_strategy.consecutive_losses_today = 3
        db_session.commit()

        limit_reached = loss_detector.check_loss_limit(sample_strategy.id)

        assert limit_reached is True

    def test_over_limit(self, loss_detector, sample_strategy, db_session):
        """Test when over loss limit."""
        sample_strategy.consecutive_losses_today = 5
        db_session.commit()

        limit_reached = loss_detector.check_loss_limit(sample_strategy.id)

        assert limit_reached is True


class TestPauseStrategyOnLimit:
    """Test strategy pausing."""

    def test_pause_strategy(self, loss_detector, sample_strategy, db_session):
        """Test pausing strategy on limit."""
        sample_strategy.consecutive_losses_today = 3
        sample_strategy.status = "active"
        db_session.commit()

        loss_detector.pause_strategy_on_limit(sample_strategy.id)

        db_session.refresh(sample_strategy)
        assert sample_strategy.status == "paused"

    def test_pause_already_paused_strategy(self, loss_detector, sample_strategy, db_session):
        """Test pausing already paused strategy."""
        sample_strategy.status = "paused"
        db_session.commit()

        # Should not raise error
        loss_detector.pause_strategy_on_limit(sample_strategy.id)

        db_session.refresh(sample_strategy)
        assert sample_strategy.status == "paused"


class TestResetDailyCounters:
    """Test daily counter reset."""

    def test_reset_single_strategy(self, loss_detector, sample_strategy, db_session):
        """Test resetting counter for single strategy."""
        sample_strategy.consecutive_losses_today = 3
        db_session.commit()

        loss_detector.reset_daily_counters()

        db_session.refresh(sample_strategy)
        assert sample_strategy.consecutive_losses_today == 0

    def test_reset_multiple_strategies(self, loss_detector, db_session):
        """Test resetting counters for multiple strategies."""
        strategies = []
        for i in range(3):
            strategy = Strategy(
                name=f"Strategy {i}",
                parameters={},
                consecutive_losses_today=i + 1
            )
            strategies.append(strategy)
            db_session.add(strategy)
        db_session.commit()

        loss_detector.reset_daily_counters()

        for strategy in strategies:
            db_session.refresh(strategy)
            assert strategy.consecutive_losses_today == 0

    def test_reset_only_affects_nonzero_counters(self, loss_detector, db_session):
        """Test that reset only affects strategies with losses."""
        strategy1 = Strategy(name="Strategy 1", parameters={}, consecutive_losses_today=2)
        strategy2 = Strategy(name="Strategy 2", parameters={}, consecutive_losses_today=0)

        db_session.add(strategy1)
        db_session.add(strategy2)
        db_session.commit()

        loss_detector.reset_daily_counters()

        db_session.refresh(strategy1)
        db_session.refresh(strategy2)

        assert strategy1.consecutive_losses_today == 0
        assert strategy2.consecutive_losses_today == 0


class TestGetStrategyStatus:
    """Test getting strategy status."""

    def test_get_status_active_strategy(self, loss_detector, sample_strategy):
        """Test getting status of active strategy."""
        status = loss_detector.get_strategy_status(sample_strategy.id)

        assert status['strategy_id'] == sample_strategy.id
        assert status['strategy_name'] == sample_strategy.name
        assert status['status'] == 'active'
        assert status['consecutive_losses_today'] == 0
        assert status['loss_limit'] == 3
        assert status['is_paused'] is False
        assert status['losses_until_pause'] == 3

    def test_get_status_with_losses(self, loss_detector, sample_strategy, db_session):
        """Test getting status with some losses."""
        sample_strategy.consecutive_losses_today = 2
        db_session.commit()

        status = loss_detector.get_strategy_status(sample_strategy.id)

        assert status['consecutive_losses_today'] == 2
        assert status['losses_until_pause'] == 1

    def test_get_status_paused_strategy(self, loss_detector, sample_strategy, db_session):
        """Test getting status of paused strategy."""
        sample_strategy.status = 'paused'
        sample_strategy.consecutive_losses_today = 3
        db_session.commit()

        status = loss_detector.get_strategy_status(sample_strategy.id)

        assert status['is_paused'] is True
        assert status['losses_until_pause'] == 0


class TestIntegrationScenario:
    """Test complete loss limit scenario."""

    def test_complete_loss_limit_scenario(self, loss_detector, sample_strategy, sample_stock, db_session):
        """Test complete scenario: 3 losses -> pause -> win -> reset."""
        # Simulate 3 consecutive losses
        for i in range(3):
            trade = Trade(
                strategy_id=sample_strategy.id,
                stock_id=sample_stock.id,
                entry_time=datetime.now(timezone.utc),
                entry_price=100.0,
                quantity=10,
                exit_time=datetime.now(timezone.utc),
                exit_price=95.0,
                profit_loss=-50.0,
                trade_type="LONG",
                status="CLOSED"
            )
            db_session.add(trade)
            db_session.commit()
            db_session.refresh(trade)

            loss_detector.track_trade_outcome(trade.id)

            if i == 2:  # After 3rd loss
                if loss_detector.check_loss_limit(sample_strategy.id):
                    loss_detector.pause_strategy_on_limit(sample_strategy.id)

        # Verify paused
        db_session.refresh(sample_strategy)
        assert sample_strategy.status == "paused"
        assert sample_strategy.consecutive_losses_today == 3

        # Resume and simulate win
        sample_strategy.status = "active"
        db_session.commit()

        win_trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            exit_time=datetime.now(timezone.utc),
            exit_price=110.0,
            profit_loss=100.0,
            trade_type="LONG",
            status="CLOSED"
        )
        db_session.add(win_trade)
        db_session.commit()
        db_session.refresh(win_trade)

        loss_detector.track_trade_outcome(win_trade.id)

        # Verify reset
        db_session.refresh(sample_strategy)
        assert sample_strategy.consecutive_losses_today == 0
