"""Backtest engine for coordinating backtest execution and storage."""
from typing import Dict, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
import time

from app.services.backtesting.simple_backtester import SimpleBacktester
from app.services.indicators.indicator_service import IndicatorService
from app.services.strategies.ma_crossover_rsi import MACrossoverRSIStrategy
from app.models.strategy import Strategy
from app.models.stock import Stock
from app.models.backtest import BacktestRun, BacktestTrade, BacktestEquityCurve
from app.core.logging import get_logger

logger = get_logger("backtest_engine")


class BacktestEngine:
    """
    Engine for running and storing backtests.

    Coordinates:
    - Data fetching
    - Indicator calculation
    - Strategy execution via SimpleBacktester
    - Results storage
    """

    def __init__(self, db: Session):
        """
        Initialize backtest engine.

        Args:
            db: Database session
        """
        self.db = db
        self.indicator_service = IndicatorService(db)

    def run_backtest(
        self,
        strategy_id: int,
        symbol: str,
        start_date: date,
        end_date: date,
        initial_capital: float = 100000.0,
        slippage_pct: float = 0.001,
        commission_per_trade: float = 1.0
    ) -> Dict:
        """
        Run a backtest for a strategy on a stock.

        Args:
            strategy_id: Strategy to test
            symbol: Stock symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            slippage_pct: Slippage percentage
            commission_per_trade: Commission per trade

        Returns:
            Backtest results dictionary

        Raises:
            ValueError: If strategy/stock not found or insufficient data
        """
        logger.info(
            f"Starting backtest: strategy={strategy_id}, symbol={symbol}, "
            f"period={start_date} to {end_date}"
        )

        start_time = time.time()

        # Get strategy
        strategy_model = self.db.query(Strategy).filter(
            Strategy.id == strategy_id
        ).first()

        if not strategy_model:
            raise ValueError(f"Strategy {strategy_id} not found")

        # Get stock
        stock = self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()

        if not stock:
            raise ValueError(f"Stock {symbol} not found")

        # Calculate lookback days needed
        lookback_days = (end_date - start_date).days + 100  # Extra for indicator warm-up

        # Get historical data with indicators
        logger.info(f"Fetching {lookback_days} days of data with indicators")

        try:
            strategy_instance = self._create_strategy_instance(strategy_model)
            required_indicators = strategy_instance.get_required_indicators()

            df = self.indicator_service.get_indicators_for_stock(
                symbol=symbol,
                indicators=required_indicators,
                lookback_days=lookback_days,
                save_to_db=False
            )

        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            raise ValueError(f"Failed to fetch data for {symbol}: {str(e)}")

        # Filter to backtest period
        df_backtest = df[(df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))]

        if len(df_backtest) < 2:
            raise ValueError(
                f"Insufficient data for backtest period: only {len(df_backtest)} bars available"
            )

        logger.info(f"Backtest data ready: {len(df_backtest)} bars")

        # Run backtest
        backtester = SimpleBacktester(
            initial_capital=initial_capital,
            slippage_pct=slippage_pct,
            commission_per_trade=commission_per_trade
        )

        results = backtester.run(
            df=df_backtest,
            strategy=strategy_instance,
            symbol=symbol
        )

        execution_time = time.time() - start_time

        # Save results
        backtest_run = self.save_backtest_results(
            strategy_id=strategy_id,
            stock_id=stock.id,
            results=results,
            execution_time=execution_time
        )

        results['backtest_id'] = backtest_run.id
        results['execution_time_seconds'] = execution_time

        logger.info(f"Backtest {backtest_run.id} completed in {execution_time:.2f}s")

        return results

    def save_backtest_results(
        self,
        strategy_id: int,
        stock_id: int,
        results: Dict,
        execution_time: float
    ) -> BacktestRun:
        """
        Save backtest results to database.

        Args:
            strategy_id: Strategy ID
            stock_id: Stock ID
            results: Backtest results
            execution_time: Execution time in seconds

        Returns:
            Created BacktestRun record
        """
        logger.info(f"Saving backtest results: strategy={strategy_id}, stock={stock_id}")

        # Get strategy for parameters
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()

        # Create backtest run record
        backtest_run = BacktestRun(
            strategy_id=strategy_id,
            stock_id=stock_id,
            start_date=results['start_date'],
            end_date=results['end_date'],
            initial_capital=results['initial_capital'],
            slippage_pct=self._get_backtest_param(results, 'slippage_pct', 0.001),
            commission_per_trade=self._get_backtest_param(results, 'commission_per_trade', 1.0),
            strategy_parameters=strategy.parameters if strategy else {},
            final_equity=results['final_equity'],
            total_return_pct=results['total_return_pct'],
            annualized_return_pct=results.get('annualized_return_pct'),
            sharpe_ratio=results.get('sharpe_ratio'),
            max_drawdown_pct=results.get('max_drawdown_pct'),
            win_rate_pct=results.get('win_rate_pct'),
            profit_factor=results.get('profit_factor'),
            total_trades=results['total_trades'],
            winning_trades=results['winning_trades'],
            losing_trades=results['losing_trades'],
            avg_win=results.get('avg_win'),
            avg_loss=results.get('avg_loss'),
            largest_win=results.get('largest_win'),
            largest_loss=results.get('largest_loss'),
            execution_time_seconds=execution_time,
            bars_processed=results['bars_processed']
        )

        self.db.add(backtest_run)
        self.db.commit()
        self.db.refresh(backtest_run)

        logger.debug(f"Backtest run saved: ID={backtest_run.id}")

        # Save individual trades
        self._save_trades(backtest_run.id, results['trades'])

        # Save equity curve
        self._save_equity_curve(backtest_run.id, results['equity_curve'])

        logger.info(
            f"Backtest results saved: run_id={backtest_run.id}, "
            f"trades={len(results['trades'])}, equity_points={len(results['equity_curve'])}"
        )

        return backtest_run

    def _save_trades(self, backtest_run_id: int, trades: List[Dict]):
        """Save individual trades to database."""
        for trade_data in trades:
            trade = BacktestTrade(
                backtest_run_id=backtest_run_id,
                trade_number=trade_data['trade_number'],
                entry_date=trade_data['entry_date'],
                entry_price=trade_data['entry_price'],
                entry_signal=trade_data['entry_signal'],
                exit_date=trade_data.get('exit_date'),
                exit_price=trade_data.get('exit_price'),
                exit_signal=trade_data.get('exit_signal'),
                shares=trade_data['shares'],
                position_value=trade_data['shares'] * trade_data['entry_price'],
                gross_pnl=trade_data.get('gross_pnl'),
                commission_paid=self._get_backtest_param(trade_data, 'commission', 2.0),
                slippage_cost=0.0,  # Will calculate from trade data
                net_pnl=trade_data.get('net_pnl'),
                return_pct=trade_data.get('return_pct'),
                holding_period_days=trade_data.get('holding_period_days'),
                is_winner=trade_data.get('is_winner'),
                entry_indicators=trade_data.get('entry_indicators', {}),
                entry_market_context=trade_data.get('entry_market_context', {})
            )

            self.db.add(trade)

        self.db.commit()
        logger.debug(f"Saved {len(trades)} trades")

    def _save_equity_curve(self, backtest_run_id: int, equity_curve: List[Dict]):
        """Save equity curve points to database."""
        peak_equity = equity_curve[0]['equity'] if equity_curve else 0.0

        for i, point in enumerate(equity_curve):
            # Calculate daily return
            if i > 0:
                prev_equity = equity_curve[i-1]['equity']
                daily_return_pct = (point['equity'] / prev_equity - 1) * 100 if prev_equity > 0 else 0.0
            else:
                daily_return_pct = 0.0

            # Calculate drawdown from peak
            peak_equity = max(peak_equity, point['equity'])
            drawdown_pct = (point['equity'] / peak_equity - 1) * 100 if peak_equity > 0 else 0.0

            equity_point = BacktestEquityCurve(
                backtest_run_id=backtest_run_id,
                date=point['date'],
                equity=point['equity'],
                cash=point['cash'],
                position_value=point.get('position_value', 0.0),
                daily_return_pct=daily_return_pct,
                drawdown_pct=drawdown_pct
            )

            self.db.add(equity_point)

        self.db.commit()
        logger.debug(f"Saved {len(equity_curve)} equity curve points")

    def get_backtest_results(self, backtest_id: int) -> Optional[Dict]:
        """
        Retrieve backtest results by ID.

        Args:
            backtest_id: Backtest run ID

        Returns:
            Backtest results dictionary or None

        Raises:
            ValueError: If backtest not found
        """
        backtest = self.db.query(BacktestRun).filter(
            BacktestRun.id == backtest_id
        ).first()

        if not backtest:
            raise ValueError(f"Backtest {backtest_id} not found")

        return {
            'backtest_id': backtest.id,
            'symbol': backtest.stock.symbol,
            'strategy_name': backtest.strategy.name,
            'start_date': backtest.start_date,
            'end_date': backtest.end_date,
            'initial_capital': float(backtest.initial_capital),
            'final_equity': float(backtest.final_equity),
            'total_return_pct': float(backtest.total_return_pct),
            'annualized_return_pct': float(backtest.annualized_return_pct) if backtest.annualized_return_pct else None,
            'sharpe_ratio': float(backtest.sharpe_ratio) if backtest.sharpe_ratio else None,
            'max_drawdown_pct': float(backtest.max_drawdown_pct) if backtest.max_drawdown_pct else None,
            'win_rate_pct': float(backtest.win_rate_pct) if backtest.win_rate_pct else None,
            'profit_factor': float(backtest.profit_factor) if backtest.profit_factor else None,
            'total_trades': backtest.total_trades,
            'winning_trades': backtest.winning_trades,
            'losing_trades': backtest.losing_trades,
            'execution_time_seconds': float(backtest.execution_time_seconds) if backtest.execution_time_seconds else None
        }

    def _create_strategy_instance(self, strategy: Strategy) -> BaseStrategy:
        """Create strategy instance from database model."""
        if strategy.name == "MA Crossover + RSI":
            return MACrossoverRSIStrategy(parameters=strategy.parameters)

        raise ValueError(f"Unsupported strategy type: {strategy.name}")

    def _get_backtest_param(self, data: Dict, key: str, default: any) -> any:
        """Safely get backtest parameter with default."""
        return data.get(key, default)


import pd
