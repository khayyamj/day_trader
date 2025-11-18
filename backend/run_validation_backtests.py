#!/usr/bin/env python
"""
Standalone script to run validation backtests for the 5 stocks specified in Task 6.

This script bypasses the API server and runs backtests directly using the backtest engine.
"""
import sys
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.backtesting.backtest_engine import BacktestEngine
from app.models.strategy import Strategy
from app.core.logging import get_logger

logger = get_logger("validation_backtests")

# 5 diverse stocks for testing (tech + finance + energy)
VALIDATION_STOCKS = ["AAPL", "MSFT", "GOOGL", "JPM", "XOM"]

# Date range: 1 year ago to today
END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=365)

# Default parameters
INITIAL_CAPITAL = 100000.0
SLIPPAGE_PCT = 0.001  # 0.1%
COMMISSION_PER_TRADE = 1.0  # $1 per trade


def run_validation_backtests():
    """Run backtests on all validation stocks and print results."""
    db: Session = SessionLocal()

    try:
        # Get the strategy (assuming we have one strategy in the DB)
        strategy = db.query(Strategy).first()

        if not strategy:
            logger.error("No strategy found in database. Please create a strategy first.")
            print("\nERROR: No strategy found in database.")
            print("Please ensure you have created a strategy before running backtests.")
            return 1

        logger.info(f"Using strategy: {strategy.name} (ID: {strategy.id})")
        print(f"\n{'='*80}")
        print(f"VALIDATION BACKTESTS - {START_DATE} to {END_DATE}")
        print(f"Strategy: {strategy.name}")
        print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
        print(f"Slippage: {SLIPPAGE_PCT*100}%")
        print(f"Commission: ${COMMISSION_PER_TRADE} per trade")
        print(f"{'='*80}\n")

        engine = BacktestEngine(db)
        results_summary = []

        for symbol in VALIDATION_STOCKS:
            print(f"\nRunning backtest for {symbol}...")
            logger.info(f"Starting backtest for {symbol}")

            try:
                results = engine.run_backtest(
                    strategy_id=strategy.id,
                    symbol=symbol,
                    start_date=START_DATE,
                    end_date=END_DATE,
                    initial_capital=INITIAL_CAPITAL,
                    slippage_pct=SLIPPAGE_PCT,
                    commission_per_trade=COMMISSION_PER_TRADE
                )

                # Store results for summary table
                results_summary.append({
                    'symbol': symbol,
                    'total_return_pct': results.get('total_return_pct', 0),
                    'sharpe_ratio': results.get('sharpe_ratio'),
                    'max_drawdown_pct': results.get('max_drawdown_pct'),
                    'win_rate_pct': results.get('win_rate_pct'),
                    'total_trades': results.get('total_trades', 0),
                    'final_equity': results.get('final_equity', INITIAL_CAPITAL)
                })

                # Print individual results
                print(f"\n  {symbol} Results:")
                print(f"  ├─ Total Return: {results.get('total_return_pct', 0):.2f}%")
                print(f"  ├─ Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}" if results.get('sharpe_ratio') else "  ├─ Sharpe Ratio: N/A")
                print(f"  ├─ Max Drawdown: {results.get('max_drawdown_pct', 0):.2f}%" if results.get('max_drawdown_pct') else "  ├─ Max Drawdown: N/A")
                print(f"  ├─ Win Rate: {results.get('win_rate_pct', 0):.2f}%" if results.get('win_rate_pct') else "  ├─ Win Rate: N/A")
                print(f"  ├─ Total Trades: {results.get('total_trades', 0)}")
                print(f"  └─ Final Equity: ${results.get('final_equity', INITIAL_CAPITAL):,.2f}")

                logger.info(f"Completed backtest for {symbol}: Return={results.get('total_return_pct', 0):.2f}%, Sharpe={results.get('sharpe_ratio')}")

            except Exception as e:
                logger.error(f"Error running backtest for {symbol}: {str(e)}")
                print(f"  ERROR: {str(e)}")
                results_summary.append({
                    'symbol': symbol,
                    'total_return_pct': None,
                    'sharpe_ratio': None,
                    'max_drawdown_pct': None,
                    'win_rate_pct': None,
                    'total_trades': None,
                    'final_equity': None
                })

        # Print summary table
        print(f"\n{'='*80}")
        print("SUMMARY OF ALL BACKTESTS")
        print(f"{'='*80}")
        print(f"{'Symbol':<10} {'Return %':<12} {'Sharpe':<10} {'Max DD %':<12} {'Win Rate %':<12} {'Trades':<10}")
        print(f"{'-'*80}")

        for result in results_summary:
            symbol = result['symbol']
            ret = f"{result['total_return_pct']:.2f}" if result['total_return_pct'] is not None else "N/A"
            sharpe = f"{result['sharpe_ratio']:.2f}" if result['sharpe_ratio'] is not None else "N/A"
            dd = f"{result['max_drawdown_pct']:.2f}" if result['max_drawdown_pct'] is not None else "N/A"
            wr = f"{result['win_rate_pct']:.2f}" if result['win_rate_pct'] is not None else "N/A"
            trades = f"{result['total_trades']}" if result['total_trades'] is not None else "N/A"

            print(f"{symbol:<10} {ret:<12} {sharpe:<10} {dd:<12} {wr:<12} {trades:<10}")

        # Calculate aggregate metrics
        valid_results = [r for r in results_summary if r['total_return_pct'] is not None]

        if valid_results:
            avg_return = sum(r['total_return_pct'] for r in valid_results) / len(valid_results)
            avg_sharpe = sum(r['sharpe_ratio'] for r in valid_results if r['sharpe_ratio']) / len([r for r in valid_results if r['sharpe_ratio']]) if any(r['sharpe_ratio'] for r in valid_results) else None
            avg_win_rate = sum(r['win_rate_pct'] for r in valid_results if r['win_rate_pct']) / len([r for r in valid_results if r['win_rate_pct']]) if any(r['win_rate_pct'] for r in valid_results) else None

            print(f"{'-'*80}")
            sharpe_str = f"{avg_sharpe:.2f}" if avg_sharpe else "N/A"
            wr_str = f"{avg_win_rate:.2f}" if avg_win_rate else "N/A"
            print(f"{'AVERAGE':<10} {avg_return:.2f}{'':<8} {sharpe_str:<10} {'':<12} {wr_str:<12}")

        print(f"{'='*80}\n")

        # Decision point evaluation
        print("\nDECISION POINT EVALUATION:")
        print("Target Criteria: Sharpe Ratio > 1.0, Max Drawdown < 25%")

        if valid_results:
            passing_stocks = [
                r for r in valid_results
                if r['sharpe_ratio'] and r['sharpe_ratio'] > 1.0
                and r['max_drawdown_pct'] and abs(r['max_drawdown_pct']) < 25
            ]

            print(f"Stocks meeting criteria: {len(passing_stocks)}/{len(valid_results)}")

            if passing_stocks:
                print("\nPassing stocks:")
                for r in passing_stocks:
                    print(f"  - {r['symbol']}: Sharpe={r['sharpe_ratio']:.2f}, Drawdown={r['max_drawdown_pct']:.2f}%")

            if avg_sharpe and avg_sharpe > 1.0:
                print(f"\n✓ Average Sharpe Ratio ({avg_sharpe:.2f}) exceeds target (1.0)")
            else:
                print(f"\n✗ Average Sharpe Ratio ({avg_sharpe:.2f if avg_sharpe else 'N/A'}) below target (1.0)")

        logger.info("Validation backtests completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Fatal error running validation backtests: {str(e)}")
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run_validation_backtests())
