"""Position management and reconciliation service."""
import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.services.trading.ibkr_client import IBKRClient
from app.models.trade import Trade
from app.models.stock import Stock

logger = logging.getLogger(__name__)


class PositionDiscrepancy:
    """Represents a discrepancy between broker and database positions."""

    def __init__(
        self,
        symbol: str,
        broker_quantity: int,
        db_quantity: int,
        value_difference: float,
        discrepancy_type: str
    ):
        """
        Initialize position discrepancy.

        Args:
            symbol: Stock symbol
            broker_quantity: Quantity at broker
            db_quantity: Quantity in database
            value_difference: Dollar value of discrepancy
            discrepancy_type: Type of discrepancy (EXTRA_AT_BROKER, MISSING_AT_BROKER, QUANTITY_MISMATCH)
        """
        self.symbol = symbol
        self.broker_quantity = broker_quantity
        self.db_quantity = db_quantity
        self.value_difference = value_difference
        self.discrepancy_type = discrepancy_type

    def __repr__(self):
        return (
            f"<PositionDiscrepancy(symbol='{self.symbol}', "
            f"broker={self.broker_quantity}, db={self.db_quantity}, "
            f"type='{self.discrepancy_type}')>"
        )


class PositionService:
    """
    Service for position management and reconciliation.

    Compares broker positions with database positions and handles discrepancies.
    """

    def __init__(self, ibkr_client: IBKRClient, db: Session):
        """
        Initialize PositionService.

        Args:
            ibkr_client: Configured IBKRClient instance
            db: Database session
        """
        self.ibkr_client = ibkr_client
        self.db = db

        logger.info("PositionService initialized")

    def get_broker_positions(self) -> Dict[str, Dict]:
        """
        Get current positions from IBKR broker.

        Returns:
            dict: Dictionary mapping symbol to position data
                  {symbol: {quantity: int, avg_cost: float, market_value: float}}

        Raises:
            ConnectionError: If not connected to IBKR
        """
        if not self.ibkr_client.is_connected:
            raise ConnectionError("Not connected to IBKR")

        logger.info("Retrieving positions from IBKR broker")

        try:
            positions = self.ibkr_client.get_positions()
            broker_positions = {}

            for position in positions:
                symbol = position.contract.symbol
                broker_positions[symbol] = {
                    'quantity': int(position.position),
                    'avg_cost': float(position.avgCost),
                    'market_value': float(position.position * position.avgCost)
                }

            logger.info(f"Retrieved {len(broker_positions)} positions from broker")
            return broker_positions

        except Exception as e:
            logger.error(f"Failed to get broker positions: {str(e)}")
            raise

    def get_db_positions(self) -> Dict[str, Dict]:
        """
        Get open positions from database (trades table).

        Returns:
            dict: Dictionary mapping symbol to position data
                  {symbol: {quantity: int, avg_cost: float, trade_ids: list}}
        """
        logger.info("Retrieving positions from database")

        try:
            # Get all open trades
            open_trades = self.db.query(Trade).filter(
                Trade.status == 'OPEN'
            ).all()

            db_positions = {}

            for trade in open_trades:
                # Get stock symbol
                stock = self.db.query(Stock).filter(
                    Stock.id == trade.stock_id
                ).first()

                if not stock:
                    logger.warning(f"Stock not found for trade {trade.id}")
                    continue

                symbol = stock.symbol

                if symbol not in db_positions:
                    db_positions[symbol] = {
                        'quantity': 0,
                        'total_cost': 0.0,
                        'trade_ids': []
                    }

                # Aggregate position data
                db_positions[symbol]['quantity'] += trade.quantity
                db_positions[symbol]['total_cost'] += float(trade.entry_price) * trade.quantity
                db_positions[symbol]['trade_ids'].append(trade.id)

            # Calculate average cost
            for symbol in db_positions:
                if db_positions[symbol]['quantity'] > 0:
                    db_positions[symbol]['avg_cost'] = (
                        db_positions[symbol]['total_cost'] / db_positions[symbol]['quantity']
                    )
                else:
                    db_positions[symbol]['avg_cost'] = 0.0

            logger.info(f"Retrieved {len(db_positions)} positions from database")
            return db_positions

        except Exception as e:
            logger.error(f"Failed to get database positions: {str(e)}")
            raise

    def reconcile_positions(self) -> Tuple[List[PositionDiscrepancy], float]:
        """
        Compare broker positions with database positions and identify discrepancies.

        Returns:
            tuple: (list of discrepancies, total value difference)

        Raises:
            ConnectionError: If not connected to IBKR
        """
        logger.info("Starting position reconciliation")

        try:
            broker_positions = self.get_broker_positions()
            db_positions = self.get_db_positions()

            discrepancies = []
            total_value_diff = 0.0

            # Check for positions at broker not in database
            for symbol, broker_data in broker_positions.items():
                db_data = db_positions.get(symbol, {'quantity': 0, 'avg_cost': 0})

                if db_data['quantity'] == 0:
                    # Extra position at broker
                    value_diff = broker_data['market_value']
                    discrepancies.append(
                        PositionDiscrepancy(
                            symbol=symbol,
                            broker_quantity=broker_data['quantity'],
                            db_quantity=0,
                            value_difference=value_diff,
                            discrepancy_type='EXTRA_AT_BROKER'
                        )
                    )
                    total_value_diff += abs(value_diff)
                    logger.warning(
                        f"Extra position at broker: {symbol} "
                        f"(broker: {broker_data['quantity']}, db: 0)"
                    )

                elif db_data['quantity'] != broker_data['quantity']:
                    # Quantity mismatch
                    value_diff = (broker_data['quantity'] - db_data['quantity']) * broker_data['avg_cost']
                    discrepancies.append(
                        PositionDiscrepancy(
                            symbol=symbol,
                            broker_quantity=broker_data['quantity'],
                            db_quantity=db_data['quantity'],
                            value_difference=value_diff,
                            discrepancy_type='QUANTITY_MISMATCH'
                        )
                    )
                    total_value_diff += abs(value_diff)
                    logger.warning(
                        f"Quantity mismatch for {symbol}: "
                        f"broker={broker_data['quantity']}, db={db_data['quantity']}"
                    )

            # Check for positions in database not at broker
            for symbol, db_data in db_positions.items():
                if symbol not in broker_positions:
                    # Position missing at broker
                    value_diff = db_data['total_cost']
                    discrepancies.append(
                        PositionDiscrepancy(
                            symbol=symbol,
                            broker_quantity=0,
                            db_quantity=db_data['quantity'],
                            value_difference=value_diff,
                            discrepancy_type='MISSING_AT_BROKER'
                        )
                    )
                    total_value_diff += abs(value_diff)
                    logger.warning(
                        f"Position missing at broker: {symbol} "
                        f"(broker: 0, db: {db_data['quantity']})"
                    )

            if not discrepancies:
                logger.info("✓ Position reconciliation successful - no discrepancies")
            else:
                logger.warning(
                    f"Position reconciliation found {len(discrepancies)} discrepancies, "
                    f"total value difference: ${total_value_diff:,.2f}"
                )

            return discrepancies, total_value_diff

        except Exception as e:
            logger.error(f"Position reconciliation failed: {str(e)}")
            raise

    def recover_extra_position(
        self,
        discrepancy: PositionDiscrepancy,
        strategy_id: int
    ) -> Trade:
        """
        Add missing trade to database for extra position at broker.

        Args:
            discrepancy: Position discrepancy with EXTRA_AT_BROKER type
            strategy_id: Strategy ID to associate with trade

        Returns:
            Trade: Created trade record

        Raises:
            ValueError: If discrepancy type is not EXTRA_AT_BROKER
        """
        if discrepancy.discrepancy_type != 'EXTRA_AT_BROKER':
            raise ValueError(
                f"Invalid discrepancy type: {discrepancy.discrepancy_type}. "
                "Expected EXTRA_AT_BROKER"
            )

        logger.warning(
            f"Recovering extra position: {discrepancy.symbol} "
            f"({discrepancy.broker_quantity} shares)"
        )

        try:
            # Get or create stock
            stock = self.db.query(Stock).filter(
                Stock.symbol == discrepancy.symbol
            ).first()

            if not stock:
                logger.error(f"Stock not found: {discrepancy.symbol}")
                raise ValueError(f"Stock not found: {discrepancy.symbol}")

            # Get broker position details
            broker_positions = self.get_broker_positions()
            broker_data = broker_positions[discrepancy.symbol]

            # Create trade record
            trade = Trade(
                strategy_id=strategy_id,
                stock_id=stock.id,
                entry_time=datetime.now(timezone.utc),
                entry_price=broker_data['avg_cost'],
                quantity=discrepancy.broker_quantity,
                trade_type='LONG',
                status='OPEN',
                market_context={'recovered': True, 'recovery_timestamp': datetime.now(timezone.utc).isoformat()}
            )

            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)

            logger.info(
                f"Created recovery trade: id={trade.id}, "
                f"symbol={discrepancy.symbol}, quantity={trade.quantity}"
            )

            return trade

        except Exception as e:
            logger.error(f"Failed to recover extra position: {str(e)}")
            self.db.rollback()
            raise

    def recover_missing_position(self, discrepancy: PositionDiscrepancy) -> None:
        """
        Close trades in database for position missing at broker.

        Args:
            discrepancy: Position discrepancy with MISSING_AT_BROKER type

        Raises:
            ValueError: If discrepancy type is not MISSING_AT_BROKER
        """
        if discrepancy.discrepancy_type != 'MISSING_AT_BROKER':
            raise ValueError(
                f"Invalid discrepancy type: {discrepancy.discrepancy_type}. "
                "Expected MISSING_AT_BROKER"
            )

        logger.warning(
            f"Recovering missing position: {discrepancy.symbol} "
            f"({discrepancy.db_quantity} shares)"
        )

        try:
            # Get stock
            stock = self.db.query(Stock).filter(
                Stock.symbol == discrepancy.symbol
            ).first()

            if not stock:
                logger.error(f"Stock not found: {discrepancy.symbol}")
                raise ValueError(f"Stock not found: {discrepancy.symbol}")

            # Find all open trades for this symbol
            open_trades = self.db.query(Trade).filter(
                Trade.stock_id == stock.id,
                Trade.status == 'OPEN'
            ).all()

            # Close all open trades
            for trade in open_trades:
                trade.status = 'CLOSED'
                trade.exit_time = datetime.now(timezone.utc)
                trade.exit_price = 0.0  # Unknown exit price
                trade.profit_loss = 0.0  # Unknown P&L
                trade.market_context = trade.market_context or {}
                trade.market_context['recovered'] = True
                trade.market_context['recovery_reason'] = 'missing_at_broker'

            self.db.commit()

            logger.info(
                f"Closed {len(open_trades)} trades for missing position: "
                f"{discrepancy.symbol}"
            )

        except Exception as e:
            logger.error(f"Failed to recover missing position: {str(e)}")
            self.db.rollback()
            raise

    def check_major_discrepancy(self, total_value_diff: float, threshold: float = 100.0) -> bool:
        """
        Check if total discrepancy exceeds threshold.

        Args:
            total_value_diff: Total value difference
            threshold: Dollar threshold for major discrepancy (default: $100)

        Returns:
            bool: True if major discrepancy detected
        """
        is_major = total_value_diff > threshold

        if is_major:
            logger.error(
                f"MAJOR DISCREPANCY DETECTED: ${total_value_diff:,.2f} "
                f"(threshold: ${threshold:,.2f})"
            )
        else:
            logger.info(
                f"Discrepancy within acceptable threshold: ${total_value_diff:,.2f}"
            )

        return is_major
