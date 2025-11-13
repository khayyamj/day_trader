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
|  1   |     |   -    | **Integrate Backtesting Framework**       | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Research Backtrader vs simple custom      | 🟢  |      -       |  2  |     -      |
|      |     |        | implementation (decision: start           |     |              |     |            |
|      |     |        | simple, upgrade if needed)                |     |              |     |            |
|      |  2  |   -    | Create models/backtest.py with            | 🟢  |      -       |  5  |     -      |
|      |     |        | BacktestRun, BacktestTrade,               |     |              |     |            |
|      |     |        | BacktestEquityCurve models per PRD        |     |              |     |            |
|      |     |        | schema                                    |     |              |     |            |
|      |  3  |   -    | Create Alembic migration for backtest     | 🟡  |     1.2      |  2  |     -      |
|      |     |        | tables with indexes                       |     |              |     |            |
|      |  4  |   -    | Run migration and verify tables in DB     | 🟡  |     1.3      | 0.5 |     -      |
|      |  5  |   -    | Create                                    | 🟢  |      -       |  3  |     -      |
|      |     |        | services/backtesting/backtest_engine.py   |     |              |     |            |
|      |     |        | with BacktestEngine class                 |     |              |     |            |
|      |  6  |   -    | Decide on simple custom backtester for    | 🟡  |     1.5      |  1  |     -      |
|      |     |        | MVP (easier to understand and debug)      |     |              |     |            |
|  2   |     |   -    | **Implement Backtest Execution Service**  | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create                                    | 🟢  |      1       |  8  |     -      |
|      |     |        | services/backtesting/simple_backtester.py |     |              |     |            |
|      |     |        | with SimpleBacktester class               |     |              |     |            |
|      |  2  |   -    | Implement run() method: iterate through   | 🟡  |     2.1      |  8  |     -      |
|      |     |        | bars, calculate indicators, generate      |     |              |     |            |
|      |     |        | signals, execute trades                   |     |              |     |            |
|      |  3  |   -    | Implement trade execution logic with      | 🟡  |     2.2      |  5  |     -      |
|      |     |        | proper timing: signal on close,           |     |              |     |            |
|      |     |        | execute on next open (no look-ahead)      |     |              |     |            |
|      |  4  |   -    | Add slippage modeling: buy at open *     | 🟡  |     2.3      |  3  |     -      |
|      |     |        | 1.001, sell at open * 0.999 (0.1%         |     |              |     |            |
|      |     |        | slippage)                                 |     |              |     |            |
|      |  5  |   -    | Add commission modeling: $1 per trade     | 🟡  |     2.3      |  2  |     -      |
|      |     |        | (IBKR typical cost)                       |     |              |     |            |
|      |  6  |   -    | Implement position sizing: calculate      | 🟡  |     2.3      |  3  |     -      |
|      |     |        | shares based on available capital         |     |              |     |            |
|      |     |        | (use 95% of cash)                         |     |              |     |            |
|      |  7  |   -    | Track portfolio state: cash, positions,   | 🟡  |     2.2      |  3  |     -      |
|      |     |        | equity curve over time                    |     |              |     |            |
|      |  8  |   -    | Implement stop-loss and take-profit       | 🟡  |     2.3      |  5  |     -      |
|      |     |        | execution logic during backtest           |     |              |     |            |
|      |  9  |   -    | Test backtester manually with simple      | 🟡  |     2.8      |  3  |     -      |
|      |     |        | data (10 bars, known signals) and         |     |              |     |            |
|      |     |        | verify trade execution                    |     |              |     |            |
|  3   |     |   -    | **Build Performance Metrics Calculator**  | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create services/backtesting/metrics.py    | 🟢  |      -       |  5  |     -      |
|      |     |        | with MetricsCalculator class              |     |              |     |            |
|      |  2  |   -    | Implement calculate_returns(): total,     | 🟡  |     3.1      |  3  |     -      |
|      |     |        | annualized, percentage return             |     |              |     |            |
|      |  3  |   -    | Implement calculate_sharpe_ratio():       | 🟡  |     3.1      |  3  |     -      |
|      |     |        | (return - risk_free_rate) / std_dev       |     |              |     |            |
|      |  4  |   -    | Implement calculate_max_drawdown():       | 🟡  |     3.1      |  3  |     -      |
|      |     |        | largest peak-to-trough decline            |     |              |     |            |
|      |  5  |   -    | Implement calculate_win_rate(): winning   | 🟡  |     3.1      |  2  |     -      |
|      |     |        | trades / total trades                     |     |              |     |            |
|      |  6  |   -    | Implement calculate_profit_factor():      | 🟡  |     3.1      |  2  |     -      |
|      |     |        | gross_profit / gross_loss                 |     |              |     |            |
|      |  7  |   -    | Implement calculate_avg_win_loss():       | 🟡  |     3.1      |  2  |     -      |
|      |     |        | average win amount, average loss          |     |              |     |            |
|      |     |        | amount                                    |     |              |     |            |
|      |  8  |   -    | Implement calculate_trade_stats(): total  | 🟡  |     3.1      |  2  |     -      |
|      |     |        | trades, winning, losing counts            |     |              |     |            |
|      |  9  |   -    | Test metrics manually: create sample      | 🟡  |     3.2-3.8  |  2  |     -      |
|      |     |        | equity curve, verify all metrics          |     |              |     |            |
|      |     |        | correct                                   |     |              |     |            |
|  4   |     |   -    | **Create Backtest Results Storage**       | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Implement save_backtest_results() in      | 🟢  |      2, 3    |  5  |     -      |
|      |     |        | BacktestEngine that stores run            |     |              |     |            |
|      |     |        | metadata to backtest_runs table           |     |              |     |            |
|      |  2  |   -    | Save individual trades to                 | 🟡  |     4.1      |  3  |     -      |
|      |     |        | backtest_trades table with entry/exit     |     |              |     |            |
|      |     |        | details, P&L                              |     |              |     |            |
|      |  3  |   -    | Save equity curve to                      | 🟡  |     4.1      |  2  |     -      |
|      |     |        | backtest_equity_curve table (daily        |     |              |     |            |
|      |     |        | portfolio values)                         |     |              |     |            |
|      |  4  |   -    | Add unique constraint on backtest_runs:   | 🟡  |     4.1      |  2  |     -      |
|      |     |        | (strategy_id, symbol, date_range,         |     |              |     |            |
|      |     |        | parameters)                               |     |              |     |            |
|      |  5  |   -    | Implement get_backtest_results() method   | 🟡  |     4.1      |  2  |     -      |
|      |     |        | to retrieve stored backtest by ID         |     |              |     |            |
|      |  6  |   -    | Test storage by running backtest and      | 🟡  |     4.5      |  2  |     -      |
|      |     |        | querying DB to verify all data saved      |     |              |     |            |
|  5   |     |   -    | **Build Backtest API Endpoints**          | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create schemas/backtest.py with           | 🟢  |      -       |  3  |     -      |
|      |     |        | BacktestRequest, BacktestResponse,        |     |              |     |            |
|      |     |        | BacktestMetrics schemas                   |     |              |     |            |
|      |  2  |   -    | Create api/endpoints/backtests.py         | 🟡  |     5.1      |  3  |     -      |
|      |  3  |   -    | Implement POST /api/backtests to run      | 🟡  |     4, 5.2   |  5  |     -      |
|      |     |        | new backtest with params: strategy_id,    |     |              |     |            |
|      |     |        | symbol, start/end date                    |     |              |     |            |
|      |  4  |   -    | Make backtest execution async (long       | 🟡  |     5.3      |  3  |     -      |
|      |     |        | running) and return job ID                |     |              |     |            |
|      |  5  |   -    | Implement GET /api/backtests/{id} to      | 🟡  |     5.2      |  2  |     -      |
|      |     |        | retrieve backtest results                 |     |              |     |            |
|      |  6  |   -    | Implement GET /api/backtests to list      | 🟡  |     5.2      |  2  |     -      |
|      |     |        | all backtests with summary metrics        |     |              |     |            |
|      |  7  |   -    | Implement GET                             | 🟡  |     5.2      |  2  |     -      |
|      |     |        | /api/backtests/{id}/trades to get         |     |              |     |            |
|      |     |        | detailed trade list                       |     |              |     |            |
|      |  8  |   -    | Implement GET                             | 🟡  |     5.2      |  2  |     -      |
|      |     |        | /api/backtests/{id}/equity-curve for      |     |              |     |            |
|      |     |        | chart data                                |     |              |     |            |
|      |  9  |   -    | Manually test backtest API: POST to       | 🟡  |     5.3-5.8  |  2  |     -      |
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
|  8   |     |   -    | **Document Backtesting Results and        | 🟢  |      -       |  -  |     -      |
|      |     |        | Methodology**                             |     |              |     |            |
|      |  1  |   -    | Create docs/BACKTESTING.md documenting    | 🟢  |      7       |  3  |     -      |
|      |     |        | backtesting approach, framework           |     |              |     |            |
|      |     |        | choice                                    |     |              |     |            |
|      |  2  |   -    | Document slippage and commission          | 🟡  |     8.1      |  2  |     -      |
|      |     |        | assumptions (0.1%, $1)                    |     |              |     |            |
|      |  3  |   -    | Document no look-ahead bias verification  | 🟡  |     8.1      |  2  |     -      |
|      |     |        | (signal on close, execute on next         |     |              |     |            |
|      |     |        | open)                                     |     |              |     |            |
|      |  4  |   -    | Document all performance metrics          | 🟡  |     8.1      |  2  |     -      |
|      |     |        | calculated and their interpretations      |     |              |     |            |
|      |  5  |   -    | Include backtest API examples in          | 🟡  |     8.4      |  2  |     -      |
|      |     |        | documentation                             |     |              |     |            |
|      |  6  |   -    | Document interpretation guide: what       | 🟡  |     8.4      |  3  |     -      |
|      |     |        | good metrics look like (Sharpe >1.0,      |     |              |     |            |
|      |     |        | drawdown <25%, win rate 40-60%)           |     |              |     |            |

---

**Phase 4 Total Sprint Points:** ~167 points
**Estimated Duration:** 2 weeks
**Key Deliverables:** Backtesting system functional, validation backtests completed on 5+ stocks, strategy validated (or rejected), comprehensive backtest results documented, decision made to proceed or refine strategy
