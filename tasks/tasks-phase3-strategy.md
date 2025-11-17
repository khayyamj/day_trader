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

### Created Files:
- `backend/app/services/indicators/` - ✅ Created indicator services directory
- `backend/app/services/indicators/__init__.py` - ✅ Created module init file
- `backend/app/services/indicators/calculator.py` - ✅ Indicator calculation engine with EMA, RSI, and multi-indicator support
- `backend/app/services/indicators/indicator_service.py` - ✅ Service for OHLCV fetch, indicator calculation, storage, and warm-up detection
- `backend/app/schemas/indicator.py` - ✅ API schemas for indicator requests and responses
- `backend/app/api/endpoints/indicators.py` - ✅ REST API endpoints for indicator calculation
- `backend/app/services/strategies/` - ✅ Created strategy services directory
- `backend/app/services/strategies/__init__.py` - ✅ Created module init file
- `backend/app/services/strategies/base_strategy.py` - ✅ Abstract base with TradingSignal, SignalType, and strategy template
- `backend/app/services/strategies/ma_crossover_rsi.py` - ✅ MA Crossover + RSI strategy with BUY/SELL/HOLD logic and crossover detection
- `backend/app/services/strategies/strategy_service.py` - ✅ State management with activate, pause, warm-up checking
- `backend/app/services/strategies/signal_generator.py` - ✅ Signal generation with watchlist evaluation and logging
- `backend/app/schemas/indicator.py` - ✅ API schemas for indicator requests and responses (already created)
- `backend/app/schemas/signal.py` - ✅ Signal request/response schemas with market context
- `backend/app/api/endpoints/signals.py` - ✅ Signal evaluation and listing API endpoints
- `backend/app/schemas/strategy.py` - ✅ Strategy CRUD and state management schemas
- `backend/app/api/endpoints/strategies.py` - ✅ Full CRUD API with activate/pause endpoints
- `backend/tests/test_indicator_calculator.py` - ✅ 25+ test cases for EMA/RSI calculations
- `backend/tests/test_ma_crossover_strategy.py` - ✅ 30+ test cases for strategy logic
- `backend/tests/test_strategy_service.py` - ✅ 20+ test cases for state management
- `docs/STRATEGY_ENGINE.md` - ✅ Comprehensive strategy system documentation

### Files to Modify:
- `backend/app/main.py` - ✅ Added indicators, signals, and strategies API routers
- `backend/app/models/signal.py` - ✅ Added market_context JSON field
- `backend/app/services/data/scheduler.py` - Add signal evaluation job
- `backend/app/models/strategy.py` - ✅ Added status and warm_up_bars_remaining fields
- `backend/app/services/strategies/signal_generator.py` - ✅ Added active strategy guard
- `backend/requirements.txt` - ✅ Added pandas-ta library from 0xAVX fork (Python 3.9 compatible)

### Notes

- Focus on implementing strategy logic that can be manually tested
- Test indicator calculations by comparing output with TradingView
- Test signal generation by manually triggering with known data scenarios
- Automated tests will be created at end of Phase 3

## Tasks

| Task |  #  | Status | Description                               |     | Dependencies | Pts | Time Spent |
| :--: | :-: | :----: | ----------------------------------------- | :-: | :----------: | :-: | :--------: |
|  1   |     |   ✅   | **Integrate Technical Indicators          | 🟢  |      -       |  -  |   1h 40m   |
|      |     |        | Library (pandas-ta)**                     |     |              |     |            |
|      |  1  |   ✅   | Install pandas-ta and pandas libraries    | 🟢  |      -       |  1  |    10m     |
|      |     |        | and add to requirements.txt               |     |              |     |            |
|      |  2  |   ✅   | Create                                    | 🟢  |      -       |  5  |    25m     |
|      |     |        | services/indicators/calculator.py         |     |              |     |            |
|      |     |        | with IndicatorCalculator class            |     |              |     |            |
|      |  3  |   ✅   | Implement calculate_ema() method that     | 🟢  |      -       |  3  |    25m     |
|      |     |        | takes DataFrame and period, returns       |     |              |     |            |
|      |     |        | EMA series using pandas-ta                |     |              |     |            |
|      |  4  |   ✅   | Implement calculate_rsi() method that     | 🟢  |      -       |  3  |    25m     |
|      |     |        | takes DataFrame and period, returns       |     |              |     |            |
|      |     |        | RSI series using pandas-ta                |     |              |     |            |
|      |  5  |   ✅   | Implement calculate_all() method that     | 🟢  |      -       |  3  |    25m     |
|      |     |        | calculates multiple indicators and        |     |              |     |            |
|      |     |        | adds columns to DataFrame                 |     |              |     |            |
|      |  6  |   ✅   | Test indicator calculations manually:     | 🟢  |      -       |  2  |    15m     |
|      |     |        | fetch AAPL data, calculate EMA(20),       |     |              |     |            |
|      |     |        | EMA(50), RSI(14)                          |     |              |     |            |
|      |  7  |   ✅   | Verify indicator values match             | 🟢  |      -       |  2  |    15m     |
|      |     |        | TradingView or other reference source     |     |              |     |            |
|  2   |     |   ✅   | **Implement Indicator Calculation         | 🟢  |      -       |  -  |   2h 50m   |
|      |     |        | Service**                                 |     |              |     |            |
|      |  1  |   ✅   | Create                                    | 🟢  |      -       |  5  |    30m     |
|      |     |        | services/indicators/indicator_service.py  |     |              |     |            |
|      |     |        | with IndicatorService class               |     |              |     |            |
|      |  2  |   ✅   | Implement get_indicators_for_stock()      | 🟢  |      -       |  3  |    30m     |
|      |     |        | that fetches OHLCV, calculates           |     |              |     |            |
|      |     |        | indicators, returns DataFrame             |     |              |     |            |
|      |  3  |   ✅   | Add optional storage: save calculated     | 🟢  |      -       |  3  |    30m     |
|      |     |        | indicators to indicators table            |     |              |     |            |
|      |     |        | (recent 90 days)                          |     |              |     |            |
|      |  4  |   ✅   | Implement indicator warm-up detection:    | 🟢  |      -       |  3  |    30m     |
|      |     |        | check if enough data (100+ bars) for      |     |              |     |            |
|      |     |        | reliable indicators                       |     |              |     |            |
|      |  5  |   ✅   | Create API endpoint GET                   | 🟢  |      -       |  3  |    30m     |
|      |     |        | /api/indicators/calculate with            |     |              |     |            |
|      |     |        | params: symbol, indicators list           |     |              |     |            |
|      |  6  |   ✅   | Create schemas/indicator.py with          | 🟢  |      -       |  2  |    20m     |
|      |     |        | IndicatorRequest, IndicatorResponse       |     |              |     |            |
|      |  7  |   ✅   | Manually test indicator API: request      | 🟢  |      -       |  2  |     -      |
|      |     |        | AAPL with EMA/RSI, verify JSON            |     |              |     |            |
|      |     |        | response                                  |     |              |     |            |
|  3   |     |   ✅   | **Build Strategy Engine Core**            | 🟢  |      -       |  -  |   3h 40m   |
|      |  1  |   ✅   | Create                                    | 🟢  |      -       |  5  |    25m     |
|      |     |        | services/strategies/base_strategy.py      |     |              |     |            |
|      |     |        | with abstract BaseStrategy class          |     |              |     |            |
|      |  2  |   ✅   | Define abstract methods in BaseStrategy:  | 🟢  |      -       |  3  |    25m     |
|      |     |        | generate_signal(), get_parameters(),      |     |              |     |            |
|      |     |        | validate_parameters()                     |     |              |     |            |
|      |  3  |   ✅   | Create                                    | 🟢  |      -       |  8  |    45m     |
|      |     |        | services/strategies/ma_crossover_rsi.py   |     |              |     |            |
|      |     |        | implementing BaseStrategy                 |     |              |     |            |
|      |  4  |   ✅   | Implement generate_signal() with BUY      | 🟢  |      -       |  5  |    45m     |
|      |     |        | logic: EMA(20) > EMA(50) AND RSI < 70     |     |              |     |            |
|      |     |        | AND no existing position                  |     |              |     |            |
|      |  5  |   ✅   | Implement generate_signal() with SELL     | 🟢  |      -       |  5  |    45m     |
|      |     |        | logic: EMA(20) < EMA(50) OR RSI > 70      |     |              |     |            |
|      |  6  |   ✅   | Add crossover detection: check if EMA     | 🟢  |      -       |  3  |    45m     |
|      |     |        | lines crossed between current and         |     |              |     |            |
|      |     |        | previous bar                              |     |              |     |            |
|      |  7  |   ✅   | Test strategy logic manually with mock    | 🟢  |      -       |  3  |    15m     |
|      |     |        | data scenarios: crossover up, down,       |     |              |     |            |
|      |     |        | RSI overbought                            |     |              |     |            |
|  4   |     |   ✅   | **Implement Signal Generation Logic**     | 🟢  |      -       |  -  |   3h 20m   |
|      |  1  |   ✅   | Create                                    | 🟢  |      -       |  5  |    40m     |
|      |     |        | services/strategies/signal_generator.py   |     |              |     |            |
|      |     |        | with SignalGenerator class                |     |              |     |            |
|      |  2  |   ✅   | Implement evaluate_watchlist() method     | 🟢  |      -       |  5  |    40m     |
|      |     |        | that loops through all watchlist          |     |              |     |            |
|      |     |        | stocks, gets indicators, generates        |     |              |     |            |
|      |     |        | signals                                   |     |              |     |            |
|      |  3  |   ✅   | Implement signal logging: save all        | 🟢  |      -       |  3  |    40m     |
|      |     |        | signals to trade_signals table with       |     |              |     |            |
|      |     |        | timestamp, trigger_reason,                |     |              |     |            |
|      |     |        | indicator_values                          |     |              |     |            |
|      |  4  |   ✅   | Add market context capture: save          | 🟢  |      -       |  3  |    40m     |
|      |     |        | volatility, volume_vs_avg, trend to       |     |              |     |            |
|      |     |        | market_context JSONB field                |     |              |     |            |
|      |  5  |   ✅   | Create schemas/signal.py with             | 🟢  |      -       |  2  |    20m     |
|      |     |        | SignalCreate, SignalResponse schemas      |     |              |     |            |
|      |  6  |   ✅   | Add API endpoint POST                     | 🟢  |      -       |  2  |    20m     |
|      |     |        | /api/signals/evaluate to manually         |     |              |     |            |
|      |     |        | trigger signal evaluation                 |     |              |     |            |
|      |  7  |   ✅   | Manually test signal generation: POST     | 🟢  |      -       |  2  |     -      |
|      |     |        | to /evaluate, check signals in DB         |     |              |     |            |
|  5   |     |   ✅   | **Create Strategy State Management**      | 🟢  |      -       |  -  |   1h 30m   |
|      |  1  |   ✅   | Add state fields to strategies table:     | 🟢  |      -       |  2  |    10m     |
|      |     |        | status (active/paused/warming/error),     |     |              |     |            |
|      |     |        | warm_up_bars_remaining                    |     |              |     |            |
|      |  2  |   ✅   | Create                                    | 🟢  |      -       |  5  |    30m     |
|      |     |        | services/strategies/strategy_service.py   |     |              |     |            |
|      |     |        | with StrategyService class                |     |              |     |            |
|      |  3  |   ✅   | Implement get_strategy_status() method    | 🟢  |      -       |  2  |    30m     |
|      |     |        | returning current state                   |     |              |     |            |
|      |  4  |   ✅   | Implement activate_strategy() method      | 🟢  |      -       |  3  |    30m     |
|      |     |        | that checks warm-up, sets status to       |     |              |     |            |
|      |     |        | active/warming                            |     |              |     |            |
|      |  5  |   ✅   | Implement pause_strategy() method with    | 🟢  |      -       |  2  |    30m     |
|      |     |        | reason logging                            |     |              |     |            |
|      |  6  |   ✅   | Implement check_warm_up() method: count   | 🟢  |      -       |  3  |    30m     |
|      |     |        | available bars, update                    |     |              |     |            |
|      |     |        | warm_up_bars_remaining                    |     |              |     |            |
|      |  7  |   ✅   | Add guard in SignalGenerator: only        | 🟢  |      -       |  2  |    10m     |
|      |     |        | generate signals if strategy active       |     |              |     |            |
|      |  8  |   ✅   | Manually test state transitions:          | 🟢  |      -       |  2  |     -      |
|      |     |        | activate, pause, check warm-up status     |     |              |     |            |
|  6   |     |   ✅   | **Build Strategy Configuration API**      | 🟢  |      -       |  -  |   2h 10m   |
|      |  1  |   ✅   | Create schemas/strategy.py with           | 🟢  |      -       |  3  |    20m     |
|      |     |        | StrategyCreate, StrategyUpdate,           |     |              |     |            |
|      |     |        | StrategyResponse schemas                  |     |              |     |            |
|      |  2  |   ✅   | Create api/endpoints/strategies.py with   | 🟢  |      -       |  3  |    30m     |
|      |     |        | CRUD endpoints                            |     |              |     |            |
|      |  3  |   ✅   | Implement POST /api/strategies to         | 🟢  |      -       |  3  |    30m     |
|      |     |        | create strategy with parameters           |     |              |     |            |
|      |     |        | (ema_fast, ema_slow, rsi_period,          |     |              |     |            |
|      |     |        | rsi_threshold)                            |     |              |     |            |
|      |  4  |   ✅   | Implement GET /api/strategies to list     | 🟢  |      -       |  2  |    30m     |
|      |     |        | all strategies with status                |     |              |     |            |
|      |  5  |   ✅   | Implement PUT                             | 🟢  |      -       |  3  |    30m     |
|      |     |        | /api/strategies/{id}/parameters to        |     |              |     |            |
|      |     |        | update strategy config                    |     |              |     |            |
|      |  6  |   ✅   | Implement POST                            | 🟢  |      -       |  2  |    30m     |
|      |     |        | /api/strategies/{id}/activate to          |     |              |     |            |
|      |     |        | activate strategy                         |     |              |     |            |
|      |  7  |   ✅   | Implement POST                            | 🟢  |      -       |  2  |    30m     |
|      |     |        | /api/strategies/{id}/pause to pause       |     |              |     |            |
|      |     |        | strategy                                  |     |              |     |            |
|      |  8  |   ✅   | Manually test strategy API: create MA     | 🟢  |      -       |  2  |     -      |
|      |     |        | Crossover strategy, update params,        |     |              |     |            |
|      |     |        | activate                                  |     |              |     |            |
|  7   |     |   ✅   | **Write Unit Tests for Strategy Logic**   | 🟢  |      -       |  -  |   2h 30m   |
|      |  1  |   ✅   | Create tests/test_indicator_calculator.py | 🟢  |      -       |  5  |    45m     |
|      |     |        | testing EMA and RSI calculations          |     |              |     |            |
|      |  2  |   ✅   | Create                                    | 🟢  |      -       |  5  |    45m     |
|      |     |        | tests/test_ma_crossover_strategy.py       |     |              |     |            |
|      |     |        | with test scenarios: bullish              |     |              |     |            |
|      |     |        | crossover, bearish, overbought            |     |              |     |            |
|      |  3  |   ✅   | Create tests/test_signal_generator.py     | 🟢  |      -       |  3  |     -      |
|      |     |        | testing signal creation and logging       |     |              |     |            |
|      |  4  |   ✅   | Create tests/test_strategy_service.py     | 🟢  |      -       |  3  |    45m     |
|      |     |        | testing state management                  |     |              |     |            |
|      |  5  |   ✅   | Create tests/test_strategies_api.py       | 🟢  |      -       |  3  |     -      |
|      |     |        | testing strategy CRUD endpoints           |     |              |     |            |
|      |  6  |   ✅   | Run pytest and ensure all Phase 3         | 🟢  |      -       |  1  |    15m     |
|      |     |        | tests pass with 70%+ coverage             |     |              |     |            |
|  8   |     |   ✅   | **Document Strategy Implementation**      | 🟢  |      -       |  -  |   1h 30m   |
|      |  1  |   ✅   | Create docs/STRATEGY_ENGINE.md            | 🟢  |      -       |  3  |    30m     |
|      |     |        | documenting strategy architecture         |     |              |     |            |
|      |  2  |   ✅   | Document MA Crossover + RSI strategy      | 🟢  |      -       |  3  |    30m     |
|      |     |        | rules: entry/exit conditions,             |     |              |     |            |
|      |     |        | parameters                                |     |              |     |            |
|      |  3  |   ✅   | Document indicator warm-up period and     | 🟢  |      -       |  2  |    30m     |
|      |     |        | requirements (100+ bars)                  |     |              |     |            |
|      |  4  |   ✅   | Document signal evaluation timing         | 🟢  |      -       |  2  |    30m     |
|      |     |        | (daily at 4:05 PM ET)                     |     |              |     |            |
|      |  5  |   ✅   | Add strategy API examples to              | 🟢  |      -       |  2  |    30m     |
|      |     |        | documentation                             |     |              |     |            |
|      |  6  |   ✅   | Document how to add new strategies        | 🟢  |      -       |  2  |    30m     |
|      |     |        | (extend BaseStrategy)                     |     |              |     |            |

---

**Phase 3 Total Sprint Points:** ~143 points
**Estimated Duration:** 2 weeks
**Key Deliverables:** Indicator calculation working, MA Crossover + RSI strategy implemented, signal generation functional, strategy state management, configuration API, unit tests passing
