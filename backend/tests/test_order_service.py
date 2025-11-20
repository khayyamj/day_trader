"""Tests for OrderService with mocked IBKR client."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from ib_insync import MarketOrder, StopOrder, LimitOrder, Trade as IBKRTrade

from app.services.trading.order_service import OrderService
from app.models.stock import Stock
from app.models.order import Order


@pytest.fixture
def mock_ibkr_client():
    """Create a mocked IBKR client."""
    client = Mock()
    client.is_connected = True
    client.ib = Mock()
    client.create_stock_contract = Mock(return_value=Mock(symbol="AAPL"))
    return client


@pytest.fixture
def sample_stock(db_session):
    """Create a sample stock in the database."""
    stock = Stock(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ")
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


@pytest.fixture
def order_service(mock_ibkr_client, db_session):
    """Create OrderService instance with mocked client."""
    return OrderService(mock_ibkr_client, db_session)


class TestOrderServiceMarketOrders:
    """Test market order submission."""

    def test_submit_market_order_buy(self, order_service, sample_stock, mock_ibkr_client):
        """Test submitting a BUY market order."""
        # Setup mock
        mock_trade = Mock()
        mock_trade.order = Mock()
        mock_trade.order.orderId = 12345
        mock_ibkr_client.ib.placeOrder.return_value = mock_trade
        mock_ibkr_client.ib.sleep = Mock()

        # Submit order
        order = order_service.submit_market_order(
            symbol="AAPL",
            quantity=10,
            action="BUY",
            stock_id=sample_stock.id
        )

        # Assertions
        assert order is not None
        assert order.order_type == "MARKET"
        assert order.side == "BUY"
        assert order.quantity == 10
        assert order.status == "PENDING"
        assert order.broker_order_id == "12345"
        assert order.stock_id == sample_stock.id

        # Verify placeOrder was called
        mock_ibkr_client.ib.placeOrder.assert_called_once()

    def test_submit_market_order_sell(self, order_service, sample_stock, mock_ibkr_client):
        """Test submitting a SELL market order."""
        # Setup mock
        mock_trade = Mock()
        mock_trade.order = Mock()
        mock_trade.order.orderId = 54321
        mock_ibkr_client.ib.placeOrder.return_value = mock_trade
        mock_ibkr_client.ib.sleep = Mock()

        # Submit order
        order = order_service.submit_market_order(
            symbol="AAPL",
            quantity=5,
            action="SELL",
            stock_id=sample_stock.id
        )

        # Assertions
        assert order.side == "SELL"
        assert order.quantity == 5
        assert order.broker_order_id == "54321"

    def test_submit_market_order_not_connected(self, order_service, sample_stock):
        """Test market order submission when not connected."""
        order_service.ibkr_client.is_connected = False

        with pytest.raises(ConnectionError, match="Not connected to IBKR"):
            order_service.submit_market_order(
                symbol="AAPL",
                quantity=10,
                action="BUY",
                stock_id=sample_stock.id
            )

    def test_submit_market_order_invalid_action(self, order_service, sample_stock):
        """Test market order with invalid action."""
        with pytest.raises(ValueError, match="Invalid action"):
            order_service.submit_market_order(
                symbol="AAPL",
                quantity=10,
                action="HOLD",
                stock_id=sample_stock.id
            )


class TestOrderServiceStopLossOrders:
    """Test stop-loss order submission."""

    def test_submit_stop_loss_order(self, order_service, sample_stock, mock_ibkr_client):
        """Test submitting a stop-loss order."""
        # Setup mock
        mock_trade = Mock()
        mock_trade.order = Mock()
        mock_trade.order.orderId = 99999
        mock_ibkr_client.ib.placeOrder.return_value = mock_trade
        mock_ibkr_client.ib.sleep = Mock()

        # Submit stop-loss order
        order = order_service.submit_stop_loss_order(
            symbol="AAPL",
            quantity=10,
            stop_price=95.00,
            stock_id=sample_stock.id
        )

        # Assertions
        assert order.order_type == "STOP"
        assert order.side == "SELL"  # Stop-loss is always SELL
        assert order.quantity == 10
        assert float(order.stop_price) == 95.00
        assert order.status == "PENDING"
        assert order.broker_order_id == "99999"

    def test_submit_stop_loss_not_connected(self, order_service, sample_stock):
        """Test stop-loss order when not connected."""
        order_service.ibkr_client.is_connected = False

        with pytest.raises(ConnectionError):
            order_service.submit_stop_loss_order(
                symbol="AAPL",
                quantity=10,
                stop_price=95.00,
                stock_id=sample_stock.id
            )


class TestOrderServiceTakeProfitOrders:
    """Test take-profit order submission."""

    def test_submit_take_profit_order(self, order_service, sample_stock, mock_ibkr_client):
        """Test submitting a take-profit order."""
        # Setup mock
        mock_trade = Mock()
        mock_trade.order = Mock()
        mock_trade.order.orderId = 88888
        mock_ibkr_client.ib.placeOrder.return_value = mock_trade
        mock_ibkr_client.ib.sleep = Mock()

        # Submit take-profit order
        order = order_service.submit_take_profit_order(
            symbol="AAPL",
            quantity=10,
            limit_price=110.00,
            stock_id=sample_stock.id
        )

        # Assertions
        assert order.order_type == "LIMIT"
        assert order.side == "SELL"  # Take-profit is always SELL
        assert order.quantity == 10
        assert float(order.limit_price) == 110.00
        assert order.status == "PENDING"
        assert order.broker_order_id == "88888"

    def test_submit_take_profit_with_trade_id(self, order_service, sample_stock, mock_ibkr_client):
        """Test submitting take-profit with trade_id."""
        # Setup mock
        mock_trade = Mock()
        mock_trade.order = Mock()
        mock_trade.order.orderId = 77777
        mock_ibkr_client.ib.placeOrder.return_value = mock_trade
        mock_ibkr_client.ib.sleep = Mock()

        # Submit order with trade_id
        order = order_service.submit_take_profit_order(
            symbol="AAPL",
            quantity=10,
            limit_price=110.00,
            stock_id=sample_stock.id,
            trade_id=123
        )

        # Assertions
        assert order.trade_id == 123


class TestOrderServiceDatabase:
    """Test order database operations."""

    def test_order_persisted_to_database(self, order_service, sample_stock, mock_ibkr_client, db_session):
        """Test that orders are saved to database."""
        # Setup mock
        mock_trade = Mock()
        mock_trade.order = Mock()
        mock_trade.order.orderId = 11111
        mock_ibkr_client.ib.placeOrder.return_value = mock_trade
        mock_ibkr_client.ib.sleep = Mock()

        # Submit order
        order = order_service.submit_market_order(
            symbol="AAPL",
            quantity=10,
            action="BUY",
            stock_id=sample_stock.id
        )

        # Query database
        db_order = db_session.query(Order).filter(Order.id == order.id).first()

        assert db_order is not None
        assert db_order.broker_order_id == "11111"
        assert db_order.quantity == 10

    def test_multiple_orders_tracked(self, order_service, sample_stock, mock_ibkr_client, db_session):
        """Test that multiple orders are tracked."""
        # Setup mocks
        mock_trade1 = Mock()
        mock_trade1.order = Mock(orderId=1001)
        mock_trade2 = Mock()
        mock_trade2.order = Mock(orderId=1002)

        mock_ibkr_client.ib.placeOrder.side_effect = [mock_trade1, mock_trade2]
        mock_ibkr_client.ib.sleep = Mock()

        # Submit two orders
        order1 = order_service.submit_market_order(
            symbol="AAPL",
            quantity=10,
            action="BUY",
            stock_id=sample_stock.id
        )

        order2 = order_service.submit_market_order(
            symbol="AAPL",
            quantity=5,
            action="SELL",
            stock_id=sample_stock.id
        )

        # Check database
        orders = db_session.query(Order).all()
        assert len(orders) == 2
        assert order1.broker_order_id == "1001"
        assert order2.broker_order_id == "1002"
