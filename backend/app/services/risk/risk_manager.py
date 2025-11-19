"""Risk management engine for trade validation."""
import logging
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from decimal import Decimal

from app.services.risk.position_sizer import PositionSizer
from app.services.trading.ibkr_client import IBKRClient
from app.models.trade import Trade
from app.models.stock import Stock
from app.models.strategy import Strategy

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of risk validation check."""

    def __init__(self, is_valid: bool, reason: Optional[str] = None):
        """
        Initialize validation result.

        Args:
            is_valid: Whether validation passed
            reason: Reason for rejection if validation failed
        """
        self.is_valid = is_valid
        self.reason = reason

    def __repr__(self):
        if self.is_valid:
            return "<ValidationResult(valid=True)>"
        return f"<ValidationResult(valid=False, reason='{self.reason}')>"


class RiskManager:
    """
    Risk management engine that enforces trading rules.

    Rules enforced:
    - Maximum 20% position size per trade
    - Maximum 50% portfolio allocation per strategy
    - No duplicate positions (can't buy if already long same symbol)
    - Sufficient capital available for trade
    - Daily loss limit not hit (3 consecutive losses)
    """

    # Risk limits
    MAX_POSITION_PERCENT = 0.20  # 20% max position size
    MAX_STRATEGY_ALLOCATION_PERCENT = 0.50  # 50% max per strategy

    def __init__(
        self,
        ibkr_client: IBKRClient,
        position_sizer: PositionSizer,
        db: Session
    ):
        """
        Initialize RiskManager.

        Args:
            ibkr_client: Configured IBKRClient instance
            position_sizer: PositionSizer instance
            db: Database session
        """
        self.ibkr_client = ibkr_client
        self.position_sizer = position_sizer
        self.db = db

        logger.info("RiskManager initialized")

    def check_portfolio_allocation(
        self,
        strategy_id: int,
        new_position_value: float
    ) -> ValidationResult:
        """
        Check if adding new position would exceed 50% portfolio allocation for strategy.

        Args:
            strategy_id: Strategy ID
            new_position_value: Value of new position to add

        Returns:
            ValidationResult: Validation result
        """
        try:
            # Get portfolio value
            portfolio_value = self.position_sizer.get_portfolio_value()

            # Calculate current strategy allocation
            current_allocation = self._get_strategy_allocation(strategy_id)

            # Calculate new allocation after adding position
            new_allocation = current_allocation + new_position_value
            new_allocation_percent = new_allocation / portfolio_value

            logger.info(
                f"Strategy {strategy_id} allocation check: "
                f"current=${current_allocation:,.2f}, "
                f"new=${new_allocation:,.2f} "
                f"({new_allocation_percent * 100:.1f}% of portfolio)"
            )

            if new_allocation_percent > self.MAX_STRATEGY_ALLOCATION_PERCENT:
                reason = (
                    f"Strategy allocation exceeds 50% limit: "
                    f"{new_allocation_percent * 100:.1f}% "
                    f"(${new_allocation:,.2f} / ${portfolio_value:,.2f})"
                )
                logger.warning(f"Validation failed: {reason}")
                return ValidationResult(is_valid=False, reason=reason)

            return ValidationResult(is_valid=True)

        except Exception as e:
            reason = f"Portfolio allocation check failed: {str(e)}"
            logger.error(reason)
            return ValidationResult(is_valid=False, reason=reason)

    def _get_strategy_allocation(self, strategy_id: int) -> float:
        """
        Get current dollar value allocated to strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            float: Total position value for strategy
        """
        try:
            # Get all open trades for strategy
            open_trades = self.db.query(Trade).filter(
                Trade.strategy_id == strategy_id,
                Trade.status == 'OPEN'
            ).all()

            total_value = 0.0

            for trade in open_trades:
                position_value = float(trade.entry_price) * trade.quantity
                total_value += position_value

            logger.info(
                f"Strategy {strategy_id} current allocation: ${total_value:,.2f} "
                f"({len(open_trades)} open positions)"
            )

            return total_value

        except Exception as e:
            logger.error(f"Failed to get strategy allocation: {str(e)}")
            raise

    def check_duplicate_position(
        self,
        strategy_id: int,
        symbol: str
    ) -> ValidationResult:
        """
        Check if already holding position in symbol for strategy.

        Args:
            strategy_id: Strategy ID
            symbol: Stock symbol

        Returns:
            ValidationResult: Validation result
        """
        try:
            # Get stock ID
            stock = self.db.query(Stock).filter(
                Stock.symbol == symbol
            ).first()

            if not stock:
                reason = f"Stock not found: {symbol}"
                logger.error(reason)
                return ValidationResult(is_valid=False, reason=reason)

            # Check for open position
            existing_trade = self.db.query(Trade).filter(
                Trade.strategy_id == strategy_id,
                Trade.stock_id == stock.id,
                Trade.status == 'OPEN'
            ).first()

            if existing_trade:
                reason = (
                    f"Duplicate position: already holding {symbol} "
                    f"(trade_id={existing_trade.id}, qty={existing_trade.quantity})"
                )
                logger.warning(f"Validation failed: {reason}")
                return ValidationResult(is_valid=False, reason=reason)

            return ValidationResult(is_valid=True)

        except Exception as e:
            reason = f"Duplicate position check failed: {str(e)}"
            logger.error(reason)
            return ValidationResult(is_valid=False, reason=reason)

    def check_sufficient_capital(
        self,
        position_value: float
    ) -> ValidationResult:
        """
        Check if sufficient capital available for trade.

        Args:
            position_value: Required capital for position

        Returns:
            ValidationResult: Validation result
        """
        try:
            available_cash = self.position_sizer.get_available_cash()

            logger.info(
                f"Capital check: need ${position_value:,.2f}, "
                f"have ${available_cash:,.2f}"
            )

            if position_value > available_cash:
                reason = (
                    f"Insufficient capital: need ${position_value:,.2f}, "
                    f"have ${available_cash:,.2f}"
                )
                logger.warning(f"Validation failed: {reason}")
                return ValidationResult(is_valid=False, reason=reason)

            return ValidationResult(is_valid=True)

        except Exception as e:
            reason = f"Capital check failed: {str(e)}"
            logger.error(reason)
            return ValidationResult(is_valid=False, reason=reason)

    def check_position_size_limit(
        self,
        position_value: float
    ) -> ValidationResult:
        """
        Check if position size is within 20% portfolio limit.

        Args:
            position_value: Value of position

        Returns:
            ValidationResult: Validation result
        """
        try:
            portfolio_value = self.position_sizer.get_portfolio_value()
            position_percent = position_value / portfolio_value

            logger.info(
                f"Position size check: ${position_value:,.2f} "
                f"= {position_percent * 100:.1f}% of ${portfolio_value:,.2f}"
            )

            if position_percent > self.MAX_POSITION_PERCENT:
                reason = (
                    f"Position size exceeds 20% limit: "
                    f"{position_percent * 100:.1f}% "
                    f"(${position_value:,.2f} / ${portfolio_value:,.2f})"
                )
                logger.warning(f"Validation failed: {reason}")
                return ValidationResult(is_valid=False, reason=reason)

            return ValidationResult(is_valid=True)

        except Exception as e:
            reason = f"Position size check failed: {str(e)}"
            logger.error(reason)
            return ValidationResult(is_valid=False, reason=reason)

    def check_daily_loss_limit(
        self,
        strategy_id: int
    ) -> ValidationResult:
        """
        Check if strategy has hit daily loss limit (3 consecutive losses).

        Args:
            strategy_id: Strategy ID

        Returns:
            ValidationResult: Validation result
        """
        try:
            # Get strategy
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strategy_id
            ).first()

            if not strategy:
                reason = f"Strategy not found: {strategy_id}"
                logger.error(reason)
                return ValidationResult(is_valid=False, reason=reason)

            # Check if strategy is paused due to loss limit
            if strategy.status == 'paused':
                reason = (
                    f"Strategy paused (likely due to daily loss limit): "
                    f"{strategy.name}"
                )
                logger.warning(f"Validation failed: {reason}")
                return ValidationResult(is_valid=False, reason=reason)

            return ValidationResult(is_valid=True)

        except Exception as e:
            reason = f"Daily loss limit check failed: {str(e)}"
            logger.error(reason)
            return ValidationResult(is_valid=False, reason=reason)

    def validate_trade(
        self,
        strategy_id: int,
        symbol: str,
        position_size: Dict
    ) -> ValidationResult:
        """
        Run all risk validation checks before allowing trade.

        Args:
            strategy_id: Strategy ID
            symbol: Stock symbol
            position_size: Position size dict from PositionSizer.calculate_position_size()

        Returns:
            ValidationResult: Combined validation result
        """
        logger.info("=" * 60)
        logger.info("RISK VALIDATION")
        logger.info("=" * 60)
        logger.info(f"Strategy: {strategy_id}")
        logger.info(f"Symbol: {symbol}")
        logger.info(f"Quantity: {position_size['quantity']} shares")
        logger.info(f"Position Value: ${position_size['position_value']:,.2f}")
        logger.info("-" * 60)

        # Run all checks
        checks = [
            ("Daily Loss Limit", self.check_daily_loss_limit(strategy_id)),
            ("Duplicate Position", self.check_duplicate_position(strategy_id, symbol)),
            ("Position Size Limit", self.check_position_size_limit(position_size['position_value'])),
            ("Sufficient Capital", self.check_sufficient_capital(position_size['position_value'])),
            ("Portfolio Allocation", self.check_portfolio_allocation(strategy_id, position_size['position_value']))
        ]

        # Check each validation result
        for check_name, result in checks:
            if not result.is_valid:
                logger.error(f"✗ {check_name}: FAILED - {result.reason}")
                logger.info("=" * 60)
                return result
            else:
                logger.info(f"✓ {check_name}: PASSED")

        logger.info("-" * 60)
        logger.info("✓ ALL RISK CHECKS PASSED")
        logger.info("=" * 60)

        return ValidationResult(is_valid=True)
