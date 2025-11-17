"""Moving Average Crossover with RSI Confirmation strategy."""
from typing import Dict, Optional, Any
import pandas as pd

from app.services.strategies.base_strategy import BaseStrategy, TradingSignal, SignalType
from app.core.logging import get_logger

logger = get_logger("ma_crossover_rsi")


class MACrossoverRSIStrategy(BaseStrategy):
    """
    Moving Average Crossover with RSI Confirmation strategy.

    Entry (BUY) conditions:
    - EMA(fast) crosses above EMA(slow) (bullish crossover)
    - RSI < rsi_threshold (not overbought)
    - No existing position

    Exit (SELL) conditions:
    - EMA(fast) crosses below EMA(slow) (bearish crossover)
    - OR RSI > rsi_threshold (overbought)
    - AND have existing position

    Parameters:
    - ema_fast: Fast EMA period (default: 20)
    - ema_slow: Slow EMA period (default: 50)
    - rsi_period: RSI period (default: 14)
    - rsi_threshold: RSI overbought threshold (default: 70)
    """

    DEFAULT_PARAMS = {
        'ema_fast': 20,
        'ema_slow': 50,
        'rsi_period': 14,
        'rsi_threshold': 70
    }

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize MA Crossover + RSI strategy.

        Args:
            parameters: Strategy parameters (uses defaults if not provided)
        """
        # Merge with defaults
        params = self.DEFAULT_PARAMS.copy()
        if parameters:
            params.update(parameters)

        # Validate parameters
        self.validate_parameters(params)

        # Initialize base
        super().__init__(name="MA Crossover + RSI", parameters=params)

        # Extract parameters for easy access
        self.ema_fast = params['ema_fast']
        self.ema_slow = params['ema_slow']
        self.rsi_period = params['rsi_period']
        self.rsi_threshold = params['rsi_threshold']

        logger.info(
            f"Strategy initialized: EMA({self.ema_fast}/{self.ema_slow}), "
            f"RSI({self.rsi_period}) threshold={self.rsi_threshold}"
        )

    def generate_signal(
        self,
        df: pd.DataFrame,
        current_position: Optional[str] = None
    ) -> TradingSignal:
        """
        Generate trading signal based on MA crossover and RSI.

        Args:
            df: DataFrame with OHLCV and indicators
            current_position: Current position ('long', None)

        Returns:
            TradingSignal with buy/sell/hold decision
        """
        # Check data sufficiency
        is_sufficient, message = self.check_data_sufficiency(df)
        if not is_sufficient:
            raise ValueError(f"Insufficient data: {message}")

        # Need at least 2 bars to detect crossover
        if len(df) < 2:
            raise ValueError("Need at least 2 bars to detect crossover")

        # Get indicator column names
        ema_fast_col = f'ema_{self.ema_fast}'
        ema_slow_col = f'ema_{self.ema_slow}'
        rsi_col = f'rsi_{self.rsi_period}'

        # Get current and previous values
        current = df.iloc[-1]
        previous = df.iloc[-2]

        current_ema_fast = current[ema_fast_col]
        current_ema_slow = current[ema_slow_col]
        current_rsi = current[rsi_col]

        previous_ema_fast = previous[ema_fast_col]
        previous_ema_slow = previous[ema_slow_col]

        timestamp = pd.Timestamp(current.name)
        symbol = current.get('symbol', 'UNKNOWN')

        # Check for NaN values
        if pd.isna([current_ema_fast, current_ema_slow, current_rsi]).any():
            logger.warning("NaN values in indicators, returning HOLD")
            return TradingSignal(
                signal_type=SignalType.HOLD,
                symbol=symbol,
                timestamp=timestamp,
                trigger_reason="Insufficient warm-up: indicators have NaN values",
                indicator_values={
                    ema_fast_col: float(current_ema_fast) if not pd.isna(current_ema_fast) else None,
                    ema_slow_col: float(current_ema_slow) if not pd.isna(current_ema_slow) else None,
                    rsi_col: float(current_rsi) if not pd.isna(current_rsi) else None
                }
            )

        # Detect crossovers
        bullish_crossover = self._detect_bullish_crossover(
            current_ema_fast, current_ema_slow,
            previous_ema_fast, previous_ema_slow
        )

        bearish_crossover = self._detect_bearish_crossover(
            current_ema_fast, current_ema_slow,
            previous_ema_fast, previous_ema_slow
        )

        # Store indicator values for signal
        indicator_values = {
            ema_fast_col: float(current_ema_fast),
            ema_slow_col: float(current_ema_slow),
            rsi_col: float(current_rsi),
            'close': float(current['close'])
        }

        # Calculate market context
        market_context = self._calculate_market_context(df)

        # Generate signal based on rules
        has_position = current_position == 'long'

        # BUY LOGIC: Bullish crossover + RSI not overbought + no position
        if bullish_crossover and current_rsi < self.rsi_threshold and not has_position:
            trigger_reason = (
                f"BUY: Bullish crossover detected (EMA{self.ema_fast} crossed above EMA{self.ema_slow}) "
                f"with RSI({current_rsi:.1f}) < {self.rsi_threshold}"
            )

            logger.info(f"BUY signal generated: {trigger_reason}")

            return TradingSignal(
                signal_type=SignalType.BUY,
                symbol=symbol,
                timestamp=timestamp,
                trigger_reason=trigger_reason,
                indicator_values=indicator_values,
                market_context=market_context
            )

        # SELL LOGIC: (Bearish crossover OR overbought) + have position
        if has_position:
            if bearish_crossover:
                trigger_reason = (
                    f"SELL: Bearish crossover detected (EMA{self.ema_fast} crossed below EMA{self.ema_slow})"
                )
                logger.info(f"SELL signal generated: {trigger_reason}")

                return TradingSignal(
                    signal_type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=timestamp,
                    trigger_reason=trigger_reason,
                    indicator_values=indicator_values,
                    market_context=market_context
                )

            elif current_rsi > self.rsi_threshold:
                trigger_reason = (
                    f"SELL: Overbought condition (RSI {current_rsi:.1f} > {self.rsi_threshold})"
                )
                logger.info(f"SELL signal generated: {trigger_reason}")

                return TradingSignal(
                    signal_type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=timestamp,
                    trigger_reason=trigger_reason,
                    indicator_values=indicator_values,
                    market_context=market_context
                )

        # HOLD: No conditions met
        trigger_reason = "HOLD: No trading conditions met"

        return TradingSignal(
            signal_type=SignalType.HOLD,
            symbol=symbol,
            timestamp=timestamp,
            trigger_reason=trigger_reason,
            indicator_values=indicator_values,
            market_context=market_context
        )

    def _detect_bullish_crossover(
        self,
        current_fast: float,
        current_slow: float,
        previous_fast: float,
        previous_slow: float
    ) -> bool:
        """
        Detect bullish crossover (fast crosses above slow).

        Args:
            current_fast: Current fast EMA value
            current_slow: Current slow EMA value
            previous_fast: Previous fast EMA value
            previous_slow: Previous slow EMA value

        Returns:
            True if bullish crossover detected
        """
        # Previous: fast was below slow
        # Current: fast is above slow
        return previous_fast <= previous_slow and current_fast > current_slow

    def _detect_bearish_crossover(
        self,
        current_fast: float,
        current_slow: float,
        previous_fast: float,
        previous_slow: float
    ) -> bool:
        """
        Detect bearish crossover (fast crosses below slow).

        Args:
            current_fast: Current fast EMA value
            current_slow: Current slow EMA value
            previous_fast: Previous fast EMA value
            previous_slow: Previous slow EMA value

        Returns:
            True if bearish crossover detected
        """
        # Previous: fast was above slow
        # Current: fast is below slow
        return previous_fast >= previous_slow and current_fast < current_slow

    def _calculate_market_context(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate additional market context.

        Args:
            df: DataFrame with market data

        Returns:
            Dictionary with market context metrics
        """
        try:
            # Calculate volatility (std dev of recent returns)
            returns = df['close'].pct_change().tail(20)
            volatility = float(returns.std())

            # Calculate volume trend (current vs average)
            avg_volume = float(df['volume'].tail(20).mean())
            current_volume = float(df['volume'].iloc[-1])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            # Determine trend direction
            ema_fast_col = f'ema_{self.ema_fast}'
            current_fast = df[ema_fast_col].iloc[-1]
            previous_fast = df[ema_fast_col].iloc[-20] if len(df) >= 20 else df[ema_fast_col].iloc[0]

            if current_fast > previous_fast:
                trend = "uptrend"
            elif current_fast < previous_fast:
                trend = "downtrend"
            else:
                trend = "sideways"

            return {
                'volatility': volatility,
                'volume_vs_avg': volume_ratio,
                'trend': trend
            }

        except Exception as e:
            logger.warning(f"Error calculating market context: {str(e)}")
            return {}

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.parameters.copy()

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate strategy parameters.

        Args:
            parameters: Parameters to validate

        Returns:
            True if valid

        Raises:
            ValueError: If parameters are invalid
        """
        required = ['ema_fast', 'ema_slow', 'rsi_period', 'rsi_threshold']

        # Check required parameters
        missing = [p for p in required if p not in parameters]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Validate types
        for param in required:
            if not isinstance(parameters[param], (int, float)):
                raise ValueError(f"Parameter {param} must be numeric")

        # Validate ranges
        if parameters['ema_fast'] <= 0:
            raise ValueError("ema_fast must be positive")

        if parameters['ema_slow'] <= 0:
            raise ValueError("ema_slow must be positive")

        if parameters['ema_fast'] >= parameters['ema_slow']:
            raise ValueError("ema_fast must be less than ema_slow")

        if parameters['rsi_period'] <= 0:
            raise ValueError("rsi_period must be positive")

        if not (0 < parameters['rsi_threshold'] <= 100):
            raise ValueError("rsi_threshold must be between 0 and 100")

        return True

    def get_required_indicators(self) -> Dict[str, Dict]:
        """Get required indicators for this strategy."""
        return {
            f'ema_{self.ema_fast}': {
                'type': 'ema',
                'period': self.ema_fast,
                'column': 'close'
            },
            f'ema_{self.ema_slow}': {
                'type': 'ema',
                'period': self.ema_slow,
                'column': 'close'
            },
            f'rsi_{self.rsi_period}': {
                'type': 'rsi',
                'period': self.rsi_period,
                'column': 'close'
            }
        }
