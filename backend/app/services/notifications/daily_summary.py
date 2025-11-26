"""Daily summary email generation service."""
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.trade import Trade
from app.models.stock import Stock
from app.models.signal import Signal
from .notification_manager import notification_manager

logger = logging.getLogger(__name__)


class DailySummaryService:
    """Service for generating and sending daily trading summaries."""

    def __init__(self, db: Session):
        """
        Initialize daily summary service.

        Args:
            db: Database session
        """
        self.db = db

    def generate_daily_summary(self, summary_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Generate daily summary data.

        Args:
            summary_date: Date to generate summary for (defaults to today)

        Returns:
            Dictionary containing summary data
        """
        if summary_date is None:
            summary_date = date.today()

        logger.info(f"Generating daily summary for {summary_date}")

        # Get today's trades
        trades_data = self._get_trades_today(summary_date)

        # Calculate metrics
        total_pnl = self._calculate_total_pnl(trades_data)
        win_rate = self._calculate_win_rate(trades_data)

        # Get open positions
        positions_data = self._get_open_positions()

        # Get watchlist (stocks near signals)
        watchlist_data = self._get_watchlist()

        summary = {
            "date": summary_date.strftime("%Y-%m-%d"),
            "total_pnl": total_pnl,
            "trades_count": len(trades_data),
            "win_rate": win_rate,
            "open_positions": len(positions_data),
            "trades": trades_data,
            "positions": positions_data,
            "watchlist": watchlist_data
        }

        logger.info(
            f"Summary generated: {len(trades_data)} trades, "
            f"P&L: ${total_pnl:.2f}, Win rate: {win_rate:.1f}%"
        )

        return summary

    def _get_trades_today(self, summary_date: date) -> List[Dict[str, Any]]:
        """Get all trades for the specified date."""
        try:
            # Query trades for today
            trades = self.db.query(Trade).filter(
                func.date(Trade.created_at) == summary_date
            ).order_by(Trade.created_at.desc()).all()

            trades_data = []
            for trade in trades:
                # Calculate P&L for closed trades (trades with both entry and exit)
                pnl = None
                if trade.exit_price and trade.entry_price:
                    if trade.action.upper() in ['BUY', 'LONG']:
                        pnl = (trade.exit_price - trade.entry_price) * trade.quantity
                    else:  # SELL, SHORT
                        pnl = (trade.entry_price - trade.exit_price) * trade.quantity

                trades_data.append({
                    "time": trade.created_at.strftime("%H:%M:%S"),
                    "symbol": trade.symbol,
                    "action": trade.action,
                    "quantity": trade.quantity,
                    "price": trade.entry_price or trade.price,
                    "pnl": pnl
                })

            return trades_data

        except Exception as e:
            logger.error(f"Error getting today's trades: {e}")
            return []

    def _calculate_total_pnl(self, trades_data: List[Dict[str, Any]]) -> float:
        """Calculate total P&L from trades."""
        total = 0.0
        for trade in trades_data:
            if trade.get("pnl") is not None:
                total += trade["pnl"]
        return total

    def _calculate_win_rate(self, trades_data: List[Dict[str, Any]]) -> float:
        """Calculate win rate percentage."""
        if not trades_data:
            return 0.0

        completed_trades = [t for t in trades_data if t.get("pnl") is not None]
        if not completed_trades:
            return 0.0

        winning_trades = sum(1 for t in completed_trades if t["pnl"] > 0)
        return (winning_trades / len(completed_trades)) * 100

    def _get_open_positions(self) -> List[Dict[str, Any]]:
        """Get current open positions."""
        try:
            # Query trades with entry but no exit
            open_trades = self.db.query(Trade).filter(
                Trade.entry_price.isnot(None),
                Trade.exit_price.is_(None),
                Trade.status.in_(['OPEN', 'ACTIVE'])
            ).all()

            positions_data = []
            for trade in open_trades:
                # For demo purposes, assume current price = entry price
                # In production, fetch live price from market data
                current_price = trade.entry_price
                unrealized_pnl = 0.0

                if trade.action.upper() in ['BUY', 'LONG']:
                    unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
                else:
                    unrealized_pnl = (trade.entry_price - current_price) * trade.quantity

                positions_data.append({
                    "symbol": trade.symbol,
                    "strategy": trade.strategy.name if trade.strategy else "N/A",
                    "quantity": trade.quantity,
                    "entry_price": trade.entry_price,
                    "current_price": current_price,
                    "unrealized_pnl": unrealized_pnl
                })

            return positions_data

        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []

    def _get_watchlist(self) -> List[Dict[str, Any]]:
        """Get tomorrow's watchlist - stocks near signals."""
        try:
            # Get recent signals from the last 7 days that haven't been acted on
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=7)

            signals = self.db.query(Signal).filter(
                Signal.created_at >= cutoff_date,
                Signal.action.in_(['BUY', 'SELL'])
            ).order_by(Signal.created_at.desc()).limit(10).all()

            watchlist_data = []
            seen_symbols = set()

            for signal in signals:
                if signal.symbol not in seen_symbols:
                    watchlist_data.append({
                        "symbol": signal.symbol,
                        "reason": f"{signal.action} signal from {signal.strategy.name if signal.strategy else 'strategy'}"
                    })
                    seen_symbols.add(signal.symbol)

            # If no signals, add watchlist stocks
            if not watchlist_data:
                stocks = self.db.query(Stock).limit(5).all()
                for stock in stocks:
                    watchlist_data.append({
                        "symbol": stock.symbol,
                        "reason": "Watchlist stock - monitor for signals"
                    })

            return watchlist_data

        except Exception as e:
            logger.error(f"Error getting watchlist: {e}")
            return []

    def send_daily_summary(self, summary_date: Optional[date] = None) -> bool:
        """
        Generate and send daily summary email.

        Args:
            summary_date: Date to generate summary for (defaults to today)

        Returns:
            bool: True if email sent successfully
        """
        try:
            # Generate summary data
            summary = self.generate_daily_summary(summary_date)

            # Send email using notification manager
            success = notification_manager.send_daily_summary(
                date=summary["date"],
                total_pnl=summary["total_pnl"],
                trades_count=summary["trades_count"],
                win_rate=summary["win_rate"],
                open_positions=summary["open_positions"],
                trades=summary["trades"],
                positions=summary["positions"],
                watchlist=summary["watchlist"]
            )

            if success:
                logger.info("Daily summary email sent successfully")
            else:
                logger.error("Failed to send daily summary email")

            return success

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False
