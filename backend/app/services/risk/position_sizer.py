"""Position sizing calculator using 2% risk rule."""
import logging
from typing import Optional, Dict
from app.services.trading.ibkr_client import IBKRClient

logger = logging.getLogger(__name__)


class PositionSizer:
    """
    Calculate position sizes using 2% risk rule with safety caps.

    The 2% rule means we risk no more than 2% of portfolio value on any single trade.
    Position size = (portfolio_value * 0.02) / (entry_price - stop_loss)
    """

    # Risk parameters
    RISK_PERCENT = 0.02  # 2% risk per trade
    MAX_POSITION_PERCENT = 0.20  # 20% max position size

    def __init__(self, ibkr_client: IBKRClient):
        """
        Initialize PositionSizer.

        Args:
            ibkr_client: Configured IBKRClient instance
        """
        self.ibkr_client = ibkr_client
        logger.info("PositionSizer initialized with 2% risk rule")

    def get_portfolio_value(self) -> float:
        """
        Get current portfolio net liquidation value from IBKR.

        Returns:
            float: Portfolio net liquidation value

        Raises:
            ConnectionError: If not connected to IBKR
            ValueError: If portfolio value cannot be retrieved
        """
        if not self.ibkr_client.is_connected:
            raise ConnectionError("Not connected to IBKR")

        try:
            account_summary = self.ibkr_client.get_account_summary()

            if 'NetLiquidation' not in account_summary:
                raise ValueError("NetLiquidation not found in account summary")

            portfolio_value = account_summary['NetLiquidation']

            logger.info(f"Portfolio value: ${portfolio_value:,.2f}")
            return portfolio_value

        except Exception as e:
            logger.error(f"Failed to get portfolio value: {str(e)}")
            raise

    def get_available_cash(self) -> float:
        """
        Get available cash for trading from IBKR.

        Returns:
            float: Available cash (buying power)

        Raises:
            ConnectionError: If not connected to IBKR
            ValueError: If buying power cannot be retrieved
        """
        if not self.ibkr_client.is_connected:
            raise ConnectionError("Not connected to IBKR")

        try:
            account_summary = self.ibkr_client.get_account_summary()

            if 'BuyingPower' not in account_summary:
                raise ValueError("BuyingPower not found in account summary")

            buying_power = account_summary['BuyingPower']

            logger.info(f"Available buying power: ${buying_power:,.2f}")
            return buying_power

        except Exception as e:
            logger.error(f"Failed to get available cash: {str(e)}")
            raise

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        portfolio_value: Optional[float] = None
    ) -> Dict:
        """
        Calculate position size using 2% risk rule.

        Formula: position_size = (portfolio_value * 0.02) / (entry_price - stop_loss)

        Args:
            entry_price: Planned entry price per share
            stop_loss: Stop loss price per share
            portfolio_value: Optional portfolio value (fetched if not provided)

        Returns:
            dict: {
                'quantity': int,  # Number of shares
                'position_value': float,  # Total position value in dollars
                'risk_amount': float,  # Dollar amount at risk
                'risk_percent': float,  # Actual risk as percent of portfolio
                'position_percent': float,  # Position size as percent of portfolio
                'capped': bool,  # Whether position was capped
                'cap_reason': str  # Reason for capping (if applicable)
            }

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate inputs
        if entry_price <= 0:
            raise ValueError(f"Invalid entry price: {entry_price}")

        if stop_loss <= 0:
            raise ValueError(f"Invalid stop loss: {stop_loss}")

        if stop_loss >= entry_price:
            raise ValueError(
                f"Stop loss (${stop_loss:.2f}) must be below entry price (${entry_price:.2f})"
            )

        # Get portfolio value
        if portfolio_value is None:
            portfolio_value = self.get_portfolio_value()

        logger.info(
            f"Calculating position size: entry=${entry_price:.2f}, "
            f"stop=${stop_loss:.2f}, portfolio=${portfolio_value:,.2f}"
        )

        # Calculate risk per share
        risk_per_share = entry_price - stop_loss

        # Calculate position size using 2% rule
        risk_amount = portfolio_value * self.RISK_PERCENT
        quantity = int(risk_amount / risk_per_share)

        # Apply maximum position size cap (20% of portfolio)
        max_position_value = portfolio_value * self.MAX_POSITION_PERCENT
        max_quantity_by_value = int(max_position_value / entry_price)

        capped = False
        cap_reason = None

        if quantity > max_quantity_by_value:
            quantity = max_quantity_by_value
            capped = True
            cap_reason = "MAX_POSITION_SIZE"
            logger.warning(
                f"Position size capped at 20% of portfolio: {quantity} shares"
            )

        # Ensure minimum of 1 share
        if quantity < 1:
            quantity = 1
            logger.warning("Position size rounded up to minimum of 1 share")

        # Calculate actual values
        position_value = quantity * entry_price
        actual_risk_amount = quantity * risk_per_share
        actual_risk_percent = (actual_risk_amount / portfolio_value) * 100
        position_percent = (position_value / portfolio_value) * 100

        result = {
            'quantity': quantity,
            'position_value': position_value,
            'risk_amount': actual_risk_amount,
            'risk_percent': actual_risk_percent,
            'position_percent': position_percent,
            'capped': capped,
            'cap_reason': cap_reason,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'portfolio_value': portfolio_value
        }

        logger.info(
            f"Position size calculated: {quantity} shares = ${position_value:,.2f} "
            f"({position_percent:.1f}% of portfolio), "
            f"risk=${actual_risk_amount:,.2f} ({actual_risk_percent:.2f}%)"
        )

        return result

    def validate_position(self, position_size: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate that position size doesn't exceed available cash.

        Args:
            position_size: Position size dict from calculate_position_size()

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            available_cash = self.get_available_cash()
            position_value = position_size['position_value']

            if position_value > available_cash:
                error_msg = (
                    f"Insufficient buying power: need ${position_value:,.2f}, "
                    f"have ${available_cash:,.2f}"
                )
                logger.error(error_msg)
                return False, error_msg

            logger.info(
                f"Position validated: ${position_value:,.2f} <= ${available_cash:,.2f}"
            )
            return True, None

        except Exception as e:
            error_msg = f"Position validation failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def log_calculation_details(self, position_size: Dict) -> None:
        """
        Log detailed position sizing calculation for audit trail.

        Args:
            position_size: Position size dict from calculate_position_size()
        """
        logger.info("=" * 60)
        logger.info("POSITION SIZING CALCULATION")
        logger.info("=" * 60)
        logger.info(f"Portfolio Value:     ${position_size['portfolio_value']:,.2f}")
        logger.info(f"Entry Price:         ${position_size['entry_price']:.2f}")
        logger.info(f"Stop Loss:           ${position_size['stop_loss']:.2f}")
        logger.info(f"Risk per Share:      ${position_size['entry_price'] - position_size['stop_loss']:.2f}")
        logger.info("-" * 60)
        logger.info(f"Quantity:            {position_size['quantity']} shares")
        logger.info(f"Position Value:      ${position_size['position_value']:,.2f}")
        logger.info(f"Position %:          {position_size['position_percent']:.2f}%")
        logger.info(f"Risk Amount:         ${position_size['risk_amount']:,.2f}")
        logger.info(f"Risk %:              {position_size['risk_percent']:.2f}%")

        if position_size['capped']:
            logger.info(f"⚠ CAPPED:           {position_size['cap_reason']}")

        logger.info("=" * 60)
