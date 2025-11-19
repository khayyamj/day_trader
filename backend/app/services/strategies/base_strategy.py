"""Base strategy class for implementing trading strategies."""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from enum import Enum
import pandas as pd

from app.core.logging import get_logger

logger = get_logger("base_strategy")


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TradingSignal:
    """Trading signal with metadata."""

    def __init__(
        self,
        signal_type: SignalType,
        symbol: str,
        timestamp: pd.Timestamp,
        trigger_reason: str,
        indicator_values: Dict[str, float],
        market_context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize trading signal.

        Args:
            signal_type: Type of signal (BUY, SELL, HOLD)
            symbol: Stock symbol
            timestamp: Time when signal was generated
            trigger_reason: Explanation of why signal was generated
            indicator_values: Current values of key indicators
            market_context: Additional market context (volatility, volume, etc.)
        """
        self.signal_type = signal_type
        self.symbol = symbol
        self.timestamp = timestamp
        self.trigger_reason = trigger_reason
        self.indicator_values = indicator_values
        self.market_context = market_context or {}

    def to_dict(self) -> Dict:
        """Convert signal to dictionary for storage."""
        return {
            'signal_type': self.signal_type.value,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'trigger_reason': self.trigger_reason,
            'indicator_values': self.indicator_values,
            'market_context': self.market_context
        }

    def __repr__(self):
        return (
            f"<TradingSignal(type={self.signal_type.value}, symbol={self.symbol}, "
            f"timestamp={self.timestamp}, reason='{self.trigger_reason}')>"
        )


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    All strategy implementations must inherit from this class and
    implement the required abstract methods.
    """

    def __init__(self, name: str, parameters: Dict[str, Any]):
        """
        Initialize base strategy.

        Args:
            name: Strategy name
            parameters: Strategy-specific parameters
        """
        self.name = name
        self.parameters = parameters
        logger.info(f"Initialized strategy: {name}")

    @abstractmethod
    def generate_signal(
        self,
        df: pd.DataFrame,
        current_position: Optional[str] = None
    ) -> TradingSignal:
        """
        Generate trading signal based on market data and indicators.

        Args:
            df: DataFrame with OHLCV data and calculated indicators
            current_position: Current position status ('long', 'short', or None)

        Returns:
            TradingSignal with buy/sell/hold decision

        Raises:
            ValueError: If DataFrame missing required data
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get strategy parameters.

        Returns:
            Dictionary of parameter names and values
        """
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate strategy parameters.

        Args:
            parameters: Parameters to validate

        Returns:
            True if parameters are valid

        Raises:
            ValueError: If parameters are invalid with description
        """
        pass

    def get_required_indicators(self) -> Dict[str, Dict]:
        """
        Get required indicators for this strategy.

        Returns:
            Dictionary of indicator names and their configurations

        Note:
            Override this method to specify required indicators.
            Default returns empty dict (no indicators required).
        """
        return {}

    def check_data_sufficiency(self, df: pd.DataFrame) -> tuple[bool, str]:
        """
        Check if DataFrame has sufficient data for strategy.

        Args:
            df: DataFrame to check

        Returns:
            Tuple of (is_sufficient, message)
        """
        if df.empty:
            return False, "DataFrame is empty"

        # Check for required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            return False, f"Missing required columns: {missing_cols}"

        # Check for required indicators
        required_indicators = self.get_required_indicators()
        missing_indicators = [
            name for name in required_indicators.keys()
            if name not in df.columns
        ]

        if missing_indicators:
            return False, f"Missing required indicators: {missing_indicators}"

        return True, "Data is sufficient"

    def calculate_stop_loss_price(
        self,
        entry_price: float,
        stop_loss_pct: Optional[float] = None
    ) -> float:
        """
        Calculate stop-loss price based on entry price and percentage.

        Formula: stop_loss = entry_price * (1 - stop_loss_pct)

        Args:
            entry_price: Entry price per share
            stop_loss_pct: Stop loss percentage (e.g., 0.05 for 5%).
                          If None, uses strategy parameter 'stop_loss_pct'

        Returns:
            float: Stop loss price

        Raises:
            ValueError: If stop_loss_pct is invalid or not provided
        """
        if stop_loss_pct is None:
            stop_loss_pct = self.parameters.get('stop_loss_pct')

        if stop_loss_pct is None:
            raise ValueError("stop_loss_pct must be provided or in strategy parameters")

        if stop_loss_pct <= 0 or stop_loss_pct >= 1:
            raise ValueError(f"stop_loss_pct must be between 0 and 1, got {stop_loss_pct}")

        stop_price = entry_price * (1 - stop_loss_pct)

        logger.debug(
            f"Calculated stop loss: entry=${entry_price:.2f}, "
            f"pct={stop_loss_pct*100:.1f}%, stop=${stop_price:.2f}"
        )

        return stop_price

    def calculate_take_profit_price(
        self,
        entry_price: float,
        take_profit_pct: Optional[float] = None
    ) -> float:
        """
        Calculate take-profit price based on entry price and percentage.

        Formula: take_profit = entry_price * (1 + take_profit_pct)

        Args:
            entry_price: Entry price per share
            take_profit_pct: Take profit percentage (e.g., 0.10 for 10%).
                            If None, uses strategy parameter 'take_profit_pct'

        Returns:
            float: Take profit price

        Raises:
            ValueError: If take_profit_pct is invalid or not provided
        """
        if take_profit_pct is None:
            take_profit_pct = self.parameters.get('take_profit_pct')

        if take_profit_pct is None:
            raise ValueError("take_profit_pct must be provided or in strategy parameters")

        if take_profit_pct <= 0:
            raise ValueError(f"take_profit_pct must be positive, got {take_profit_pct}")

        take_profit = entry_price * (1 + take_profit_pct)

        logger.debug(
            f"Calculated take profit: entry=${entry_price:.2f}, "
            f"pct={take_profit_pct*100:.1f}%, tp=${take_profit:.2f}"
        )

        return take_profit

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', parameters={self.parameters})>"
