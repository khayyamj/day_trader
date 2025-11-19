# Phase 5: Trading Execution & Risk Management (Weeks 9-10)

## PRD Reference

**Source:** `/PRD.md`
**Key Requirements:**
- Integrate with IBKR paper trading account via ib_insync library
- Implement order submission (market orders) and tracking
- Build position reconciliation system (database vs broker reality)
- Implement position sizing calculator using 2% risk rule
- Enforce risk management rules: max 20% position size, max 50% portfolio allocation
- Implement stop-loss order placement at broker level (survives app crashes)
- Build daily loss limit detector (pause after 3 consecutive losses)
- **CRITICAL**: All stop-loss orders MUST be placed at broker level for safety

**Development Approach:** Implementation-first with manual testing, automated tests and documentation at end of cycle

## Relevant Files

### Created:
- `backend/app/services/trading/__init__.py` - Trading services module initialization
- `backend/app/services/trading/ibkr_client.py` - IBKR API wrapper using ib_insync with connection management
- `backend/app/services/trading/order_service.py` - Order submission and tracking service
- `backend/app/services/trading/position_service.py` - Position management and reconciliation
- `backend/app/services/trading/execution_engine.py` - Main trade execution coordinator
- `backend/app/services/risk/position_sizer.py` - Position sizing calculator using 2% risk rule
- `backend/app/services/risk/risk_manager.py` - Risk management engine enforcing all trading rules
- `backend/test_ibkr_connection.py` - Test script for IBKR connection verification

### To Be Created:
- `backend/app/services/risk/loss_limit_detector.py` - Daily loss limit tracker
- `backend/app/api/endpoints/trading.py` - Trading API endpoints
- `backend/app/api/endpoints/orders.py` - Order management API
- `backend/app/schemas/order.py` - Order schemas
- `backend/app/schemas/position.py` - Position schemas

### Modified:
- `backend/app/core/config.py` - Added IBKR_HOST and IBKR_CLIENT_ID configuration
- `backend/.env` - Added IBKR connection credentials
- `backend/app/services/strategies/base_strategy.py` - Added calculate_stop_loss_price() and calculate_take_profit_price() methods

### Files to Modify:
- `backend/app/main.py` - Add trading routes
- `backend/app/models/order.py` - May need additional fields
- `backend/app/models/trade.py` - Add risk management fields
- `backend/app/services/strategies/signal_generator.py` - Connect to execution engine
- `backend/requirements.txt` - Add ib_insync

### Notes

- Focus on safe, tested order execution that can be verified in IBKR paper account
- Test all scenarios: successful orders, rejections, insufficient funds, market closed
- Verify stop-loss orders are placed at broker level (visible in IBKR TWS/Gateway)
- Test crash recovery by stopping app and verifying positions reconcile
- Automated tests will be created at end of Phase 5

## Tasks

| Task |  #  | Status | Description                               |     | Dependencies | Pts | Time Spent |
| :--: | :-: | :----: | ----------------------------------------- | :-: | :----------: | :-: | :--------: |
|  1   |     |   ✅   | **Set Up IBKR Integration**               | 🟢  |      -       |  -  |   1h 20m   |
|      |  1  |   ✅   | Open IBKR paper trading account online    | 🟢  |      -       |  2  |     5m     |
|      |  2  |   ✅   | Download and install IB Gateway or TWS    | 🟢  |     1.1      |  1  |     5m     |
|      |     |        | desktop application                       |     |              |     |            |
|      |  3  |   ✅   | Configure IB Gateway: enable API          | 🟢  |     1.2      |  2  |     10m    |
|      |     |        | connections, set port 7497 (paper),       |     |              |     |            |
|      |     |        | add localhost to trusted IPs              |     |              |     |            |
|      |  4  |   ✅   | Install ib_insync library and add to      | 🟢  |     1.3      |  1  |     5m     |
|      |     |        | requirements.txt                          |     |              |     |            |
|      |  5  |   ✅   | Add IBKR credentials to .env:             | 🟢  |     1.4      | 0.5 |     5m     |
|      |     |        | IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID      |     |              |     |            |
|      |  6  |   ✅   | Create services/trading/ibkr_client.py    | 🟢  |     1.4      |  5  |     15m    |
|      |     |        | with IBKRClient class wrapping            |     |              |     |            |
|      |     |        | ib_insync.IB                              |     |              |     |            |
|      |  7  |   ✅   | Implement connect() method with retry     | 🟢  |     1.6      |  3  |     20m    |
|      |     |        | logic and connection monitoring           |     |              |     |            |
|      |  8  |   ✅   | Implement disconnect() method and         | 🟢  |     1.7      |  2  |     15m    |
|      |     |        | reconnect on connection loss              |     |              |     |            |
|      |  9  |   ✅   | Manually test connection: start IB        | 🟢  |     1.8      |  1  |     5m     |
|      |     |        | Gateway, run Python script to             |     |              |     |            |
|      |     |        | connect, verify in logs                   |     |              |     |            |
|  2   |     |   🔄   | **Implement Order Submission Service**    | 🟢  |      1       |  -  |     -      |
|      |  1  |   ✅   | Create services/trading/order_service.py  | 🟢  |      1       |  5  |     30m    |
|      |     |        | with OrderService class                   |     |              |     |            |
|      |  2  |   ✅   | Implement submit_market_order() for buy   | 🟢  |     2.1      |  5  |     -      |
|      |     |        | orders: symbol, quantity, action (BUY)    |     |              |     |            |
|      |  3  |   ✅   | Implement submit_market_order() for       | 🟢  |     2.2      |  3  |     -      |
|      |     |        | sell orders: symbol, quantity, action     |     |              |     |            |
|      |     |        | (SELL)                                    |     |              |     |            |
|      |  4  |   ✅   | Add order tracking: store broker_order_id | 🟢  |     2.2      |  3  |     -      |
|      |     |        | in orders table immediately after         |     |              |     |            |
|      |     |        | submission                                |     |              |     |            |
|      |  5  |   ✅   | Implement submit_stop_loss_order() to     | 🟢  |     2.2      |  5  |     -      |
|      |     |        | place stop at broker level: symbol,       |     |              |     |            |
|      |     |        | quantity, stop_price                      |     |              |     |            |
|      |  6  |   ✅   | Implement submit_take_profit_order()      | 🟢  |     2.5      |  3  |     -      |
|      |     |        | (limit order) at broker level             |     |              |     |            |
|      |  7  |   ✅   | Add order status monitoring: poll IBKR    | 🟢  |     2.2      |  5  |     -      |
|      |     |        | every 30 seconds for order fills,         |     |              |     |            |
|      |     |        | update orders table                       |     |              |     |            |
|      |  8  |   ✅   | Implement error handling: rejections,     | 🟢  |     2.2      |  3  |     -      |
|      |     |        | insufficient margin, invalid symbol       |     |              |     |            |
|      |  9  |   -    | Manually test orders: submit buy order    | 🟢  |     2.8      |  2  |     -      |
|      |     |        | for AAPL, verify in IBKR TWS,             |     |              |     |            |
|      |     |        | check DB [MANUAL TEST - USER]             |     |              |     |            |
|      | 10  |   -    | Test stop-loss order: submit and verify   | 🟢  |     2.9      |  2  |     -      |
|      |     |        | visible in IBKR TWS as separate           |     |              |     |            |
|      |     |        | order [MANUAL TEST - USER]                |     |              |     |            |
|  3   |     |   🔄   | **Build Position Reconciliation System**  | 🟢  |      2       |  -  |     -      |
|      |  1  |   ✅   | Create                                    | 🟢  |      1       |  5  |     40m    |
|      |     |        | services/trading/position_service.py      |     |              |     |            |
|      |     |        | with PositionService class                |     |              |     |            |
|      |  2  |   ✅   | Implement get_broker_positions() that     | 🟢  |     3.1      |  3  |     -      |
|      |     |        | queries IBKR for current positions        |     |              |     |            |
|      |  3  |   ✅   | Implement get_db_positions() that         | 🟢  |     3.1      |  2  |     -      |
|      |     |        | queries trades table for open             |     |              |     |            |
|      |     |        | positions                                 |     |              |     |            |
|      |  4  |   ✅   | Implement reconcile_positions() that      | 🟢  |     3.2-3.3  |  5  |     -      |
|      |     |        | compares broker vs DB and identifies      |     |              |     |            |
|      |     |        | discrepancies                             |     |              |     |            |
|      |  5  |   ✅   | Add recovery logic: if extra position     | 🟢  |     3.4      |  3  |     -      |
|      |     |        | at broker, add to DB with warning         |     |              |     |            |
|      |  6  |   ✅   | Add recovery logic: if missing position   | 🟢  |     3.4      |  3  |     -      |
|      |     |        | at broker, mark as closed in DB           |     |              |     |            |
|      |  7  |   ✅   | Implement recovery mode: if major         | 🟢  |     3.4      |  3  |     -      |
|      |     |        | discrepancy (>$100 diff), pause           |     |              |     |            |
|      |     |        | trading, send alert                       |     |              |     |            |
|      |  8  |   -    | Run reconciliation on app startup         | 🟢  |     3.4      |  2  |     -      |
|      |     |        | automatically [DEFERRED]                  |     |              |     |            |
|      |  9  |   -    | Test reconciliation: manually create      | 🟢  |     3.8      |  3  |     -      |
|      |     |        | position in IBKR, restart app,            |     |              |     |            |
|      |     |        | verify reconciliation detects it          |     |              |     |            |
|  4   |     |   ✅   | **Implement Position Sizing Calculator**  | 🟢  |      -       |  -  |     25m    |
|      |  1  |   ✅   | Create services/risk/position_sizer.py    | 🟢  |      -       |  5  |     25m    |
|      |     |        | with PositionSizer class                  |     |              |     |            |
|      |  2  |   ✅   | Implement calculate_position_size()       | 🟢  |     4.1      |  5  |     -      |
|      |     |        | using 2% risk rule: (portfolio_value *    |     |              |     |            |
|      |     |        | 0.02) / (entry_price - stop_loss)         |     |              |     |            |
|      |  3  |   ✅   | Add maximum position size cap: 20% of     | 🟢  |     4.2      |  2  |     -      |
|      |     |        | portfolio value                           |     |              |     |            |
|      |  4  |   ✅   | Implement get_portfolio_value() from      | 🟢  |     4.1      |  3  |     -      |
|      |     |        | IBKR account info                         |     |              |     |            |
|      |  5  |   ✅   | Add validation: ensure position size      | 🟢  |     4.2-4.3  |  2  |     -      |
|      |     |        | doesn't exceed available cash             |     |              |     |            |
|      |  6  |   ✅   | Log position size calculation details     | 🟢  |     4.2      |  1  |     -      |
|      |     |        | for audit trail                           |     |              |     |            |
|      |  7  |   -    | Test position sizer manually: portfolio   | 🟢  |     4.6      |  2  |     -      |
|      |     |        | $10k, entry $100, stop $95, verify        |     |              |     |            |
|      |     |        | 40 shares [MANUAL TEST - USER]            |     |              |     |            |
|  5   |     |   🔄   | **Create Risk Management Engine**         | 🟢  |      4       |  -  |    50m     |
|      |  1  |   ✅   | Create services/risk/risk_manager.py      | 🟢  |      -       |  5  |     -      |
|      |     |        | with RiskManager class                    |     |              |     |            |
|      |  2  |   ✅   | Implement check_portfolio_allocation()    | 🟡  |     5.1      |  3  |     -      |
|      |     |        | that enforces 50% max per strategy        |     |              |     |            |
|      |  3  |   ✅   | Implement validate_trade() that runs      | 🟡  |     4, 5.1   |  5  |     -      |
|      |     |        | all risk checks before allowing           |     |              |     |            |
|      |     |        | trade                                     |     |              |     |            |
|      |  4  |   ✅   | Add check: no duplicate positions (can't  | 🟡  |     5.3      |  2  |     -      |
|      |     |        | buy if already long same symbol)          |     |              |     |            |
|      |  5  |   ✅   | Add check: sufficient capital available   | 🟡  |     5.3      |  2  |     -      |
|      |     |        | for trade                                 |     |              |     |            |
|      |  6  |   ✅   | Add check: position size within limits    | 🟡  |     4, 5.3   |  2  |     -      |
|      |     |        | (20% portfolio cap)                       |     |              |     |            |
|      |  7  |   ✅   | Add check: strategy allocation within     | 🟡  |     5.2, 5.3 |  2  |     -      |
|      |     |        | limit (50% portfolio)                     |     |              |     |            |
|      |  8  |   ✅   | Add check: daily loss limit not hit       | 🟡  |     6, 5.3   |  2  |     -      |
|      |  9  |   ✅   | Return validation result with reason if   | 🟡  |     5.3      |  2  |     -      |
|      |     |        | rejected                                  |     |              |     |            |
|      | 10  |   -    | Test risk manager: try trades that        | 🟡  |     5.9      |  3  |     -      |
|      |     |        | violate each rule, verify rejection       |     |              |     |            |
|  6   |     |   🔄   | **Implement Stop-Loss/Take-Profit         | 🟢  |      -       |  -  |    1h 15m  |
|      |     |        | Management**                              |     |              |     |            |
|      |  1  |   ✅   | Add calculate_stop_loss_price() to        | 🟢  |      -       |  2  |     -      |
|      |     |        | strategy: entry_price * (1 -              |     |              |     |            |
|      |     |        | stop_loss_pct)                            |     |              |     |            |
|      |  2  |   ✅   | Add calculate_take_profit_price() to      | 🟡  |     6.1      |  2  |     -      |
|      |     |        | strategy: entry_price * (1 +              |     |              |     |            |
|      |     |        | take_profit_pct)                          |     |              |     |            |
|      |  3  |   ✅   | Create                                    | 🟡  |     2, 6.1   |  5  |     -      |
|      |     |        | services/trading/execution_engine.py      |     |              |     |            |
|      |     |        | with ExecutionEngine class                |     |              |     |            |
|      |  4  |   ✅   | Implement execute_signal() method: take   | 🟡  |     5, 6.3   |  8  |     -      |
|      |     |        | signal, validate with RiskManager,        |     |              |     |            |
|      |     |        | calculate position size, submit           |     |              |     |            |
|      |     |        | orders                                    |     |              |     |            |
|      |  5  |   ✅   | After market order fills, immediately     | 🟡  |     6.4      |  3  |     -      |
|      |     |        | submit stop-loss order at broker          |     |              |     |            |
|      |     |        | level                                     |     |              |     |            |
|      |  6  |   ✅   | After stop-loss, submit take-profit       | 🟡  |     6.5      |  3  |     -      |
|      |     |        | order at broker level                     |     |              |     |            |
|      |  7  |   ✅   | Log trade to trades table with all        | 🟡  |     6.4      |  3  |     -      |
|      |     |        | details: entry price, stop, TP,           |     |              |     |            |
|      |     |        | indicator values, context                 |     |              |     |            |
|      |  8  |   ✅   | Monitor stop-loss/TP orders: update       | 🟡  |     2, 6.5   |  3  |     -      |
|      |     |        | trade record when filled                  |     |              |     |            |
|      |  9  |   -    | Test full execution flow: generate        | 🟡  |     6.8      |  3  |     -      |
|      |     |        | signal, execute, verify market order +    |     |              |     |            |
|      |     |        | stop + TP in IBKR [MANUAL TEST - USER]   |     |              |     |            |
|  7   |     |   -    | **Build Daily Loss Limit Detector**       | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create                                    | 🟢  |      -       |  5  |     -      |
|      |     |        | services/risk/loss_limit_detector.py      |     |              |     |            |
|      |     |        | with LossLimitDetector class              |     |              |     |            |
|      |  2  |   -    | Add consecutive_losses_today field to     | 🟡  |     7.1      |  2  |     -      |
|      |     |        | strategies table                          |     |              |     |            |
|      |  3  |   -    | Implement track_trade_outcome() that      | 🟡  |     7.2      |  3  |     -      |
|      |     |        | increments/resets consecutive loss        |     |              |     |            |
|      |     |        | counter                                   |     |              |     |            |
|      |  4  |   -    | Implement check_loss_limit() that         | 🟡  |     7.3      |  3  |     -      |
|      |     |        | returns true if >= 3 consecutive          |     |              |     |            |
|      |     |        | losses                                    |     |              |     |            |
|      |  5  |   -    | Add pause_strategy_on_limit() that sets   | 🟡  |     7.4      |  2  |     -      |
|      |     |        | strategy status to paused, logs           |     |              |     |            |
|      |     |        | event                                     |     |              |     |            |
|      |  6  |   -    | Reset consecutive loss counter at start   | 🟡  |     7.3      |  2  |     -      |
|      |     |        | of each trading day (9:30 AM ET)          |     |              |     |            |
|      |  7  |   -    | Send alert email when daily loss limit    | 🟡  |     7.5      |  2  |     -      |
|      |     |        | hit                                       |     |              |     |            |
|      |  8  |   -    | Test loss limit: simulate 3 losing        | 🟡  |     7.7      |  3  |     -      |
|      |     |        | trades, verify strategy pauses on         |     |              |     |            |
|      |     |        | 3rd                                       |     |              |     |            |
|  8   |     |   -    | **Write Integration Tests for Trading     | 🟢  |      -       |  -  |     -      |
|      |     |        | System**                                  |     |              |     |            |
|      |  1  |   -    | Create tests/test_order_service.py with   | 🟢  |      7       |  5  |     -      |
|      |     |        | mocked IBKR client                        |     |              |     |            |
|      |  2  |   -    | Create tests/test_position_service.py     | 🟡  |     8.1      |  5  |     -      |
|      |     |        | testing reconciliation logic              |     |              |     |            |
|      |  3  |   -    | Create tests/test_position_sizer.py       | 🟡  |     8.1      |  3  |     -      |
|      |     |        | testing 2% rule calculations              |     |              |     |            |
|      |  4  |   -    | Create tests/test_risk_manager.py         | 🟡  |     8.1      |  5  |     -      |
|      |     |        | testing all risk validation rules         |     |              |     |            |
|      |  5  |   -    | Create tests/test_execution_engine.py     | 🟡  |     8.1      |  5  |     -      |
|      |     |        | testing full trade execution flow         |     |              |     |            |
|      |  6  |   -    | Create tests/test_loss_limit_detector.py  | 🟡  |     8.1      |  3  |     -      |
|      |     |        | testing consecutive loss tracking         |     |              |     |            |
|      |  7  |   -    | Run pytest and ensure all Phase 5         | 🟡  |     8.2-8.6  |  1  |     -      |
|      |     |        | tests pass with 70%+ coverage             |     |              |     |            |
|  9   |     |   -    | **Document Trading and Risk Management**  | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create docs/TRADING.md documenting IBKR   | 🟢  |      8       |  3  |     -      |
|      |     |        | setup, connection, order types            |     |              |     |            |
|      |  2  |   -    | Document position sizing formula and      | 🟡  |     9.1      |  3  |     -      |
|      |     |        | 2% risk rule with examples                |     |              |     |            |
|      |  3  |   -    | Document all risk management rules:       | 🟡  |     9.2      |  3  |     -      |
|      |     |        | position caps, allocation limits,         |     |              |     |            |
|      |     |        | loss limits                               |     |              |     |            |
|      |  4  |   -    | Document stop-loss placement at broker    | 🟡  |     9.3      |  2  |     -      |
|      |     |        | level (critical safety feature)           |     |              |     |            |
|      |  5  |   -    | Document crash recovery and               | 🟡  |     9.3      |  3  |     -      |
|      |     |        | reconciliation process                    |     |              |     |            |
|      |  6  |   -    | Document daily loss limit (3              | 🟡  |     9.3      |  2  |     -      |
|      |     |        | consecutive losses) and reset timing      |     |              |     |            |
|      |  7  |   -    | Add troubleshooting guide: order          | 🟡  |     9.6      |  3  |     -      |
|      |     |        | rejections, connection failures,          |     |              |     |            |
|      |     |        | reconciliation issues                     |     |              |     |            |

---

**Phase 5 Total Sprint Points:** ~186 points
**Estimated Duration:** 2 weeks
**Key Deliverables:** IBKR integration working, order submission and tracking functional, position reconciliation system, position sizing calculator, risk management engine enforcing all rules, stop-loss orders at broker level, daily loss limit detector, integration tests passing
