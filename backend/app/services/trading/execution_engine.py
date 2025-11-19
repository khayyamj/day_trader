"""Trade execution engine coordinating signal execution with risk management."""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.services.trading.ibkr_client import IBKRClient
from app.services.trading.order_service import OrderService
from app.services.risk.position_sizer import PositionSizer
from app.services.risk.risk_manager import RiskManager
from app.services.strategies.base_strategy import TradingSignal, SignalType, BaseStrategy
from app.models.trade import Trade
from app.models.stock import Stock
from app.models.order import Order

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Result of trade execution."""

    def __init__(
        self,
        success: bool,
        trade: Optional[Trade] = None,
        market_order: Optional[Order] = None,
        stop_loss_order: Optional[Order] = None,
        take_profit_order: Optional[Order] = None,
        error_message: Optional[str] = None
    ):
        """
        Initialize execution result.

        Args:
            success: Whether execution succeeded
            trade: Created trade record
            market_order: Market order
            stop_loss_order: Stop-loss order
            take_profit_order: Take-profit order
            error_message: Error message if failed
        """
        self.success = success
        self.trade = trade
        self.market_order = market_order
        self.stop_loss_order = stop_loss_order
        self.take_profit_order = take_profit_order
        self.error_message = error_message

    def __repr__(self):
        if self.success:
            return (
                f"<ExecutionResult(success=True, trade_id={self.trade.id if self.trade else None})>"
            )
        return f"<ExecutionResult(success=False, error='{self.error_message}')>"


class ExecutionEngine:
    """
    Trade execution engine that coordinates signal execution.

    Flow:
    1. Receive trading signal
    2. Validate trade with RiskManager
    3. Calculate position size with PositionSizer
    4. Submit market order
    5. Wait for fill
    6. Submit stop-loss order at broker
    7. Submit take-profit order at broker
    8. Log trade to database
    """

    def __init__(
        self,
        ibkr_client: IBKRClient,
        order_service: OrderService,
        position_sizer: PositionSizer,
        risk_manager: RiskManager,
        db: Session
    ):
        """
        Initialize ExecutionEngine.

        Args:
            ibkr_client: Configured IBKRClient instance
            order_service: OrderService instance
            position_sizer: PositionSizer instance
            risk_manager: RiskManager instance
            db: Database session
        """
        self.ibkr_client = ibkr_client
        self.order_service = order_service
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.db = db

        logger.info("ExecutionEngine initialized")

    def execute_signal(
        self,
        signal: TradingSignal,
        strategy: BaseStrategy,
        strategy_id: int
    ) -> ExecutionResult:
        """
        Execute trading signal with full risk management.

        Args:
            signal: Trading signal to execute
            strategy: Strategy instance for price calculations
            strategy_id: Database strategy ID

        Returns:
            ExecutionResult: Result of execution attempt
        """
        logger.info("=" * 60)
        logger.info("TRADE EXECUTION")
        logger.info("=" * 60)
        logger.info(f"Signal: {signal.signal_type.value.upper()}")
        logger.info(f"Symbol: {signal.symbol}")
        logger.info(f"Strategy ID: {strategy_id}")
        logger.info(f"Reason: {signal.trigger_reason}")
        logger.info("-" * 60)

        # Only execute BUY signals (we don't handle SELL/HOLD)
        if signal.signal_type != SignalType.BUY:
            error_msg = f"Signal type not supported for execution: {signal.signal_type.value}"
            logger.warning(error_msg)
            return ExecutionResult(success=False, error_message=error_msg)

        try:
            # Get stock from database
            stock = self.db.query(Stock).filter(
                Stock.symbol == signal.symbol
            ).first()

            if not stock:
                error_msg = f"Stock not found in database: {signal.symbol}"
                logger.error(error_msg)
                return ExecutionResult(success=False, error_message=error_msg)

            # Get current market price
            current_price = self._get_current_price(signal.symbol)
            if not current_price:
                error_msg = f"Unable to get current price for {signal.symbol}"
                logger.error(error_msg)
                return ExecutionResult(success=False, error_message=error_msg)

            logger.info(f"Current price: ${current_price:.2f}")

            # Calculate stop-loss and take-profit prices
            stop_loss_price = strategy.calculate_stop_loss_price(current_price)
            take_profit_price = strategy.calculate_take_profit_price(current_price)

            logger.info(f"Stop loss: ${stop_loss_price:.2f}")
            logger.info(f"Take profit: ${take_profit_price:.2f}")

            # Calculate position size
            position_size = self.position_sizer.calculate_position_size(
                entry_price=current_price,
                stop_loss=stop_loss_price
            )

            logger.info(
                f"Position size: {position_size['quantity']} shares "
                f"= ${position_size['position_value']:,.2f}"
            )

            # Validate trade with risk manager
            validation = self.risk_manager.validate_trade(
                strategy_id=strategy_id,
                symbol=signal.symbol,
                position_size=position_size
            )

            if not validation.is_valid:
                logger.error(f"Trade validation failed: {validation.reason}")
                return ExecutionResult(
                    success=False,
                    error_message=f"Risk validation failed: {validation.reason}"
                )

            # Submit market order
            logger.info("-" * 60)
            logger.info("Submitting market order...")

            market_order = self.order_service.submit_market_order(
                symbol=signal.symbol,
                quantity=position_size['quantity'],
                action='BUY',
                stock_id=stock.id
            )

            logger.info(
                f"Market order submitted: order_id={market_order.id}, "
                f"broker_order_id={market_order.broker_order_id}"
            )

            # Wait for market order to fill
            logger.info("Waiting for market order fill...")
            fill_price = self._wait_for_fill(market_order)

            if not fill_price:
                error_msg = "Market order did not fill in expected time"
                logger.error(error_msg)
                return ExecutionResult(
                    success=False,
                    market_order=market_order,
                    error_message=error_msg
                )

            logger.info(f"Market order filled at ${fill_price:.2f}")

            # Create trade record
            trade = Trade(
                strategy_id=strategy_id,
                stock_id=stock.id,
                entry_time=datetime.now(timezone.utc),
                entry_price=fill_price,
                quantity=position_size['quantity'],
                trade_type='LONG',
                status='OPEN',
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
                market_context={
                    'signal_reason': signal.trigger_reason,
                    'indicator_values': signal.indicator_values,
                    'position_sizing': {
                        'risk_amount': position_size['risk_amount'],
                        'risk_percent': position_size['risk_percent'],
                        'position_percent': position_size['position_percent']
                    }
                }
            )

            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)

            # Update market order with trade_id
            market_order.trade_id = trade.id
            self.db.commit()

            logger.info(f"Trade created: trade_id={trade.id}")

            # Submit stop-loss order at broker level
            logger.info("-" * 60)
            logger.info("Submitting stop-loss order at broker level...")

            stop_loss_order = self.order_service.submit_stop_loss_order(
                symbol=signal.symbol,
                quantity=position_size['quantity'],
                stop_price=stop_loss_price,
                stock_id=stock.id,
                trade_id=trade.id
            )

            logger.info(
                f"Stop-loss order placed: order_id={stop_loss_order.id}, "
                f"broker_order_id={stop_loss_order.broker_order_id}"
            )

            # Submit take-profit order at broker level
            logger.info("Submitting take-profit order at broker level...")

            take_profit_order = self.order_service.submit_take_profit_order(
                symbol=signal.symbol,
                quantity=position_size['quantity'],
                limit_price=take_profit_price,
                stock_id=stock.id,
                trade_id=trade.id
            )

            logger.info(
                f"Take-profit order placed: order_id={take_profit_order.id}, "
                f"broker_order_id={take_profit_order.broker_order_id}"
            )

            logger.info("=" * 60)
            logger.info("✓ TRADE EXECUTION COMPLETE")
            logger.info(f"Trade ID: {trade.id}")
            logger.info(f"Entry: ${fill_price:.2f} x {position_size['quantity']} shares")
            logger.info(f"Stop Loss: ${stop_loss_price:.2f}")
            logger.info(f"Take Profit: ${take_profit_price:.2f}")
            logger.info("=" * 60)

            return ExecutionResult(
                success=True,
                trade=trade,
                market_order=market_order,
                stop_loss_order=stop_loss_order,
                take_profit_order=take_profit_order
            )

        except Exception as e:
            error_msg = f"Trade execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.db.rollback()
            return ExecutionResult(success=False, error_message=error_msg)

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for symbol.

        Args:
            symbol: Stock symbol

        Returns:
            float: Current price or None if unavailable
        """
        try:
            contract = self.ibkr_client.create_stock_contract(symbol)
            ticker = self.ibkr_client.ib.reqMktData(contract, '', False, False)
            self.ibkr_client.ib.sleep(2)  # Wait for market data

            # Get last price or use mid price
            if ticker.last and ticker.last > 0:
                price = ticker.last
            elif ticker.bid and ticker.ask:
                price = (ticker.bid + ticker.ask) / 2
            else:
                logger.error(f"No price data available for {symbol}")
                return None

            self.ibkr_client.ib.cancelMktData(contract)
            return float(price)

        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {str(e)}")
            return None

    def _wait_for_fill(
        self,
        order: Order,
        timeout_seconds: int = 30
    ) -> Optional[float]:
        """
        Wait for order to fill and return fill price.

        Args:
            order: Order to monitor
            timeout_seconds: Maximum wait time in seconds

        Returns:
            float: Fill price or None if timeout
        """
        try:
            # Get IBKR trade object
            broker_order_id = int(order.broker_order_id)

            # Poll for fill status
            elapsed = 0
            poll_interval = 1  # Poll every second

            while elapsed < timeout_seconds:
                self.ibkr_client.ib.sleep(poll_interval)
                elapsed += poll_interval

                # Check order status through IBKR
                trades = self.ibkr_client.ib.trades()
                for trade in trades:
                    if trade.order.orderId == broker_order_id:
                        if trade.orderStatus.status == 'Filled':
                            # Update order status in database
                            order.status = 'FILLED'
                            order.filled_at = datetime.now(timezone.utc)
                            order.filled_price = trade.orderStatus.avgFillPrice
                            order.filled_quantity = trade.orderStatus.filled
                            self.db.commit()

                            return float(trade.orderStatus.avgFillPrice)

            logger.warning(f"Order {order.broker_order_id} did not fill within {timeout_seconds}s")
            return None

        except Exception as e:
            logger.error(f"Error waiting for fill: {str(e)}")
            return None

    def monitor_protective_orders(self, trade_id: int) -> None:
        """
        Monitor stop-loss and take-profit orders for a trade.

        Updates trade record when protective orders are filled.

        Args:
            trade_id: Trade ID to monitor

        Note:
            This should be called periodically by a background task.
        """
        try:
            trade = self.db.query(Trade).filter(Trade.id == trade_id).first()

            if not trade or trade.status != 'OPEN':
                return

            # Get orders for this trade
            orders = self.db.query(Order).filter(
                Order.trade_id == trade_id,
                Order.status == 'PENDING'
            ).all()

            # Check each order status
            for order in orders:
                broker_order_id = int(order.broker_order_id)
                trades = self.ibkr_client.ib.trades()

                for ibkr_trade in trades:
                    if ibkr_trade.order.orderId == broker_order_id:
                        if ibkr_trade.orderStatus.status == 'Filled':
                            # Order filled - update order record
                            order.status = 'FILLED'
                            order.filled_at = datetime.now(timezone.utc)
                            order.filled_price = ibkr_trade.orderStatus.avgFillPrice
                            order.filled_quantity = ibkr_trade.orderStatus.filled

                            # Update trade record
                            trade.status = 'CLOSED'
                            trade.exit_time = datetime.now(timezone.utc)
                            trade.exit_price = ibkr_trade.orderStatus.avgFillPrice

                            # Calculate P&L
                            exit_value = float(trade.exit_price) * trade.quantity
                            entry_value = float(trade.entry_price) * trade.quantity
                            trade.profit_loss = exit_value - entry_value
                            trade.profit_loss_percent = (
                                (trade.profit_loss / entry_value) * 100
                            )

                            self.db.commit()

                            logger.info(
                                f"Trade {trade_id} closed via {order.order_type} order: "
                                f"P&L=${trade.profit_loss:.2f} "
                                f"({trade.profit_loss_percent:.2f}%)"
                            )

        except Exception as e:
            logger.error(f"Error monitoring protective orders: {str(e)}")
            self.db.rollback()
