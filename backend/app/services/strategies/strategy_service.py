"""Strategy service for managing strategy state and lifecycle."""
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.models.stock import Stock
from app.models.stock_data import StockData
from app.core.logging import get_logger

logger = get_logger("strategy_service")


class StrategyService:
    """Service for managing trading strategies and their state."""

    def __init__(self, db: Session):
        """
        Initialize strategy service.

        Args:
            db: Database session
        """
        self.db = db

    def get_strategy_status(self, strategy_id: int) -> Dict:
        """
        Get current status of a strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            Dictionary with strategy status information

        Raises:
            ValueError: If strategy not found
        """
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()

        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        logger.debug(f"Getting status for strategy {strategy_id}")

        return {
            'strategy_id': strategy.id,
            'name': strategy.name,
            'status': strategy.status,
            'active': strategy.active,
            'warm_up_bars_remaining': strategy.warm_up_bars_remaining,
            'parameters': strategy.parameters
        }

    def activate_strategy(self, strategy_id: int) -> Dict:
        """
        Activate a strategy after checking warm-up requirements.

        Args:
            strategy_id: Strategy ID

        Returns:
            Dictionary with activation result

        Raises:
            ValueError: If strategy not found or cannot be activated
        """
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()

        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        logger.info(f"Activating strategy {strategy_id}: {strategy.name}")

        # Check warm-up status
        warm_up_result = self.check_warm_up(strategy_id)

        if not warm_up_result['warm_up_complete']:
            # Set status to warming
            strategy.status = "warming"
            strategy.warm_up_bars_remaining = warm_up_result['bars_needed']

            self.db.commit()
            self.db.refresh(strategy)

            logger.warning(
                f"Strategy {strategy_id} activated but in warm-up mode: "
                f"{warm_up_result['bars_needed']} bars remaining"
            )

            return {
                'strategy_id': strategy.id,
                'name': strategy.name,
                'status': strategy.status,
                'warm_up_complete': False,
                'warm_up_bars_remaining': warm_up_result['bars_needed'],
                'message': f"Strategy activated in warming mode. Need {warm_up_result['bars_needed']} more bars."
            }

        # Warm-up complete, set to active
        strategy.status = "active"
        strategy.active = True
        strategy.warm_up_bars_remaining = 0

        self.db.commit()
        self.db.refresh(strategy)

        logger.info(f"Strategy {strategy_id} activated successfully")

        return {
            'strategy_id': strategy.id,
            'name': strategy.name,
            'status': strategy.status,
            'warm_up_complete': True,
            'warm_up_bars_remaining': 0,
            'message': "Strategy activated successfully"
        }

    def pause_strategy(self, strategy_id: int, reason: Optional[str] = None) -> Dict:
        """
        Pause a strategy.

        Args:
            strategy_id: Strategy ID
            reason: Optional reason for pausing

        Returns:
            Dictionary with pause result

        Raises:
            ValueError: If strategy not found
        """
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()

        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        previous_status = strategy.status

        strategy.status = "paused"
        strategy.active = False

        self.db.commit()
        self.db.refresh(strategy)

        log_message = f"Strategy {strategy_id} paused (was: {previous_status})"
        if reason:
            log_message += f": {reason}"

        logger.info(log_message)

        return {
            'strategy_id': strategy.id,
            'name': strategy.name,
            'previous_status': previous_status,
            'current_status': strategy.status,
            'reason': reason,
            'message': "Strategy paused successfully"
        }

    def check_warm_up(self, strategy_id: int) -> Dict:
        """
        Check if strategy has sufficient data for warm-up period.

        The warm-up check verifies that all stocks in the watchlist have
        at least 100 bars of historical data, which is needed for
        reliable indicator calculations.

        Args:
            strategy_id: Strategy ID

        Returns:
            Dictionary with warm-up status

        Raises:
            ValueError: If strategy not found
        """
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()

        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        logger.debug(f"Checking warm-up for strategy {strategy_id}")

        # Get all stocks
        stocks = self.db.query(Stock).all()

        if not stocks:
            logger.warning("No stocks in watchlist for warm-up check")
            return {
                'strategy_id': strategy_id,
                'warm_up_complete': False,
                'bars_available': 0,
                'bars_needed': 100,
                'stocks_checked': 0,
                'stocks_ready': 0
            }

        min_bars_required = 100
        stocks_ready = 0
        min_bars_available = float('inf')

        # Check each stock
        for stock in stocks:
            bar_count = self.db.query(StockData).filter(
                StockData.stock_id == stock.id
            ).count()

            if bar_count >= min_bars_required:
                stocks_ready += 1

            min_bars_available = min(min_bars_available, bar_count)

        # Warm-up complete if all stocks have enough data
        warm_up_complete = stocks_ready == len(stocks)
        bars_needed = max(0, min_bars_required - min_bars_available) if min_bars_available != float('inf') else min_bars_required

        # Update strategy
        strategy.warm_up_bars_remaining = bars_needed

        if warm_up_complete:
            if strategy.status == "warming":
                strategy.status = "active"
        else:
            if strategy.status == "active":
                strategy.status = "warming"

        self.db.commit()

        logger.debug(
            f"Warm-up check: {stocks_ready}/{len(stocks)} stocks ready, "
            f"{bars_needed} bars needed"
        )

        return {
            'strategy_id': strategy_id,
            'warm_up_complete': warm_up_complete,
            'bars_available': int(min_bars_available) if min_bars_available != float('inf') else 0,
            'bars_needed': bars_needed,
            'stocks_checked': len(stocks),
            'stocks_ready': stocks_ready
        }

    def set_error_status(self, strategy_id: int, error_message: str) -> None:
        """
        Set strategy to error status.

        Args:
            strategy_id: Strategy ID
            error_message: Error message

        Raises:
            ValueError: If strategy not found
        """
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()

        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        strategy.status = "error"
        strategy.active = False

        self.db.commit()

        logger.error(f"Strategy {strategy_id} set to error status: {error_message}")

    def list_strategies(self) -> list:
        """
        List all strategies with their current status.

        Returns:
            List of strategy dictionaries
        """
        strategies = self.db.query(Strategy).all()

        return [
            {
                'strategy_id': s.id,
                'name': s.name,
                'description': s.description,
                'status': s.status,
                'active': s.active,
                'warm_up_bars_remaining': s.warm_up_bars_remaining,
                'parameters': s.parameters
            }
            for s in strategies
        ]
