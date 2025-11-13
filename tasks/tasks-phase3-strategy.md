# Phase 3: Indicators & Strategy Engine (Weeks 5-6)

## PRD Reference

**Source:** `/PRD.md`
**Key Requirements:**
- Integrate pandas-ta for technical indicator calculations (EMA, RSI)
- Implement Moving Average Crossover with RSI Confirmation strategy
- Generate buy/sell signals based on: EMA(20) crosses EMA(50) AND RSI < 70
- Log all signals (executed and rejected) to trade_signals table
- Handle indicator warm-up period (100 bars minimum before trading)
- Build strategy configuration API for parameter adjustments
- Trigger signal evaluation daily at 4:05 PM ET after bar completion

**Development Approach:** Implementation-first with manual testing, automated tests and documentation at end of cycle

## Relevant Files

### To Be Created:
- `backend/app/services/indicators/` - Indicator services directory
- `backend/app/services/indicators/calculator.py` - Indicator calculation engine using pandas-ta
- `backend/app/services/indicators/indicator_service.py` - Indicator management service
- `backend/app/services/strategies/` - Strategy services directory
- `backend/app/services/strategies/base_strategy.py` - Abstract base strategy class
- `backend/app/services/strategies/ma_crossover_rsi.py` - MA Crossover + RSI strategy implementation
- `backend/app/services/strategies/strategy_service.py` - Strategy management service
- `backend/app/services/strategies/signal_generator.py` - Signal generation coordinator
- `backend/app/api/endpoints/indicators.py` - Indicator API endpoints
- `backend/app/api/endpoints/strategies.py` - Strategy configuration API
- `backend/app/schemas/indicator.py` - Indicator schemas
- `backend/app/schemas/strategy.py` - Strategy schemas
- `backend/app/schemas/signal.py` - Signal schemas

### Files to Modify:
- `backend/app/main.py` - Add indicator and strategy routes
- `backend/app/services/data/scheduler.py` - Add signal evaluation job
- `backend/app/models/strategy.py` - May need additional fields
- `backend/requirements.txt` - Add pandas-ta

### Notes

- Focus on implementing strategy logic that can be manually tested
- Test indicator calculations by comparing output with TradingView
- Test signal generation by manually triggering with known data scenarios
- Automated tests will be created at end of Phase 3

## Tasks

| Task |  #  | Status | Description                               |     | Dependencies | Pts | Time Spent |
| :--: | :-: | :----: | ----------------------------------------- | :-: | :----------: | :-: | :--------: |
|  1   |     |   -    | **Integrate Technical Indicators          | 🟢  |      -       |  -  |     -      |
|      |     |        | Library (pandas-ta)**                     |     |              |     |            |
|      |  1  |   -    | Install pandas-ta and pandas libraries    | 🟢  |      -       |  1  |     -      |
|      |     |        | and add to requirements.txt               |     |              |     |            |
|      |  2  |   -    | Create                                    | 🟡  |     1.1      |  5  |     -      |
|      |     |        | services/indicators/calculator.py         |     |              |     |            |
|      |     |        | with IndicatorCalculator class            |     |              |     |            |
|      |  3  |   -    | Implement calculate_ema() method that     | 🟡  |     1.2      |  3  |     -      |
|      |     |        | takes DataFrame and period, returns       |     |              |     |            |
|      |     |        | EMA series using pandas-ta                |     |              |     |            |
|      |  4  |   -    | Implement calculate_rsi() method that     | 🟡  |     1.2      |  3  |     -      |
|      |     |        | takes DataFrame and period, returns       |     |              |     |            |
|      |     |        | RSI series using pandas-ta                |     |              |     |            |
|      |  5  |   -    | Implement calculate_all() method that     | 🟡  |     1.3-1.4  |  3  |     -      |
|      |     |        | calculates multiple indicators and        |     |              |     |            |
|      |     |        | adds columns to DataFrame                 |     |              |     |            |
|      |  6  |   -    | Test indicator calculations manually:     | 🟡  |     1.5      |  2  |     -      |
|      |     |        | fetch AAPL data, calculate EMA(20),       |     |              |     |            |
|      |     |        | EMA(50), RSI(14)                          |     |              |     |            |
|      |  7  |   -    | Verify indicator values match             | 🟡  |     1.6      |  2  |     -      |
|      |     |        | TradingView or other reference source     |     |              |     |            |
|  2   |     |   -    | **Implement Indicator Calculation         | 🟢  |      -       |  -  |     -      |
|      |     |        | Service**                                 |     |              |     |            |
|      |  1  |   -    | Create                                    | 🟢  |      1       |  5  |     -      |
|      |     |        | services/indicators/indicator_service.py  |     |              |     |            |
|      |     |        | with IndicatorService class               |     |              |     |            |
|      |  2  |   -    | Implement get_indicators_for_stock()      | 🟡  |     2.1      |  3  |     -      |
|      |     |        | that fetches OHLCV, calculates           |     |              |     |            |
|      |     |        | indicators, returns DataFrame             |     |              |     |            |
|      |  3  |   -    | Add optional storage: save calculated     | 🟡  |     2.2      |  3  |     -      |
|      |     |        | indicators to indicators table            |     |              |     |            |
|      |     |        | (recent 90 days)                          |     |              |     |            |
|      |  4  |   -    | Implement indicator warm-up detection:    | 🟡  |     2.2      |  3  |     -      |
|      |     |        | check if enough data (100+ bars) for      |     |              |     |            |
|      |     |        | reliable indicators                       |     |              |     |            |
|      |  5  |   -    | Create API endpoint GET                   | 🟡  |     2.2      |  3  |     -      |
|      |     |        | /api/indicators/calculate with            |     |              |     |            |
|      |     |        | params: symbol, indicators list           |     |              |     |            |
|      |  6  |   -    | Create schemas/indicator.py with          | 🟡  |     2.5      |  2  |     -      |
|      |     |        | IndicatorRequest, IndicatorResponse       |     |              |     |            |
|      |  7  |   -    | Manually test indicator API: request      | 🟡  |     2.5-2.6  |  2  |     -      |
|      |     |        | AAPL with EMA/RSI, verify JSON            |     |              |     |            |
|      |     |        | response                                  |     |              |     |            |
|  3   |     |   -    | **Build Strategy Engine Core**            | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create                                    | 🟢  |      -       |  5  |     -      |
|      |     |        | services/strategies/base_strategy.py      |     |              |     |            |
|      |     |        | with abstract BaseStrategy class          |     |              |     |            |
|      |  2  |   -    | Define abstract methods in BaseStrategy:  | 🟡  |     3.1      |  3  |     -      |
|      |     |        | generate_signal(), get_parameters(),      |     |              |     |            |
|      |     |        | validate_parameters()                     |     |              |     |            |
|      |  3  |   -    | Create                                    | 🟡  |     3.2      |  8  |     -      |
|      |     |        | services/strategies/ma_crossover_rsi.py   |     |              |     |            |
|      |     |        | implementing BaseStrategy                 |     |              |     |            |
|      |  4  |   -    | Implement generate_signal() with BUY      | 🟡  |     3.3      |  5  |     -      |
|      |     |        | logic: EMA(20) > EMA(50) AND RSI < 70     |     |              |     |            |
|      |     |        | AND no existing position                  |     |              |     |            |
|      |  5  |   -    | Implement generate_signal() with SELL     | 🟡  |     3.4      |  5  |     -      |
|      |     |        | logic: EMA(20) < EMA(50) OR RSI > 70      |     |              |     |            |
|      |  6  |   -    | Add crossover detection: check if EMA     | 🟡  |     3.4-3.5  |  3  |     -      |
|      |     |        | lines crossed between current and         |     |              |     |            |
|      |     |        | previous bar                              |     |              |     |            |
|      |  7  |   -    | Test strategy logic manually with mock    | 🟡  |     3.6      |  3  |     -      |
|      |     |        | data scenarios: crossover up, down,       |     |              |     |            |
|      |     |        | RSI overbought                            |     |              |     |            |
|  4   |     |   -    | **Implement Signal Generation Logic**     | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create                                    | 🟢  |      2, 3    |  5  |     -      |
|      |     |        | services/strategies/signal_generator.py   |     |              |     |            |
|      |     |        | with SignalGenerator class                |     |              |     |            |
|      |  2  |   -    | Implement evaluate_watchlist() method     | 🟡  |     4.1      |  5  |     -      |
|      |     |        | that loops through all watchlist          |     |              |     |            |
|      |     |        | stocks, gets indicators, generates        |     |              |     |            |
|      |     |        | signals                                   |     |              |     |            |
|      |  3  |   -    | Implement signal logging: save all        | 🟡  |     4.2      |  3  |     -      |
|      |     |        | signals to trade_signals table with       |     |              |     |            |
|      |     |        | timestamp, trigger_reason,                |     |              |     |            |
|      |     |        | indicator_values                          |     |              |     |            |
|      |  4  |   -    | Add market context capture: save          | 🟡  |     4.3      |  3  |     -      |
|      |     |        | volatility, volume_vs_avg, trend to       |     |              |     |            |
|      |     |        | market_context JSONB field                |     |              |     |            |
|      |  5  |   -    | Create schemas/signal.py with             | 🟡  |     4.1      |  2  |     -      |
|      |     |        | SignalCreate, SignalResponse schemas      |     |              |     |            |
|      |  6  |   -    | Add API endpoint POST                     | 🟡  |     4.2      |  2  |     -      |
|      |     |        | /api/signals/evaluate to manually         |     |              |     |            |
|      |     |        | trigger signal evaluation                 |     |              |     |            |
|      |  7  |   -    | Manually test signal generation: POST     | 🟡  |     4.6      |  2  |     -      |
|      |     |        | to /evaluate, check signals in DB         |     |              |     |            |
|  5   |     |   -    | **Create Strategy State Management**      | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Add state fields to strategies table:     | 🟢  |      -       |  2  |     -      |
|      |     |        | status (active/paused/warming/error),     |     |              |     |            |
|      |     |        | warm_up_bars_remaining                    |     |              |     |            |
|      |  2  |   -    | Create                                    | 🟡  |     5.1      |  5  |     -      |
|      |     |        | services/strategies/strategy_service.py   |     |              |     |            |
|      |     |        | with StrategyService class                |     |              |     |            |
|      |  3  |   -    | Implement get_strategy_status() method    | 🟡  |     5.2      |  2  |     -      |
|      |     |        | returning current state                   |     |              |     |            |
|      |  4  |   -    | Implement activate_strategy() method      | 🟡  |     5.2      |  3  |     -      |
|      |     |        | that checks warm-up, sets status to       |     |              |     |            |
|      |     |        | active/warming                            |     |              |     |            |
|      |  5  |   -    | Implement pause_strategy() method with    | 🟡  |     5.2      |  2  |     -      |
|      |     |        | reason logging                            |     |              |     |            |
|      |  6  |   -    | Implement check_warm_up() method: count   | 🟡  |     5.2      |  3  |     -      |
|      |     |        | available bars, update                    |     |              |     |            |
|      |     |        | warm_up_bars_remaining                    |     |              |     |            |
|      |  7  |   -    | Add guard in SignalGenerator: only        | 🟡  |     4, 5.4   |  2  |     -      |
|      |     |        | generate signals if strategy active       |     |              |     |            |
|      |  8  |   -    | Manually test state transitions:          | 🟡  |     5.4-5.7  |  2  |     -      |
|      |     |        | activate, pause, check warm-up status     |     |              |     |            |
|  6   |     |   -    | **Build Strategy Configuration API**      | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create schemas/strategy.py with           | 🟢  |      -       |  3  |     -      |
|      |     |        | StrategyCreate, StrategyUpdate,           |     |              |     |            |
|      |     |        | StrategyResponse schemas                  |     |              |     |            |
|      |  2  |   -    | Create api/endpoints/strategies.py with   | 🟡  |     6.1      |  3  |     -      |
|      |     |        | CRUD endpoints                            |     |              |     |            |
|      |  3  |   -    | Implement POST /api/strategies to         | 🟡  |     6.2      |  3  |     -      |
|      |     |        | create strategy with parameters           |     |              |     |            |
|      |     |        | (ema_fast, ema_slow, rsi_period,          |     |              |     |            |
|      |     |        | rsi_threshold)                            |     |              |     |            |
|      |  4  |   -    | Implement GET /api/strategies to list     | 🟡  |     6.2      |  2  |     -      |
|      |     |        | all strategies with status                |     |              |     |            |
|      |  5  |   -    | Implement PUT                             | 🟡  |     6.2      |  3  |     -      |
|      |     |        | /api/strategies/{id}/parameters to        |     |              |     |            |
|      |     |        | update strategy config                    |     |              |     |            |
|      |  6  |   -    | Implement POST                            | 🟡  |     5, 6.2   |  2  |     -      |
|      |     |        | /api/strategies/{id}/activate to          |     |              |     |            |
|      |     |        | activate strategy                         |     |              |     |            |
|      |  7  |   -    | Implement POST                            | 🟡  |     5, 6.2   |  2  |     -      |
|      |     |        | /api/strategies/{id}/pause to pause       |     |              |     |            |
|      |     |        | strategy                                  |     |              |     |            |
|      |  8  |   -    | Manually test strategy API: create MA     | 🟡  |     6.3-6.7  |  2  |     -      |
|      |     |        | Crossover strategy, update params,        |     |              |     |            |
|      |     |        | activate                                  |     |              |     |            |
|  7   |     |   -    | **Write Unit Tests for Strategy Logic**   | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create tests/test_indicator_calculator.py | 🟢  |      6       |  5  |     -      |
|      |     |        | testing EMA and RSI calculations          |     |              |     |            |
|      |  2  |   -    | Create                                    | 🟡  |     7.1      |  5  |     -      |
|      |     |        | tests/test_ma_crossover_strategy.py       |     |              |     |            |
|      |     |        | with test scenarios: bullish              |     |              |     |            |
|      |     |        | crossover, bearish, overbought            |     |              |     |            |
|      |  3  |   -    | Create tests/test_signal_generator.py     | 🟡  |     7.1      |  3  |     -      |
|      |     |        | testing signal creation and logging       |     |              |     |            |
|      |  4  |   -    | Create tests/test_strategy_service.py     | 🟡  |     7.1      |  3  |     -      |
|      |     |        | testing state management                  |     |              |     |            |
|      |  5  |   -    | Create tests/test_strategies_api.py       | 🟡  |     7.1      |  3  |     -      |
|      |     |        | testing strategy CRUD endpoints           |     |              |     |            |
|      |  6  |   -    | Run pytest and ensure all Phase 3         | 🟡  |     7.2-7.5  |  1  |     -      |
|      |     |        | tests pass with 70%+ coverage             |     |              |     |            |
|  8   |     |   -    | **Document Strategy Implementation**      | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create docs/STRATEGY_ENGINE.md            | 🟢  |      7       |  3  |     -      |
|      |     |        | documenting strategy architecture         |     |              |     |            |
|      |  2  |   -    | Document MA Crossover + RSI strategy      | 🟡  |     8.1      |  3  |     -      |
|      |     |        | rules: entry/exit conditions,             |     |              |     |            |
|      |     |        | parameters                                |     |              |     |            |
|      |  3  |   -    | Document indicator warm-up period and     | 🟡  |     8.2      |  2  |     -      |
|      |     |        | requirements (100+ bars)                  |     |              |     |            |
|      |  4  |   -    | Document signal evaluation timing         | 🟡  |     8.2      |  2  |     -      |
|      |     |        | (daily at 4:05 PM ET)                     |     |              |     |            |
|      |  5  |   -    | Add strategy API examples to              | 🟡  |     8.2      |  2  |     -      |
|      |     |        | documentation                             |     |              |     |            |
|      |  6  |   -    | Document how to add new strategies        | 🟡  |     8.5      |  2  |     -      |
|      |     |        | (extend BaseStrategy)                     |     |              |     |            |

---

**Phase 3 Total Sprint Points:** ~143 points
**Estimated Duration:** 2 weeks
**Key Deliverables:** Indicator calculation working, MA Crossover + RSI strategy implemented, signal generation functional, strategy state management, configuration API, unit tests passing
