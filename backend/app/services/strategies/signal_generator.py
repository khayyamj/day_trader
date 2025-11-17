"""Signal generator for evaluating strategies and generating trading signals."""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.indicators.indicator_service import IndicatorService
from app.services.strategies.ma_crossover_rsi import MACrossoverRSIStrategy
from app.models.stock import Stock
from app.models.strategy import Strategy
from app.models.signal import Signal
from app.models.trade import Trade
from app.core.logging import get_logger

logger = get_logger("signal_generator")


class SignalGenerator:
    """Service for generating trading signals from strategies."""

    def __init__(self, db: Session):
        """
        Initialize signal generator.

        Args:
            db: Database session
        """
        self.db = db
        self.indicator_service = IndicatorService(db)

    def evaluate_watchlist(
        self,
        strategy_id: int,
        lookback_days: int = 100
    ) -> Dict[str, any]:
        """
        Evaluate all watchlist stocks and generate signals.

        Args:
            strategy_id: Strategy to use for evaluation
            lookback_days: Days of historical data to use

        Returns:
            Dictionary with evaluation results

        Raises:
            ValueError: If strategy not found or inactive
        """
        logger.info(f"Starting watchlist evaluation for strategy {strategy_id}")

        # Get strategy
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        if not strategy.active:
            raise ValueError(f"Strategy {strategy_id} is not active")

        # Get all stocks (watchlist)
        stocks = self.db.query(Stock).all()
        if not stocks:
            logger.warning("No stocks in watchlist")
            return {
                'strategy_id': strategy_id,
                'strategy_name': strategy.name,
                'stocks_evaluated': 0,
                'signals_generated': 0,
                'signals': []
            }

        logger.info(f"Evaluating {len(stocks)} stocks")

        # Initialize strategy instance
        strategy_instance = self._create_strategy_instance(strategy)

        signals_generated = []
        stocks_evaluated = 0

        # Evaluate each stock
        for stock in stocks:
            try:
                signal = self._evaluate_stock(
                    stock=stock,
                    strategy=strategy,
                    strategy_instance=strategy_instance,
                    lookback_days=lookback_days
                )

                if signal:
                    signals_generated.append(signal)

                stocks_evaluated += 1

            except Exception as e:
                logger.error(f"Error evaluating {stock.symbol}: {str(e)}")
                continue

        logger.info(
            f"Watchlist evaluation complete: {stocks_evaluated} stocks evaluated, "
            f"{len(signals_generated)} signals generated"
        )

        return {
            'strategy_id': strategy_id,
            'strategy_name': strategy.name,
            'stocks_evaluated': stocks_evaluated,
            'signals_generated': len(signals_generated),
            'signals': signals_generated
        }

    def _evaluate_stock(
        self,
        stock: Stock,
        strategy: Strategy,
        strategy_instance: MACrossoverRSIStrategy,
        lookback_days: int
    ) -> Optional[Dict]:
        """
        Evaluate a single stock and generate signal if applicable.

        Args:
            stock: Stock to evaluate
            strategy: Strategy model
            strategy_instance: Strategy instance
            lookback_days: Days of historical data

        Returns:
            Signal dictionary if generated, None otherwise
        """
        logger.debug(f"Evaluating {stock.symbol}")

        # Check if stock has sufficient data
        if not self.indicator_service.has_sufficient_data(stock.symbol, min_bars=100):
            logger.debug(f"{stock.symbol}: Insufficient data for evaluation")
            return None

        # Get indicators for stock
        required_indicators = strategy_instance.get_required_indicators()

        try:
            df = self.indicator_service.get_indicators_for_stock(
                symbol=stock.symbol,
                indicators=required_indicators,
                lookback_days=lookback_days,
                save_to_db=False
            )
        except Exception as e:
            logger.error(f"Error getting indicators for {stock.symbol}: {str(e)}")
            return None

        # Check current position
        current_position = self._get_current_position(stock.id)

        # Generate signal
        try:
            trading_signal = strategy_instance.generate_signal(
                df=df,
                current_position=current_position
            )
        except Exception as e:
            logger.error(f"Error generating signal for {stock.symbol}: {str(e)}")
            return None

        # Log signal to database
        signal_record = self._log_signal(
            strategy_id=strategy.id,
            stock_id=stock.id,
            trading_signal=trading_signal
        )

        # Return signal info if not HOLD
        if trading_signal.signal_type.value != "hold":
            logger.info(
                f"Signal generated for {stock.symbol}: {trading_signal.signal_type.value.upper()} "
                f"- {trading_signal.trigger_reason}"
            )

            return {
                'signal_id': signal_record.id,
                'symbol': stock.symbol,
                'signal_type': trading_signal.signal_type.value,
                'signal_time': trading_signal.timestamp.isoformat(),
                'trigger_reason': trading_signal.trigger_reason,
                'indicator_values': trading_signal.indicator_values,
                'market_context': trading_signal.market_context,
                'executed': False
            }

        return None

    def _get_current_position(self, stock_id: int) -> Optional[str]:
        """
        Get current position for a stock.

        Args:
            stock_id: Stock ID

        Returns:
            'long' if position exists, None otherwise
        """
        # Check if there's an open trade for this stock
        open_trade = self.db.query(Trade).filter(
            Trade.stock_id == stock_id,
            Trade.exit_time.is_(None)
        ).first()

        if open_trade:
            return 'long'

        return None

    def _log_signal(
        self,
        strategy_id: int,
        stock_id: int,
        trading_signal: any
    ) -> Signal:
        """
        Log signal to database.

        Args:
            strategy_id: Strategy ID
            stock_id: Stock ID
            trading_signal: TradingSignal object

        Returns:
            Created Signal record
        """
        signal = Signal(
            strategy_id=strategy_id,
            stock_id=stock_id,
            signal_type=trading_signal.signal_type.value,
            signal_time=trading_signal.timestamp,
            executed=False,
            reasons=[trading_signal.trigger_reason],
            indicator_values=trading_signal.indicator_values,
            market_context=trading_signal.market_context
        )

        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)

        logger.debug(f"Signal logged: {signal.id}")

        return signal

    def _create_strategy_instance(self, strategy: Strategy):
        """
        Create strategy instance from database model.

        Args:
            strategy: Strategy model

        Returns:
            Strategy instance

        Raises:
            ValueError: If strategy type not supported
        """
        # For now, we only support MA Crossover + RSI
        if strategy.name == "MA Crossover + RSI":
            return MACrossoverRSIStrategy(parameters=strategy.parameters)

        raise ValueError(f"Unsupported strategy type: {strategy.name}")

    def evaluate_single_stock(
        self,
        symbol: str,
        strategy_id: int,
        lookback_days: int = 100
    ) -> Dict:
        """
        Evaluate a single stock and generate signal.

        Args:
            symbol: Stock symbol
            strategy_id: Strategy to use
            lookback_days: Days of historical data

        Returns:
            Signal dictionary

        Raises:
            ValueError: If stock or strategy not found
        """
        logger.info(f"Evaluating single stock: {symbol}")

        # Get stock
        stock = self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found")

        # Get strategy
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        # Create strategy instance
        strategy_instance = self._create_strategy_instance(strategy)

        # Evaluate stock
        signal = self._evaluate_stock(
            stock=stock,
            strategy=strategy,
            strategy_instance=strategy_instance,
            lookback_days=lookback_days
        )

        if signal:
            return {
                'symbol': symbol,
                'signal_generated': True,
                'signal': signal
            }
        else:
            return {
                'symbol': symbol,
                'signal_generated': False,
                'message': 'No actionable signal generated (HOLD)'
            }
