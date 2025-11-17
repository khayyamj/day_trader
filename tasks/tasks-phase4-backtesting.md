# Phase 4: Backtesting System (Weeks 7-8)

## PRD Reference

**Source:** `/PRD.md`
**Key Requirements:**
- Implement backtesting system to validate strategy on historical data (1 year)
- Include realistic slippage (0.1%) and commissions ($1 per trade)
- Calculate comprehensive performance metrics: returns, Sharpe ratio, max drawdown, win rate, profit factor
- Test on 5+ different stocks to validate strategy robustness
- Verify no look-ahead bias (signal on close, execute on next open)
- **Decision Point**: Strategy must achieve Sharpe ratio >1.0 and max drawdown <25% to proceed
- Store all backtest results for comparison and analysis

**Development Approach:** Implementation-first with manual testing, automated tests and documentation at end of cycle

## Relevant Files

### To Be Created:
- `backend/app/services/backtesting/` - Backtesting services directory
- `backend/app/services/backtesting/backtest_engine.py` - Main backtest executor
- `backend/app/services/backtesting/metrics.py` - Performance metrics calculator
- `backend/app/services/backtesting/simple_backtester.py` - Simple custom backtester (if not using Backtrader)
- `backend/app/api/endpoints/backtests.py` - Backtest API endpoints
- `backend/app/schemas/backtest.py` - Backtest schemas
- `backend/app/models/backtest.py` - Backtest results models (backtest_runs, backtest_trades, backtest_equity_curve)

### Files to Modify:
- `backend/app/main.py` - Add backtest routes
- `backend/app/db/base.py` - Import backtest models
- `backend/alembic/` - Create migration for backtest tables
- `backend/requirements.txt` - Add backtrader (if using)

### Notes

- Focus on implementing backtesting that produces verifiable results
- Test with known data scenarios and compare with expected outcomes
- Validate metrics calculations by hand-checking sample trades
- Week 8 is dedicated to running validation backtests and analyzing results
- Automated tests will be created at end of Phase 4

## Tasks

| Task |  #  | Status | Description                               |     | Dependencies | Pts | Time Spent |
| :--: | :-: | :----: | ----------------------------------------- | :-: | :----------: | :-: | :--------: |
|  1   |     |   ✅   | **Integrate Backtesting Framework**       | 🟢  |      -       |  -  |   1h 5m    |
|      |  1  |   ✅   | Research Backtrader vs simple custom      | 🟢  |      -       |  2  |    10m     |
|      |     |        | implementation (decision: start           |     |              |     |            |
|      |     |        | simple, upgrade if needed)                |     |              |     |            |
|      |  2  |   ✅   | Create models/backtest.py with            | 🟢  |      -       |  5  |    35m     |
|      |     |        | BacktestRun, BacktestTrade,               |     |              |     |            |
|      |     |        | BacktestEquityCurve models per PRD        |     |              |     |            |
|      |     |        | schema                                    |     |              |     |            |
|      |  3  |   ✅   | Create Alembic migration for backtest     | 🟢  |      -       |  2  |    10m     |
|      |     |        | tables with indexes                       |     |              |     |            |
|      |  4  |   ✅   | Run migration and verify tables in DB     | 🟢  |      -       | 0.5 |    5m      |
|      |  5  |   ✅   | Create                                    | 🟢  |      -       |  3  |    20m     |
|      |     |        | services/backtesting/backtest_engine.py   |     |              |     |            |
|      |     |        | with BacktestEngine class                 |     |              |     |            |
|      |  6  |   ✅   | Decide on simple custom backtester for    | 🟢  |      -       |  1  |    5m      |
|      |     |        | MVP (easier to understand and debug)      |     |              |     |            |
|  2   |     |   ✅   | **Implement Backtest Execution Service**  | 🟢  |      -       |  -  |   3h 30m   |
|      |  1  |   ✅   | Create                                    | 🟢  |      -       |  8  |    60m     |
|      |     |        | services/backtesting/simple_backtester.py |     |              |     |            |
|      |     |        | with SimpleBacktester class               |     |              |     |            |
|      |  2  |   ✅   | Implement run() method: iterate through   | 🟢  |      -       |  8  |    60m     |
|      |     |        | bars, calculate indicators, generate      |     |              |     |            |
|      |     |        | signals, execute trades                   |     |              |     |            |
|      |  3  |   ✅   | Implement trade execution logic with      | 🟢  |      -       |  5  |    60m     |
|      |     |        | proper timing: signal on close,           |     |              |     |            |
|      |     |        | execute on next open (no look-ahead)      |     |              |     |            |
|      |  4  |   ✅   | Add slippage modeling: buy at open *     | 🟢  |      -       |  3  |    60m     |
|      |     |        | 1.001, sell at open * 0.999 (0.1%         |     |              |     |            |
|      |     |        | slippage)                                 |     |              |     |            |
|      |  5  |   ✅   | Add commission modeling: $1 per trade     | 🟢  |      -       |  2  |    60m     |
|      |     |        | (IBKR typical cost)                       |     |              |     |            |
|      |  6  |   ✅   | Implement position sizing: calculate      | 🟢  |      -       |  3  |    60m     |
|      |     |        | shares based on available capital         |     |              |     |            |
|      |     |        | (use 95% of cash)                         |     |              |     |            |
|      |  7  |   ✅   | Track portfolio state: cash, positions,   | 🟢  |      -       |  3  |    60m     |
|      |     |        | equity curve over time                    |     |              |     |            |
|      |  8  |   -    | Implement stop-loss and take-profit       | 🟡  |     2.3      |  5  |     -      |
|      |     |        | execution logic during backtest           |     |              |     |            |
|      |  9  |   ✅   | Test backtester manually with simple      | 🟢  |      -       |  3  |     -      |
|      |     |        | data (10 bars, known signals) and         |     |              |     |            |
|      |     |        | verify trade execution                    |     |              |     |            |
|  3   |     |   ✅   | **Build Performance Metrics Calculator**  | 🟢  |      -       |  -  |   1h 30m   |
|      |  1  |   ✅   | Create services/backtesting/metrics.py    | 🟢  |      -       |  5  |    10m     |
|      |     |        | with MetricsCalculator class              |     |              |     |            |
|      |  2  |   ✅   | Implement calculate_returns(): total,     | 🟢  |      -       |  3  |    10m     |
|      |     |        | annualized, percentage return             |     |              |     |            |
|      |  3  |   ✅   | Implement calculate_sharpe_ratio():       | 🟢  |      -       |  3  |    15m     |
|      |     |        | (return - risk_free_rate) / std_dev       |     |              |     |            |
|      |  4  |   ✅   | Implement calculate_max_drawdown():       | 🟢  |      -       |  3  |    15m     |
|      |     |        | largest peak-to-trough decline            |     |              |     |            |
|      |  5  |   ✅   | Implement calculate_win_rate(): winning   | 🟢  |      -       |  2  |    10m     |
|      |     |        | trades / total trades                     |     |              |     |            |
|      |  6  |   ✅   | Implement calculate_profit_factor():      | 🟢  |      -       |  2  |    10m     |
|      |     |        | gross_profit / gross_loss                 |     |              |     |            |
|      |  7  |   ✅   | Implement calculate_avg_win_loss():       | 🟢  |      -       |  2  |    10m     |
|      |     |        | average win amount, average loss          |     |              |     |            |
|      |     |        | amount                                    |     |              |     |            |
|      |  8  |   ✅   | Implement calculate_trade_stats(): total  | 🟢  |      -       |  2  |    10m     |
|      |     |        | trades, winning, losing counts            |     |              |     |            |
|      |  9  |   ✅   | Test metrics manually: create sample      | 🟢  |      -       |  2  |     -      |
|      |     |        | equity curve, verify all metrics          |     |              |     |            |
|      |     |        | correct                                   |     |              |     |            |
|  4   |     |   ✅   | **Create Backtest Results Storage**       | 🟢  |      -       |  -  |   1h 0m    |
|      |  1  |   ✅   | Implement save_backtest_results() in      | 🟢  |      -       |  5  |    20m     |
|      |     |        | BacktestEngine that stores run            |     |              |     |            |
|      |     |        | metadata to backtest_runs table           |     |              |     |            |
|      |  2  |   ✅   | Save individual trades to                 | 🟢  |      -       |  3  |    20m     |
|      |     |        | backtest_trades table with entry/exit     |     |              |     |            |
|      |     |        | details, P&L                              |     |              |     |            |
|      |  3  |   ✅   | Save equity curve to                      | 🟢  |      -       |  2  |    20m     |
|      |     |        | backtest_equity_curve table (daily        |     |              |     |            |
|      |     |        | portfolio values)                         |     |              |     |            |
|      |  4  |   ✅   | Add unique constraint on backtest_runs:   | 🟢  |      -       |  2  |     -      |
|      |     |        | (strategy_id, symbol, date_range,         |     |              |     |            |
|      |     |        | parameters)                               |     |              |     |            |
|      |  5  |   ✅   | Implement get_backtest_results() method   | 🟢  |      -       |  2  |    20m     |
|      |     |        | to retrieve stored backtest by ID         |     |              |     |            |
|      |  6  |   ✅   | Test storage by running backtest and      | 🟢  |      -       |  2  |     -      |
|      |     |        | querying DB to verify all data saved      |     |              |     |            |
|  5   |     |   ✅   | **Build Backtest API Endpoints**          | 🟢  |      -       |  -  |   2h 0m    |
|      |  1  |   ✅   | Create schemas/backtest.py with           | 🟢  |      -       |  3  |    30m     |
|      |     |        | BacktestRequest, BacktestResponse,        |     |              |     |            |
|      |     |        | BacktestMetrics schemas                   |     |              |     |            |
|      |  2  |   ✅   | Create api/endpoints/backtests.py         | 🟢  |      -       |  3  |    25m     |
|      |  3  |   ✅   | Implement POST /api/backtests to run      | 🟢  |      -       |  5  |    25m     |
|      |     |        | new backtest with params: strategy_id,    |     |              |     |            |
|      |     |        | symbol, start/end date                    |     |              |     |            |
|      |  4  |   -    | Make backtest execution async (long       | 🟡  |     5.3      |  3  |     -      |
|      |     |        | running) and return job ID                |     |              |     |            |
|      |  5  |   ✅   | Implement GET /api/backtests/{id} to      | 🟢  |      -       |  2  |    25m     |
|      |     |        | retrieve backtest results                 |     |              |     |            |
|      |  6  |   ✅   | Implement GET /api/backtests to list      | 🟢  |      -       |  2  |    25m     |
|      |     |        | all backtests with summary metrics        |     |              |     |            |
|      |  7  |   ✅   | Implement GET                             | 🟢  |      -       |  2  |    25m     |
|      |     |        | /api/backtests/{id}/trades to get         |     |              |     |            |
|      |     |        | detailed trade list                       |     |              |     |            |
|      |  8  |   ✅   | Implement GET                             | 🟢  |      -       |  2  |    25m     |
|      |     |        | /api/backtests/{id}/equity-curve for      |     |              |     |            |
|      |     |        | chart data                                |     |              |     |            |
|      |  9  |   ✅   | Manually test backtest API: POST to       | 🟢  |      -       |  2  |     -      |
|      |     |        | run AAPL 1-year backtest, GET             |     |              |     |            |
|      |     |        | results                                   |     |              |     |            |
|  6   |     |   -    | **Run Validation Backtests**              | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Select 5 diverse stocks for testing:      | 🟢  |      5       |  1  |     -      |
|      |     |        | AAPL, MSFT, GOOGL, JPM, XOM (tech +       |     |              |     |            |
|      |     |        | finance + energy)                         |     |              |     |            |
|      |  2  |   -    | Run 1-year backtest for each stock        | 🟡  |     6.1      |  5  |     -      |
|      |     |        | using default strategy parameters         |     |              |     |            |
|      |  3  |   -    | Analyze results for each stock:           | 🟡  |     6.2      |  3  |     -      |
|      |     |        | record Sharpe ratio, max drawdown,        |     |              |     |            |
|      |     |        | win rate, total return                    |     |              |     |            |
|      |  4  |   -    | Test parameter sensitivity: run           | 🟡  |     6.3      |  5  |     -      |
|      |     |        | backtests with EMA periods ±20%           |     |              |     |            |
|      |     |        | (e.g., EMA 16/24 instead of 20,           |     |              |     |            |
|      |     |        | 40/60 instead of 50)                      |     |              |     |            |
|      |  5  |   -    | Verify no look-ahead bias: manually       | 🟡  |     6.2      |  3  |     -      |
|      |     |        | inspect sample trades to ensure           |     |              |     |            |
|      |     |        | signal on close, execute on next          |     |              |     |            |
|      |     |        | open                                      |     |              |     |            |
|      |  6  |   -    | Calculate aggregate metrics across all    | 🟡  |     6.3-6.5  |  2  |     -      |
|      |     |        | 5 stocks: average Sharpe, average         |     |              |     |            |
|      |     |        | win rate, etc.                            |     |              |     |            |
|      |  7  |   -    | **DECISION POINT**: Evaluate if           | 🟡  |     6.6      |  3  |     -      |
|      |     |        | strategy passes criteria (Sharpe >1.0,    |     |              |     |            |
|      |     |        | drawdown <25%, positive returns)          |     |              |     |            |
|      |  8  |   -    | Document backtest results in              | 🟡  |     6.7      |  3  |     -      |
|      |     |        | docs/BACKTEST_RESULTS.md with tables,     |     |              |     |            |
|      |     |        | analysis, decision                        |     |              |     |            |
|  7   |     |   -    | **Write Tests for Backtesting System**    | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create tests/test_simple_backtester.py    | 🟢  |      6       |  8  |     -      |
|      |     |        | with test scenarios: buy signal,          |     |              |     |            |
|      |     |        | sell, stop-loss hit                       |     |              |     |            |
|      |  2  |   -    | Create tests/test_metrics.py testing      | 🟡  |     7.1      |  5  |     -      |
|      |     |        | all performance metrics calculations      |     |              |     |            |
|      |  3  |   -    | Create tests/test_backtest_storage.py     | 🟡  |     7.1      |  3  |     -      |
|      |     |        | testing save/retrieve backtest            |     |              |     |            |
|      |     |        | results                                   |     |              |     |            |
|      |  4  |   -    | Create tests/test_backtests_api.py        | 🟡  |     7.1      |  3  |     -      |
|      |     |        | testing API endpoints                     |     |              |     |            |
|      |  5  |   -    | Run pytest and ensure all Phase 4         | 🟡  |     7.2-7.4  |  1  |     -      |
|      |     |        | tests pass with 70%+ coverage             |     |              |     |            |
|  8   |     |   ✅   | **Document Backtesting Results and        | 🟢  |      -       |  -  |   1h 30m   |
|      |     |        | Methodology**                             |     |              |     |            |
|      |  1  |   ✅   | Create docs/BACKTESTING.md documenting    | 🟢  |      -       |  3  |    30m     |
|      |     |        | backtesting approach, framework           |     |              |     |            |
|      |     |        | choice                                    |     |              |     |            |
|      |  2  |   ✅   | Document slippage and commission          | 🟢  |      -       |  2  |    30m     |
|      |     |        | assumptions (0.1%, $1)                    |     |              |     |            |
|      |  3  |   ✅   | Document no look-ahead bias verification  | 🟢  |      -       |  2  |    30m     |
|      |     |        | (signal on close, execute on next         |     |              |     |            |
|      |     |        | open)                                     |     |              |     |            |
|      |  4  |   ✅   | Document all performance metrics          | 🟢  |      -       |  2  |    30m     |
|      |     |        | calculated and their interpretations      |     |              |     |            |
|      |  5  |   ✅   | Include backtest API examples in          | 🟢  |      -       |  2  |    30m     |
|      |     |        | documentation                             |     |              |     |            |
|      |  6  |   ✅   | Document interpretation guide: what       | 🟢  |      -       |  3  |    30m     |
|      |     |        | good metrics look like (Sharpe >1.0,      |     |              |     |            |
|      |     |        | drawdown <25%, win rate 40-60%)           |     |              |     |            |

---

**Phase 4 Total Sprint Points:** ~167 points
**Estimated Duration:** 2 weeks
**Key Deliverables:** Backtesting system functional, validation backtests completed on 5+ stocks, strategy validated (or rejected), comprehensive backtest results documented, decision made to proceed or refine strategy
