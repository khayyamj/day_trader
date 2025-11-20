"""Tests for PositionService reconciliation."""
import pytest
from unittest.mock import Mock
from datetime import datetime, timezone

from app.services.trading.position_service import PositionService, PositionDiscrepancy
from app.models.stock import Stock
from app.models.trade import Trade
from app.models.strategy import Strategy


@pytest.fixture
def mock_ibkr_client():
    """Create mocked IBKR client."""
    client = Mock()
    client.is_connected = True

    # Mock empty positions by default
    client.get_positions = Mock(return_value=[])

    return client


@pytest.fixture
def sample_strategy(db_session):
    """Create sample strategy."""
    strategy = Strategy(name="Test Strategy", parameters={})
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
def position_service(mock_ibkr_client, db_session):
    """Create PositionService instance."""
    return PositionService(mock_ibkr_client, db_session)


class TestGetBrokerPositions:
    """Test getting positions from broker."""

    def test_get_broker_positions_empty(self, position_service):
        """Test getting positions when broker has none."""
        positions = position_service.get_broker_positions()

        assert positions == {}

    def test_get_broker_positions_with_data(self, position_service, mock_ibkr_client):
        """Test getting positions from broker."""
        # Mock broker positions
        mock_position = Mock()
        mock_position.contract.symbol = "AAPL"
        mock_position.position = 100
        mock_position.avgCost = 150.0

        mock_ibkr_client.get_positions.return_value = [mock_position]

        positions = position_service.get_broker_positions()

        assert "AAPL" in positions
        assert positions["AAPL"]["quantity"] == 100
        assert positions["AAPL"]["avg_cost"] == 150.0
        assert positions["AAPL"]["market_value"] == 15000.0

    def test_get_broker_positions_not_connected(self, position_service):
        """Test getting positions when not connected."""
        position_service.ibkr_client.is_connected = False

        with pytest.raises(ConnectionError, match="Not connected to IBKR"):
            position_service.get_broker_positions()


class TestGetDBPositions:
    """Test getting positions from database."""

    def test_get_db_positions_empty(self, position_service):
        """Test getting positions when database is empty."""
        positions = position_service.get_db_positions()

        assert positions == {}

    def test_get_db_positions_single_trade(self, position_service, sample_stock, sample_strategy, db_session):
        """Test getting position from single trade."""
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=50,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        positions = position_service.get_db_positions()

        assert "AAPL" in positions
        assert positions["AAPL"]["quantity"] == 50
        assert positions["AAPL"]["avg_cost"] == 100.0

    def test_get_db_positions_multiple_trades(self, position_service, sample_stock, sample_strategy, db_session):
        """Test aggregating multiple trades."""
        trades = [
            Trade(
                strategy_id=sample_strategy.id,
                stock_id=sample_stock.id,
                entry_time=datetime.now(timezone.utc),
                entry_price=100.0,
                quantity=30,
                trade_type="LONG",
                status="OPEN"
            ),
            Trade(
                strategy_id=sample_strategy.id,
                stock_id=sample_stock.id,
                entry_time=datetime.now(timezone.utc),
                entry_price=110.0,
                quantity=20,
                trade_type="LONG",
                status="OPEN"
            )
        ]

        for trade in trades:
            db_session.add(trade)
        db_session.commit()

        positions = position_service.get_db_positions()

        assert positions["AAPL"]["quantity"] == 50
        # Weighted average: (30*100 + 20*110) / 50 = 5200/50 = 104
        assert positions["AAPL"]["avg_cost"] == 104.0

    def test_get_db_positions_ignores_closed_trades(self, position_service, sample_stock, sample_strategy, db_session):
        """Test that closed trades are not included."""
        open_trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=30,
            trade_type="LONG",
            status="OPEN"
        )

        closed_trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=20,
            trade_type="LONG",
            status="CLOSED"
        )

        db_session.add(open_trade)
        db_session.add(closed_trade)
        db_session.commit()

        positions = position_service.get_db_positions()

        assert positions["AAPL"]["quantity"] == 30  # Only open trade


class TestReconcilePositions:
    """Test position reconciliation."""

    def test_reconcile_matching_positions(self, position_service, sample_stock, sample_strategy, mock_ibkr_client, db_session):
        """Test reconciliation when positions match."""
        # Create matching broker and DB positions
        mock_position = Mock()
        mock_position.contract.symbol = "AAPL"
        mock_position.position = 50
        mock_position.avgCost = 100.0
        mock_ibkr_client.get_positions.return_value = [mock_position]

        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=50,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        discrepancies, total_diff = position_service.reconcile_positions()

        assert len(discrepancies) == 0
        assert total_diff == 0.0

    def test_reconcile_extra_at_broker(self, position_service, mock_ibkr_client):
        """Test detecting position at broker not in database."""
        # Broker has position, DB doesn't
        mock_position = Mock()
        mock_position.contract.symbol = "AAPL"
        mock_position.position = 50
        mock_position.avgCost = 100.0
        mock_ibkr_client.get_positions.return_value = [mock_position]

        discrepancies, total_diff = position_service.reconcile_positions()

        assert len(discrepancies) == 1
        assert discrepancies[0].discrepancy_type == "EXTRA_AT_BROKER"
        assert discrepancies[0].symbol == "AAPL"
        assert discrepancies[0].broker_quantity == 50
        assert discrepancies[0].db_quantity == 0
        assert total_diff == 5000.0

    def test_reconcile_missing_at_broker(self, position_service, sample_stock, sample_strategy, db_session):
        """Test detecting position in database not at broker."""
        # DB has position, broker doesn't
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=50,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        discrepancies, total_diff = position_service.reconcile_positions()

        assert len(discrepancies) == 1
        assert discrepancies[0].discrepancy_type == "MISSING_AT_BROKER"
        assert discrepancies[0].symbol == "AAPL"
        assert discrepancies[0].broker_quantity == 0
        assert discrepancies[0].db_quantity == 50

    def test_reconcile_quantity_mismatch(self, position_service, sample_stock, sample_strategy, mock_ibkr_client, db_session):
        """Test detecting quantity mismatch."""
        # Broker has different quantity than DB
        mock_position = Mock()
        mock_position.contract.symbol = "AAPL"
        mock_position.position = 100
        mock_position.avgCost = 100.0
        mock_ibkr_client.get_positions.return_value = [mock_position]

        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=50,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        discrepancies, total_diff = position_service.reconcile_positions()

        assert len(discrepancies) == 1
        assert discrepancies[0].discrepancy_type == "QUANTITY_MISMATCH"
        assert discrepancies[0].broker_quantity == 100
        assert discrepancies[0].db_quantity == 50


class TestRecoveryLogic:
    """Test position recovery."""

    def test_recover_extra_position(self, position_service, sample_stock, sample_strategy, mock_ibkr_client, db_session):
        """Test recovering extra position at broker."""
        # Setup broker position
        mock_position = Mock()
        mock_position.contract.symbol = "AAPL"
        mock_position.position = 50
        mock_position.avgCost = 150.0
        mock_ibkr_client.get_positions.return_value = [mock_position]

        discrepancy = PositionDiscrepancy(
            symbol="AAPL",
            broker_quantity=50,
            db_quantity=0,
            value_difference=7500.0,
            discrepancy_type="EXTRA_AT_BROKER"
        )

        trade = position_service.recover_extra_position(discrepancy, sample_strategy.id)

        assert trade is not None
        assert trade.quantity == 50
        assert float(trade.entry_price) == 150.0
        assert trade.status == "OPEN"
        assert trade.market_context.get('recovered') is True

    def test_recover_missing_position(self, position_service, sample_stock, sample_strategy, db_session):
        """Test recovering missing position at broker."""
        # Create open trade in DB
        trade = Trade(
            strategy_id=sample_strategy.id,
            stock_id=sample_stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=50,
            trade_type="LONG",
            status="OPEN"
        )
        db_session.add(trade)
        db_session.commit()

        discrepancy = PositionDiscrepancy(
            symbol="AAPL",
            broker_quantity=0,
            db_quantity=50,
            value_difference=5000.0,
            discrepancy_type="MISSING_AT_BROKER"
        )

        position_service.recover_missing_position(discrepancy)

        # Check trade was closed
        db_session.refresh(trade)
        assert trade.status == "CLOSED"
        assert trade.market_context.get('recovered') is True


class TestMajorDiscrepancy:
    """Test major discrepancy detection."""

    def test_check_major_discrepancy_under_threshold(self, position_service):
        """Test discrepancy under $100 threshold."""
        is_major = position_service.check_major_discrepancy(50.0)

        assert is_major is False

    def test_check_major_discrepancy_over_threshold(self, position_service):
        """Test discrepancy over $100 threshold."""
        is_major = position_service.check_major_discrepancy(250.0)

        assert is_major is True

    def test_check_major_discrepancy_exactly_at_threshold(self, position_service):
        """Test discrepancy exactly at threshold."""
        is_major = position_service.check_major_discrepancy(100.0)

        assert is_major is False

    def test_check_major_discrepancy_custom_threshold(self, position_service):
        """Test with custom threshold."""
        is_major = position_service.check_major_discrepancy(150.0, threshold=200.0)

        assert is_major is False
