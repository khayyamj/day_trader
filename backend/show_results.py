#!/usr/bin/env python
"""Display backtest results from database."""
from app.db.session import SessionLocal
from app.models.backtest import BacktestRun
from app.models.stock import Stock

db = SessionLocal()

print('\n' + '='*80)
print('VALIDATION BACKTEST RESULTS')
print('='*80)
print(f"{'Symbol':<10} {'Return %':<12} {'Sharpe':<10} {'Max DD %':<12} {'Win Rate %':<12} {'Trades':<10}")
print('-'*80)

backtests = db.query(BacktestRun).order_by(BacktestRun.id).all()
results = []

for bt in backtests:
    stock = db.query(Stock).filter(Stock.id == bt.stock_id).first()
    ret = float(bt.total_return_pct) if bt.total_return_pct else 0
    sharpe = float(bt.sharpe_ratio) if bt.sharpe_ratio else 0
    dd = float(bt.max_drawdown_pct) if bt.max_drawdown_pct else 0
    wr = float(bt.win_rate_pct) if bt.win_rate_pct else 0

    print(f"{stock.symbol:<10} {ret:<12.2f} {sharpe:<10.2f} {dd:<12.2f} {wr:<12.2f} {bt.total_trades:<10}")

    results.append({
        'symbol': stock.symbol,
        'return': ret,
        'sharpe': sharpe,
        'dd': dd,
        'wr': wr,
        'trades': bt.total_trades
    })

if results:
    avg_return = sum(r['return'] for r in results) / len(results)
    avg_sharpe = sum(r['sharpe'] for r in results) / len(results)
    avg_dd = sum(r['dd'] for r in results) / len(results)
    avg_wr = sum(r['wr'] for r in results) / len(results)

    print('-'*80)
    print(f"{'AVERAGE':<10} {avg_return:<12.2f} {avg_sharpe:<10.2f} {avg_dd:<12.2f} {avg_wr:<12.2f}")
    print('='*80)

    print('\nDECISION POINT EVALUATION:')
    print('Target: Sharpe > 1.0, Max Drawdown < 25%')
    print()

    passing = [r for r in results if r['sharpe'] > 1.0 and abs(r['dd']) < 25]
    print(f"Stocks meeting criteria: {len(passing)}/{len(results)}")

    if passing:
        print('\nPassing stocks:')
        for r in passing:
            print(f"  ✓ {r['symbol']}: Sharpe={r['sharpe']:.2f}, Drawdown={r['dd']:.2f}%")

    print(f"\nAverage Sharpe: {avg_sharpe:.2f} {'✓ PASS' if avg_sharpe > 1.0 else '✗ FAIL'} (target > 1.0)")

db.close()
