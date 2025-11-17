"""Performance metrics calculator for backtesting results."""
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from app.core.logging import get_logger

logger = get_logger("metrics_calculator")


class MetricsCalculator:
    """Calculator for backtest performance metrics."""

    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize metrics calculator.

        Args:
            risk_free_rate: Annual risk-free rate (default: 0.0)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_returns(
        self,
        initial_capital: float,
        final_equity: float,
        days: int
    ) -> Dict[str, float]:
        """
        Calculate total and annualized returns.

        Args:
            initial_capital: Starting capital
            final_equity: Final equity
            days: Number of days in backtest

        Returns:
            Dictionary with total_return, total_return_pct, annualized_return_pct
        """
        total_return = final_equity - initial_capital
        total_return_pct = (final_equity / initial_capital - 1) * 100

        # Calculate annualized return
        years = days / 365.25
        if years > 0:
            annualized_return_pct = ((final_equity / initial_capital) ** (1 / years) - 1) * 100
        else:
            annualized_return_pct = total_return_pct

        return {
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'annualized_return_pct': annualized_return_pct
        }

    def calculate_sharpe_ratio(
        self,
        equity_curve: List[float],
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            equity_curve: List of equity values over time
            periods_per_year: Trading periods per year (252 for daily)

        Returns:
            Sharpe ratio (annualized)
        """
        if len(equity_curve) < 2:
            return 0.0

        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()

        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        # Calculate annualized Sharpe
        mean_return = returns.mean()
        std_return = returns.std()

        sharpe = (mean_return - self.risk_free_rate / periods_per_year) / std_return
        sharpe_annualized = sharpe * np.sqrt(periods_per_year)

        return float(sharpe_annualized)

    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict[str, float]:
        """
        Calculate maximum drawdown.

        Args:
            equity_curve: List of equity values over time

        Returns:
            Dictionary with max_drawdown_pct, max_drawdown_value, recovery_days
        """
        if not equity_curve:
            return {'max_drawdown_pct': 0.0, 'max_drawdown_value': 0.0, 'recovery_days': 0}

        equity_series = pd.Series(equity_curve)

        # Calculate running maximum
        running_max = equity_series.expanding().max()

        # Calculate drawdown at each point
        drawdown = equity_series - running_max
        drawdown_pct = (drawdown / running_max * 100).fillna(0)

        # Find maximum drawdown
        max_dd_pct = abs(drawdown_pct.min()) if drawdown_pct.min() < 0 else 0.0
        max_dd_value = abs(drawdown.min()) if drawdown.min() < 0 else 0.0

        # Find recovery days (days from max drawdown to new peak)
        max_dd_idx = drawdown_pct.idxmin() if drawdown_pct.min() < 0 else 0
        recovery_days = 0

        if max_dd_idx > 0:
            # Find next peak after drawdown
            post_drawdown = equity_series.iloc[max_dd_idx:]
            peak_value = running_max.iloc[max_dd_idx]

            recovery_idx = (post_drawdown >= peak_value).idxmax() if (post_drawdown >= peak_value).any() else None

            if recovery_idx:
                recovery_days = recovery_idx - max_dd_idx

        return {
            'max_drawdown_pct': float(max_dd_pct),
            'max_drawdown_value': float(max_dd_value),
            'recovery_days': int(recovery_days) if recovery_days else 0
        }

    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """
        Calculate win rate percentage.

        Args:
            trades: List of trade dictionaries with 'is_winner' or 'net_pnl'

        Returns:
            Win rate percentage
        """
        if not trades:
            return 0.0

        # Count winning trades
        winning_trades = sum(
            1 for t in trades
            if t.get('is_winner', False) or (t.get('net_pnl', 0) > 0)
        )

        win_rate = (winning_trades / len(trades)) * 100

        return float(win_rate)

    def calculate_profit_factor(self, trades: List[Dict]) -> float:
        """
        Calculate profit factor (gross profit / gross loss).

        Args:
            trades: List of trade dictionaries with 'net_pnl'

        Returns:
            Profit factor
        """
        if not trades:
            return 0.0

        # Calculate gross profit and loss
        gross_profit = sum(t.get('net_pnl', 0) for t in trades if t.get('net_pnl', 0) > 0)
        gross_loss = abs(sum(t.get('net_pnl', 0) for t in trades if t.get('net_pnl', 0) < 0))

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        profit_factor = gross_profit / gross_loss

        return float(profit_factor)

    def calculate_avg_win_loss(self, trades: List[Dict]) -> Dict[str, float]:
        """
        Calculate average win and loss amounts.

        Args:
            trades: List of trade dictionaries with 'net_pnl'

        Returns:
            Dictionary with avg_win, avg_loss, win_loss_ratio
        """
        if not trades:
            return {'avg_win': 0.0, 'avg_loss': 0.0, 'win_loss_ratio': 0.0}

        # Separate wins and losses
        wins = [t.get('net_pnl', 0) for t in trades if t.get('net_pnl', 0) > 0]
        losses = [t.get('net_pnl', 0) for t in trades if t.get('net_pnl', 0) < 0]

        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        # Calculate win/loss ratio
        if avg_loss != 0:
            win_loss_ratio = abs(avg_win / avg_loss)
        else:
            win_loss_ratio = float('inf') if avg_win > 0 else 0.0

        return {
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'win_loss_ratio': float(win_loss_ratio)
        }

    def calculate_trade_stats(self, trades: List[Dict]) -> Dict:
        """
        Calculate comprehensive trade statistics.

        Args:
            trades: List of trade dictionaries

        Returns:
            Dictionary with trade statistics
        """
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate_pct': 0.0,
                'avg_holding_period_days': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0
            }

        winning_trades = sum(1 for t in trades if t.get('net_pnl', 0) > 0)
        losing_trades = len(trades) - winning_trades

        win_rate = (winning_trades / len(trades)) * 100 if trades else 0.0

        # Calculate average holding period
        holding_periods = [
            t.get('holding_period_days', 0)
            for t in trades
            if t.get('holding_period_days') is not None
        ]
        avg_holding = sum(holding_periods) / len(holding_periods) if holding_periods else 0.0

        # Find largest win/loss
        pnls = [t.get('net_pnl', 0) for t in trades]
        largest_win = max(pnls) if pnls else 0.0
        largest_loss = min(pnls) if pnls else 0.0

        return {
            'total_trades': len(trades),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': float(win_rate),
            'avg_holding_period_days': float(avg_holding),
            'largest_win': float(largest_win),
            'largest_loss': float(largest_loss)
        }

    def calculate_all_metrics(
        self,
        initial_capital: float,
        final_equity: float,
        equity_curve: List[float],
        trades: List[Dict],
        days: int
    ) -> Dict:
        """
        Calculate all performance metrics.

        Args:
            initial_capital: Starting capital
            final_equity: Final equity
            equity_curve: List of daily equity values
            trades: List of trade dictionaries
            days: Number of days in backtest

        Returns:
            Dictionary with all metrics
        """
        logger.debug("Calculating comprehensive metrics")

        # Returns
        returns = self.calculate_returns(initial_capital, final_equity, days)

        # Sharpe ratio
        sharpe_ratio = self.calculate_sharpe_ratio(equity_curve)

        # Drawdown
        drawdown = self.calculate_max_drawdown(equity_curve)

        # Win rate
        win_rate = self.calculate_win_rate(trades)

        # Profit factor
        profit_factor = self.calculate_profit_factor(trades)

        # Win/loss averages
        avg_win_loss = self.calculate_avg_win_loss(trades)

        # Trade statistics
        trade_stats = self.calculate_trade_stats(trades)

        # Combine all metrics
        all_metrics = {
            **returns,
            'sharpe_ratio': sharpe_ratio,
            **drawdown,
            'win_rate_pct': win_rate,
            'profit_factor': profit_factor,
            **avg_win_loss,
            **trade_stats
        }

        logger.debug(f"Metrics calculated: Sharpe={sharpe_ratio:.2f}, Drawdown={drawdown['max_drawdown_pct']:.2f}%")

        return all_metrics

    def calculate_rolling_sharpe(
        self,
        equity_curve: List[float],
        window: int = 30,
        periods_per_year: int = 252
    ) -> List[float]:
        """
        Calculate rolling Sharpe ratio.

        Args:
            equity_curve: List of equity values
            window: Rolling window size
            periods_per_year: Periods per year

        Returns:
            List of rolling Sharpe values
        """
        if len(equity_curve) < window:
            return []

        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()

        rolling_sharpe = []

        for i in range(window, len(returns) + 1):
            window_returns = returns.iloc[i-window:i]

            if window_returns.std() > 0:
                sharpe = (window_returns.mean() / window_returns.std()) * np.sqrt(periods_per_year)
                rolling_sharpe.append(float(sharpe))
            else:
                rolling_sharpe.append(0.0)

        return rolling_sharpe

    def calculate_consecutive_wins_losses(self, trades: List[Dict]) -> Dict:
        """
        Calculate maximum consecutive wins and losses.

        Args:
            trades: List of trade dictionaries

        Returns:
            Dictionary with max_consecutive_wins, max_consecutive_losses
        """
        if not trades:
            return {'max_consecutive_wins': 0, 'max_consecutive_losses': 0}

        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        last_was_win = None

        for trade in trades:
            is_win = trade.get('is_winner', False) or (trade.get('net_pnl', 0) > 0)

            if is_win:
                if last_was_win:
                    current_streak += 1
                else:
                    current_streak = 1

                max_win_streak = max(max_win_streak, current_streak)

            else:
                if last_was_win is False:
                    current_streak += 1
                else:
                    current_streak = 1

                max_loss_streak = max(max_loss_streak, current_streak)

            last_was_win = is_win

        return {
            'max_consecutive_wins': max_win_streak,
            'max_consecutive_losses': max_loss_streak
        }
