#!/usr/bin/env python
"""
Parameter sensitivity testing for MA Crossover + RSI strategy.

Tests EMA period variations (±20%) to evaluate strategy robustness.
"""
import json
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.backtesting.backtest_engine import BacktestEngine
from app.models.strategy import Strategy
from app.core.logging import get_logger

logger = get_logger("parameter_sensitivity")

# Test stocks (using top 3 performers from validation)
TEST_STOCKS = ["GOOGL", "JPM", "MSFT"]

# Date range: 1 year
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=365)

# Parameter configurations to test
PARAMETER_CONFIGS = [
    {
        'name': 'Baseline',
        'params': {'fast_ema': 20, 'slow_ema': 50, 'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70}
    },
    {
        'name': 'Faster (-20%)',
        'params': {'fast_ema': 16, 'slow_ema': 40, 'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70}
    },
    {
        'name': 'Slower (+20%)',
        'params': {'fast_ema': 24, 'slow_ema': 60, 'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70}
    }
]


def run_sensitivity_tests():
    """Run parameter sensitivity tests."""
    db: Session = SessionLocal()

    try:
        print(f"\n{'='*90}")
        print("PARAMETER SENSITIVITY TESTING")
        print(f"{'='*90}")
        print(f"Test Period: {START_DATE} to {END_DATE}")
        print(f"Stocks: {', '.join(TEST_STOCKS)}")
        print(f"Configurations: {len(PARAMETER_CONFIGS)}")
        print(f"{'='*90}\n")

        # Get or create test strategies
        strategies = {}
        for config in PARAMETER_CONFIGS:
            strategy_name = f"MA Crossover + RSI ({config['name']})"

            # Check if strategy exists
            strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()

            if not strategy:
                # Create new strategy
                strategy = Strategy(
                    name=strategy_name,
                    description=f"Parameter sensitivity test: {config['name']}",
                    parameters=json.dumps(config['params']),
                    active=True,
                    status='active'
                )
                db.add(strategy)
                db.commit()
                db.refresh(strategy)
                logger.info(f"Created strategy: {strategy_name} (ID: {strategy.id})")

            strategies[config['name']] = strategy

        print(f"Created/loaded {len(strategies)} strategy configurations\n")

        # Run backtests for each configuration
        engine = BacktestEngine(db)
        results = {}

        for config in PARAMETER_CONFIGS:
            config_name = config['name']
            strategy = strategies[config_name]

            print(f"\n{'─'*90}")
            print(f"Configuration: {config_name}")
            print(f"Parameters: EMA({config['params']['fast_ema']}/{config['params']['slow_ema']}), RSI({config['params']['rsi_period']})")
            print(f"{'─'*90}")

            results[config_name] = {}

            for symbol in TEST_STOCKS:
                print(f"\n  Testing {symbol}...", end=' ')
                logger.info(f"Running {config_name} backtest for {symbol}")

                try:
                    result = engine.run_backtest(
                        strategy_id=strategy.id,
                        symbol=symbol,
                        start_date=START_DATE,
                        end_date=END_DATE,
                        initial_capital=100000.0,
                        slippage_pct=0.001,
                        commission_per_trade=1.0
                    )

                    results[config_name][symbol] = {
                        'return': result.get('total_return_pct', 0),
                        'sharpe': result.get('sharpe_ratio', 0),
                        'drawdown': result.get('max_drawdown_pct', 0),
                        'trades': result.get('total_trades', 0)
                    }

                    print(f"Return: {result.get('total_return_pct', 0):6.2f}%, Sharpe: {result.get('sharpe_ratio', 0):5.2f}")

                except Exception as e:
                    logger.error(f"Error in {config_name} backtest for {symbol}: {str(e)}")
                    print(f"ERROR: {str(e)}")
                    results[config_name][symbol] = None

        # Print summary comparison table
        print(f"\n\n{'='*90}")
        print("PARAMETER SENSITIVITY SUMMARY")
        print(f"{'='*90}")

        for symbol in TEST_STOCKS:
            print(f"\n{symbol}:")
            print(f"  {'Config':<20} {'Return %':<12} {'Sharpe':<10} {'Max DD %':<12} {'Trades':<10}")
            print(f"  {'-'*70}")

            for config in PARAMETER_CONFIGS:
                config_name = config['name']
                if results[config_name].get(symbol):
                    r = results[config_name][symbol]
                    print(f"  {config_name:<20} {r['return']:<12.2f} {r['sharpe']:<10.2f} {r['drawdown']:<12.2f} {r['trades']:<10}")
                else:
                    print(f"  {config_name:<20} {'ERROR':<12}")

        # Calculate averages across stocks for each configuration
        print(f"\n\n{'='*90}")
        print("AVERAGE ACROSS ALL STOCKS")
        print(f"{'='*90}")
        print(f"{'Config':<20} {'Avg Return %':<15} {'Avg Sharpe':<12} {'Avg Max DD %':<15}")
        print(f"{'-'*90}")

        for config in PARAMETER_CONFIGS:
            config_name = config['name']
            valid_results = [r for r in results[config_name].values() if r is not None]

            if valid_results:
                avg_return = sum(r['return'] for r in valid_results) / len(valid_results)
                avg_sharpe = sum(r['sharpe'] for r in valid_results) / len(valid_results)
                avg_dd = sum(r['drawdown'] for r in valid_results) / len(valid_results)

                print(f"{config_name:<20} {avg_return:<15.2f} {avg_sharpe:<12.2f} {avg_dd:<15.2f}")
            else:
                print(f"{config_name:<20} {'No valid results':<15}")

        print(f"{'='*90}\n")

        # Analysis
        print("\nANALYSIS:")
        print("─"*90)

        baseline_results = [r for r in results['Baseline'].values() if r]
        faster_results = [r for r in results['Faster (-20%)'].values() if r]
        slower_results = [r for r in results['Slower (+20%)'].values() if r]

        if baseline_results and faster_results and slower_results:
            baseline_sharpe = sum(r['sharpe'] for r in baseline_results) / len(baseline_results)
            faster_sharpe = sum(r['sharpe'] for r in faster_results) / len(faster_results)
            slower_sharpe = sum(r['sharpe'] for r in slower_results) / len(slower_results)

            print(f"• Baseline (20/50) avg Sharpe: {baseline_sharpe:.2f}")
            print(f"• Faster (16/40) avg Sharpe:   {faster_sharpe:.2f} ({(faster_sharpe/baseline_sharpe-1)*100:+.1f}%)")
            print(f"• Slower (24/60) avg Sharpe:   {slower_sharpe:.2f} ({(slower_sharpe/baseline_sharpe-1)*100:+.1f}%)")

            if abs(faster_sharpe - baseline_sharpe) / baseline_sharpe < 0.2 and abs(slower_sharpe - baseline_sharpe) / baseline_sharpe < 0.2:
                print(f"\n✓ Strategy is ROBUST: <20% Sharpe variation across parameter changes")
            else:
                print(f"\n⚠ Strategy shows SENSITIVITY: >20% Sharpe variation with parameter changes")

        logger.info("Parameter sensitivity testing completed")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    run_sensitivity_tests()
