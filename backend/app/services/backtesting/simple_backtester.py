"""Simple custom backtester for strategy validation."""
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
import pandas as pd
from decimal import Decimal

from app.services.indicators.calculator import IndicatorCalculator
from app.services.strategies.base_strategy import BaseStrategy, SignalType
from app.core.logging import get_logger

logger = get_logger("simple_backtester")


class BacktestTrade:
    """Individual trade in a backtest."""

    def __init__(
        self,
        trade_number: int,
        entry_date: date,
        entry_price: float,
        shares: int,
        entry_signal: str,
        entry_indicators: Dict,
        entry_market_context: Dict
    ):
        self.trade_number = trade_number
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.shares = shares
        self.entry_signal = entry_signal
        self.entry_indicators = entry_indicators
        self.entry_market_context = entry_market_context

        # Exit details (filled when trade closes)
        self.exit_date: Optional[date] = None
        self.exit_price: Optional[float] = None
        self.exit_signal: Optional[str] = None
        self.gross_pnl: Optional[float] = None
        self.net_pnl: Optional[float] = None
        self.return_pct: Optional[float] = None
        self.holding_period_days: Optional[int] = None
        self.is_winner: Optional[bool] = None

    def close_trade(
        self,
        exit_date: date,
        exit_price: float,
        exit_signal: str,
        commission: float,
        slippage_cost: float
    ):
        """Close the trade and calculate P&L."""
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.exit_signal = exit_signal

        # Calculate P&L
        self.gross_pnl = (exit_price - self.entry_price) * self.shares
        self.net_pnl = self.gross_pnl - commission - slippage_cost
        self.return_pct = (exit_price / self.entry_price - 1) * 100
        self.holding_period_days = (exit_date - self.entry_date).days
        self.is_winner = self.net_pnl > 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'trade_number': self.trade_number,
            'entry_date': self.entry_date,
            'entry_price': self.entry_price,
            'exit_date': self.exit_date,
            'exit_price': self.exit_price,
            'shares': self.shares,
            'entry_signal': self.entry_signal,
            'exit_signal': self.exit_signal,
            'gross_pnl': self.gross_pnl,
            'net_pnl': self.net_pnl,
            'return_pct': self.return_pct,
            'holding_period_days': self.holding_period_days,
            'is_winner': self.is_winner,
            'entry_indicators': self.entry_indicators,
            'entry_market_context': self.entry_market_context
        }


class PortfolioState:
    """Portfolio state during backtest."""

    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position_value = 0.0
        self.position_shares = 0
        self.position_entry_price = 0.0
        self.equity_curve: List[Dict] = []

    def get_equity(self) -> float:
        """Get total equity (cash + position value)."""
        return self.cash + self.position_value

    def has_position(self) -> bool:
        """Check if currently in a position."""
        return self.position_shares > 0

    def snapshot(self, current_date: date, current_price: float) -> Dict:
        """Take a snapshot of current portfolio state."""
        if self.has_position():
            self.position_value = self.position_shares * current_price
        else:
            self.position_value = 0.0

        equity = self.get_equity()

        return {
            'date': current_date,
            'equity': equity,
            'cash': self.cash,
            'position_value': self.position_value,
            'position_shares': self.position_shares
        }


class SimpleBacktester:
    """
    Simple custom backtester for strategy validation.

    Features:
    - Event-driven bar-by-bar simulation
    - No look-ahead bias (signal on close, execute on next open)
    - Realistic slippage and commissions
    - Position sizing based on available capital
    - Complete trade tracking and equity curve
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        slippage_pct: float = 0.001,  # 0.1%
        commission_per_trade: float = 1.0,
        position_size_pct: float = 0.95,  # Use 95% of available cash
        stop_loss_pct: Optional[float] = None,  # Stop loss percentage (e.g., 0.05 for 5%)
        take_profit_pct: Optional[float] = None  # Take profit percentage (e.g., 0.10 for 10%)
    ):
        """
        Initialize backtester.

        Args:
            initial_capital: Starting capital
            slippage_pct: Slippage percentage (0.001 = 0.1%)
            commission_per_trade: Commission per trade in dollars
            position_size_pct: Percentage of cash to use per trade
            stop_loss_pct: Stop loss percentage (None to disable)
            take_profit_pct: Take profit percentage (None to disable)
        """
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct
        self.commission_per_trade = commission_per_trade
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

        self.portfolio = PortfolioState(initial_capital)
        self.trades: List[BacktestTrade] = []
        self.current_trade: Optional[BacktestTrade] = None
        self.pending_signal: Optional[str] = None  # Signal to execute on next bar
        self.pending_signal_metadata: Optional[Dict] = None

        logger.info(
            f"Backtester initialized: capital=${initial_capital:,.2f}, "
            f"slippage={slippage_pct*100:.2f}%, commission=${commission_per_trade}"
        )

    def run(
        self,
        df: pd.DataFrame,
        strategy: BaseStrategy,
        symbol: str
    ) -> Dict:
        """
        Run backtest on historical data.

        Args:
            df: DataFrame with OHLCV data and indicators
            strategy: Strategy instance to test
            symbol: Stock symbol

        Returns:
            Backtest results dictionary

        Process:
        1. Iterate through each bar
        2. Update portfolio value
        3. Execute pending signal from previous bar (if any)
        4. Generate new signal for current bar
        5. Store signal for next bar execution
        """
        logger.info(f"Starting backtest for {symbol}: {len(df)} bars")

        if len(df) < 2:
            raise ValueError("Need at least 2 bars for backtesting")

        # Reset state
        self.portfolio = PortfolioState(self.initial_capital)
        self.trades = []
        self.current_trade = None
        self.pending_signal = None
        self.pending_signal_metadata = None

        # Iterate through bars (skip first bar - need previous for signals)
        for i in range(1, len(df)):
            current_bar = df.iloc[i]
            previous_bar = df.iloc[i-1]

            current_date = current_bar.name.date() if hasattr(current_bar.name, 'date') else current_bar.name
            current_price = float(current_bar['close'])
            current_open = float(current_bar['open'])

            # 1. Check stop-loss/take-profit for existing position
            if self.portfolio.has_position() and self.current_trade:
                sl_tp_triggered = self._check_stop_loss_take_profit(
                    current_open=current_open,
                    current_high=float(current_bar['high']),
                    current_low=float(current_bar['low']),
                    current_date=current_date
                )

                # If stop-loss or take-profit triggered, skip pending signal
                if sl_tp_triggered:
                    self.pending_signal = None
                    self.pending_signal_metadata = None

            # 2. Execute pending signal from previous bar (at current open)
            if self.pending_signal and not self.portfolio.has_position():
                self._execute_signal(
                    signal_type=self.pending_signal,
                    execution_price=current_open,
                    execution_date=current_date,
                    metadata=self.pending_signal_metadata
                )
                self.pending_signal = None
                self.pending_signal_metadata = None

            # 2. Update portfolio snapshot with current close price
            snapshot = self.portfolio.snapshot(current_date, current_price)
            self.portfolio.equity_curve.append(snapshot)

            # 3. Generate signal for current bar (at close)
            # Create DataFrame slice up to current bar for signal generation
            df_slice = df.iloc[:i+1]

            try:
                current_position = 'long' if self.portfolio.has_position() else None
                trading_signal = strategy.generate_signal(df_slice, current_position)

                # 4. Store signal for next bar execution
                if trading_signal.signal_type != SignalType.HOLD:
                    self.pending_signal = trading_signal.signal_type.value
                    self.pending_signal_metadata = {
                        'trigger_reason': trading_signal.trigger_reason,
                        'indicator_values': trading_signal.indicator_values,
                        'market_context': trading_signal.market_context
                    }

                    logger.debug(
                        f"Bar {i}: {trading_signal.signal_type.value.upper()} signal generated "
                        f"at close=${current_price:.2f} (execute next bar)"
                    )

            except Exception as e:
                logger.warning(f"Error generating signal at bar {i}: {str(e)}")
                continue

        # Close any open position at end
        if self.current_trade and not self.current_trade.exit_date:
            final_bar = df.iloc[-1]
            final_date = final_bar.name.date() if hasattr(final_bar.name, 'date') else final_bar.name
            final_price = float(final_bar['close'])

            self._close_position(
                exit_price=final_price,
                exit_date=final_date,
                exit_signal="END_OF_BACKTEST"
            )

        # Calculate final results
        results = self._calculate_results(symbol, df)

        logger.info(
            f"Backtest complete: {results['total_trades']} trades, "
            f"return={results['total_return_pct']:.2f}%"
        )

        return results

    def _execute_signal(
        self,
        signal_type: str,
        execution_price: float,
        execution_date: date,
        metadata: Dict
    ):
        """
        Execute a trading signal.

        Args:
            signal_type: 'buy' or 'sell'
            execution_price: Price at execution (open of bar)
            execution_date: Date of execution
            metadata: Signal metadata
        """
        if signal_type == 'buy' and not self.portfolio.has_position():
            self._open_position(
                entry_price=execution_price,
                entry_date=execution_date,
                metadata=metadata
            )

        elif signal_type == 'sell' and self.portfolio.has_position():
            self._close_position(
                exit_price=execution_price,
                exit_date=execution_date,
                exit_signal="STRATEGY_SELL"
            )

    def _open_position(
        self,
        entry_price: float,
        entry_date: date,
        metadata: Dict
    ):
        """
        Open a new position.

        Args:
            entry_price: Entry price
            entry_date: Entry date
            metadata: Signal metadata
        """
        # Apply slippage to buy price (pay more)
        slipped_price = entry_price * (1 + self.slippage_pct)

        # Calculate shares based on available cash and position size percentage
        available_cash = self.portfolio.cash * self.position_size_pct
        shares = int(available_cash / slipped_price)

        if shares == 0:
            logger.warning(f"Insufficient cash to buy at ${slipped_price:.2f}")
            return

        # Calculate costs
        position_value = shares * slipped_price
        commission = self.commission_per_trade
        slippage_cost = shares * entry_price * self.slippage_pct
        total_cost = position_value + commission

        # Update portfolio
        self.portfolio.cash -= total_cost
        self.portfolio.position_shares = shares
        self.portfolio.position_entry_price = slipped_price
        self.portfolio.position_value = position_value

        # Create trade record
        self.current_trade = BacktestTrade(
            trade_number=len(self.trades) + 1,
            entry_date=entry_date,
            entry_price=slipped_price,
            shares=shares,
            entry_signal="BUY",
            entry_indicators=metadata.get('indicator_values', {}),
            entry_market_context=metadata.get('market_context', {})
        )

        logger.debug(
            f"OPEN: {shares} shares @ ${slipped_price:.2f} "
            f"(cost=${total_cost:,.2f}, cash=${self.portfolio.cash:,.2f})"
        )

    def _close_position(
        self,
        exit_price: float,
        exit_date: date,
        exit_signal: str
    ):
        """
        Close current position.

        Args:
            exit_price: Exit price
            exit_date: Exit date
            exit_signal: Reason for exit
        """
        if not self.current_trade:
            logger.warning("Attempted to close position but no trade is open")
            return

        # Apply slippage to sell price (receive less)
        slipped_price = exit_price * (1 - self.slippage_pct)

        # Calculate proceeds
        shares = self.current_trade.shares
        proceeds = shares * slipped_price
        commission = self.commission_per_trade
        slippage_cost = shares * exit_price * self.slippage_pct
        net_proceeds = proceeds - commission

        # Update portfolio
        self.portfolio.cash += net_proceeds
        self.portfolio.position_shares = 0
        self.portfolio.position_value = 0.0

        # Complete trade record
        self.current_trade.close_trade(
            exit_date=exit_date,
            exit_price=slipped_price,
            exit_signal=exit_signal,
            commission=commission * 2,  # Entry + exit commission
            slippage_cost=slippage_cost
        )

        logger.debug(
            f"CLOSE: {shares} shares @ ${slipped_price:.2f} "
            f"(pnl=${self.current_trade.net_pnl:,.2f}, "
            f"return={self.current_trade.return_pct:.2f}%)"
        )

        # Store completed trade
        self.trades.append(self.current_trade)
        self.current_trade = None

    def _calculate_results(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Calculate backtest results and metrics.

        Args:
            symbol: Stock symbol
            df: DataFrame with backtest data

        Returns:
            Results dictionary
        """
        final_equity = self.portfolio.get_equity()
        total_return = final_equity - self.initial_capital
        total_return_pct = (final_equity / self.initial_capital - 1) * 100

        # Calculate trade statistics
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.is_winner)
        losing_trades = total_trades - winning_trades

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        # Calculate average win/loss
        wins = [t.net_pnl for t in self.trades if t.is_winner]
        losses = [t.net_pnl for t in self.trades if not t.is_winner and t.net_pnl is not None]

        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0

        # Calculate profit factor
        gross_profit = sum(wins) if wins else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Calculate Sharpe ratio (simplified)
        if len(self.portfolio.equity_curve) > 1:
            equity_series = pd.Series([s['equity'] for s in self.portfolio.equity_curve])
            returns = equity_series.pct_change().dropna()

            if len(returns) > 0 and returns.std() > 0:
                sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5)  # Annualized
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0

        # Calculate max drawdown
        max_drawdown_pct = self._calculate_max_drawdown()

        # Calculate annualized return
        start_date = df.index[0].date() if hasattr(df.index[0], 'date') else df.index[0]
        end_date = df.index[-1].date() if hasattr(df.index[-1], 'date') else df.index[-1]
        days = (end_date - start_date).days
        years = days / 365.25

        if years > 0:
            annualized_return_pct = ((final_equity / self.initial_capital) ** (1 / years) - 1) * 100
        else:
            annualized_return_pct = total_return_pct

        return {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'annualized_return_pct': annualized_return_pct,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown_pct,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'bars_processed': len(df),
            'trades': [t.to_dict() for t in self.trades],
            'equity_curve': self.portfolio.equity_curve
        }

    def _calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown percentage.

        Returns:
            Max drawdown as percentage
        """
        if not self.portfolio.equity_curve:
            return 0.0

        equity_series = pd.Series([s['equity'] for s in self.portfolio.equity_curve])

        # Calculate running maximum
        running_max = equity_series.expanding().max()

        # Calculate drawdown at each point
        drawdown = (equity_series - running_max) / running_max * 100

        # Return maximum drawdown (most negative value)
        max_dd = drawdown.min()

        return abs(max_dd) if max_dd < 0 else 0.0

    def _check_stop_loss_take_profit(
        self,
        current_open: float,
        current_high: float,
        current_low: float,
        current_date: date
    ) -> bool:
        """
        Check if stop-loss or take-profit should trigger.

        Args:
            current_open: Open price of current bar
            current_high: High price of current bar
            current_low: Low price of current bar
            current_date: Current date

        Returns:
            True if position was closed, False otherwise
        """
        if not self.current_trade or not self.portfolio.has_position():
            return False

        entry_price = self.current_trade.entry_price

        # Check stop-loss
        if self.stop_loss_pct:
            stop_price = entry_price * (1 - self.stop_loss_pct)

            # If low touches or crosses stop price
            if current_low <= stop_price:
                logger.debug(
                    f"STOP-LOSS triggered: entry=${entry_price:.2f}, "
                    f"stop=${stop_price:.2f}, low=${current_low:.2f}"
                )

                self._close_position(
                    exit_price=stop_price,
                    exit_date=current_date,
                    exit_signal="STOP_LOSS"
                )
                return True

        # Check take-profit
        if self.take_profit_pct:
            target_price = entry_price * (1 + self.take_profit_pct)

            # If high touches or crosses target price
            if current_high >= target_price:
                logger.debug(
                    f"TAKE-PROFIT triggered: entry=${entry_price:.2f}, "
                    f"target=${target_price:.2f}, high=${current_high:.2f}"
                )

                self._close_position(
                    exit_price=target_price,
                    exit_date=current_date,
                    exit_signal="TAKE_PROFIT"
                )
                return True

        return False
