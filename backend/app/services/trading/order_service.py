"""Order submission and tracking service for IBKR trading."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ib_insync import MarketOrder, StopOrder, LimitOrder, Trade as IBKRTrade

from app.services.trading.ibkr_client import IBKRClient
from app.models.order import Order
from app.models.stock import Stock

logger = logging.getLogger(__name__)


class OrderService:
    """
    Service for submitting and tracking orders through IBKR.

    Handles order submission, status tracking, and database persistence.
    """

    def __init__(self, ibkr_client: IBKRClient, db: Session):
        """
        Initialize OrderService.

        Args:
            ibkr_client: Configured IBKRClient instance
            db: Database session
        """
        self.ibkr_client = ibkr_client
        self.db = db
        self._order_tracking: Dict[int, IBKRTrade] = {}  # Trade ID -> IBKRTrade

        logger.info("OrderService initialized")

    def submit_market_order(
        self,
        symbol: str,
        quantity: int,
        action: str,
        stock_id: int,
        trade_id: Optional[int] = None
    ) -> Order:
        """
        Submit a market order to IBKR.

        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares
            action: Order action ('BUY' or 'SELL')
            stock_id: Database stock ID
            trade_id: Optional trade ID for linking

        Returns:
            Order: Created order object with broker_order_id

        Raises:
            ConnectionError: If not connected to IBKR
            ValueError: If order submission fails
        """
        if not self.ibkr_client.is_connected:
            raise ConnectionError("Not connected to IBKR")

        if action.upper() not in ['BUY', 'SELL']:
            raise ValueError(f"Invalid action: {action}. Must be 'BUY' or 'SELL'")

        logger.info(
            f"Submitting market order: {action} {quantity} shares of {symbol}"
        )

        try:
            # Create stock contract
            contract = self.ibkr_client.create_stock_contract(symbol)

            # Create market order
            order = MarketOrder(action.upper(), quantity)

            # Place order through IBKR
            trade = self.ibkr_client.ib.placeOrder(contract, order)

            # Wait a moment for order to be acknowledged
            self.ibkr_client.ib.sleep(0.5)

            # Create database order record
            db_order = Order(
                trade_id=trade_id,
                stock_id=stock_id,
                order_type="MARKET",
                side=action.upper(),
                quantity=quantity,
                status="PENDING",
                broker_order_id=str(trade.order.orderId) if trade.order else None,
                submitted_at=datetime.now(timezone.utc)
            )

            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)

            # Track order for status updates
            if trade.order:
                self._order_tracking[trade.order.orderId] = trade

            logger.info(
                f"Market order submitted successfully: "
                f"order_id={db_order.id}, broker_order_id={db_order.broker_order_id}"
            )

            return db_order

        except Exception as e:
            logger.error(f"Failed to submit market order: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Order submission failed: {str(e)}")

    def submit_stop_loss_order(
        self,
        symbol: str,
        quantity: int,
        stop_price: float,
        stock_id: int,
        trade_id: Optional[int] = None
    ) -> Order:
        """
        Submit a stop-loss order to IBKR (placed at broker level).

        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares
            stop_price: Stop loss trigger price
            stock_id: Database stock ID
            trade_id: Optional trade ID for linking

        Returns:
            Order: Created stop-loss order object

        Raises:
            ConnectionError: If not connected to IBKR
            ValueError: If order submission fails
        """
        if not self.ibkr_client.is_connected:
            raise ConnectionError("Not connected to IBKR")

        logger.info(
            f"Submitting stop-loss order: SELL {quantity} shares of {symbol} "
            f"at stop ${stop_price:.2f}"
        )

        try:
            # Create stock contract
            contract = self.ibkr_client.create_stock_contract(symbol)

            # Create stop order (always SELL for stop-loss)
            order = StopOrder('SELL', quantity, stop_price)

            # Place order through IBKR
            trade = self.ibkr_client.ib.placeOrder(contract, order)

            # Wait a moment for order to be acknowledged
            self.ibkr_client.ib.sleep(0.5)

            # Create database order record
            db_order = Order(
                trade_id=trade_id,
                stock_id=stock_id,
                order_type="STOP",
                side="SELL",
                quantity=quantity,
                stop_price=stop_price,
                status="PENDING",
                broker_order_id=str(trade.order.orderId) if trade.order else None,
                submitted_at=datetime.now(timezone.utc)
            )

            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)

            # Track order for status updates
            if trade.order:
                self._order_tracking[trade.order.orderId] = trade

            logger.info(
                f"Stop-loss order submitted successfully: "
                f"order_id={db_order.id}, broker_order_id={db_order.broker_order_id}"
            )

            return db_order

        except Exception as e:
            logger.error(f"Failed to submit stop-loss order: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Stop-loss order submission failed: {str(e)}")

    def submit_take_profit_order(
        self,
        symbol: str,
        quantity: int,
        limit_price: float,
        stock_id: int,
        trade_id: Optional[int] = None
    ) -> Order:
        """
        Submit a take-profit (limit) order to IBKR.

        Args:
            symbol: Stock ticker symbol
            quantity: Number of shares
            limit_price: Target profit price
            stock_id: Database stock ID
            trade_id: Optional trade ID for linking

        Returns:
            Order: Created take-profit order object

        Raises:
            ConnectionError: If not connected to IBKR
            ValueError: If order submission fails
        """
        if not self.ibkr_client.is_connected:
            raise ConnectionError("Not connected to IBKR")

        logger.info(
            f"Submitting take-profit order: SELL {quantity} shares of {symbol} "
            f"at limit ${limit_price:.2f}"
        )

        try:
            # Create stock contract
            contract = self.ibkr_client.create_stock_contract(symbol)

            # Create limit order (always SELL for take-profit)
            order = LimitOrder('SELL', quantity, limit_price)

            # Place order through IBKR
            trade = self.ibkr_client.ib.placeOrder(contract, order)

            # Wait a moment for order to be acknowledged
            self.ibkr_client.ib.sleep(0.5)

            # Create database order record
            db_order = Order(
                trade_id=trade_id,
                stock_id=stock_id,
                order_type="LIMIT",
                side="SELL",
                quantity=quantity,
                limit_price=limit_price,
                status="PENDING",
                broker_order_id=str(trade.order.orderId) if trade.order else None,
                submitted_at=datetime.now(timezone.utc)
            )

            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)

            # Track order for status updates
            if trade.order:
                self._order_tracking[trade.order.orderId] = trade

            logger.info(
                f"Take-profit order submitted successfully: "
                f"order_id={db_order.id}, broker_order_id={db_order.broker_order_id}"
            )

            return db_order

        except Exception as e:
            logger.error(f"Failed to submit take-profit order: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Take-profit order submission failed: {str(e)}")

    def update_order_status(self, broker_order_id: str) -> Optional[Order]:
        """
        Update order status from IBKR.

        Args:
            broker_order_id: Broker-assigned order ID

        Returns:
            Order: Updated order object, or None if not found
        """
        # Find order in database
        db_order = self.db.query(Order).filter(
            Order.broker_order_id == broker_order_id
        ).first()

        if not db_order:
            logger.warning(f"Order not found: broker_order_id={broker_order_id}")
            return None

        try:
            order_id = int(broker_order_id)

            # Get trade from tracking or IBKR
            if order_id in self._order_tracking:
                trade = self._order_tracking[order_id]
            else:
                # Query IBKR for trade status
                trades = self.ibkr_client.ib.trades()
                trade = next(
                    (t for t in trades if t.order.orderId == order_id),
                    None
                )

            if not trade:
                logger.warning(f"Trade not found in IBKR: order_id={order_id}")
                return db_order

            # Update order status based on IBKR status
            order_status = trade.orderStatus.status

            if order_status == 'Filled':
                db_order.status = 'FILLED'
                db_order.filled_at = datetime.now(timezone.utc)
                db_order.filled_price = trade.orderStatus.avgFillPrice
            elif order_status == 'Cancelled':
                db_order.status = 'CANCELLED'
            elif order_status in ['ApiCancelled', 'Inactive']:
                db_order.status = 'CANCELLED'
            elif order_status == 'Submitted':
                db_order.status = 'PENDING'
            else:
                logger.debug(f"Order status: {order_status}")

            self.db.commit()
            self.db.refresh(db_order)

            logger.info(
                f"Order status updated: order_id={db_order.id}, "
                f"status={db_order.status}"
            )

            return db_order

        except Exception as e:
            logger.error(f"Failed to update order status: {str(e)}")
            self.db.rollback()
            return db_order

    def get_pending_orders(self) -> list[Order]:
        """
        Get all pending orders from database.

        Returns:
            list[Order]: List of pending orders
        """
        return self.db.query(Order).filter(
            Order.status == 'PENDING'
        ).all()

    def monitor_orders(self) -> None:
        """
        Monitor and update status of all pending orders.

        Should be called periodically (e.g., every 30 seconds).
        """
        pending_orders = self.get_pending_orders()

        if not pending_orders:
            return

        logger.info(f"Monitoring {len(pending_orders)} pending orders")

        for order in pending_orders:
            if order.broker_order_id:
                try:
                    self.update_order_status(order.broker_order_id)
                except Exception as e:
                    logger.error(
                        f"Failed to update order {order.id}: {str(e)}"
                    )
