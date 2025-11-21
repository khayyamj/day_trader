# Trading System Documentation

## Table of Contents

1. [Overview](#overview)
2. [IBKR Integration Setup](#ibkr-integration-setup)
3. [Position Sizing (2% Risk Rule)](#position-sizing-2-risk-rule)
4. [Risk Management Rules](#risk-management-rules)
5. [Order Types and Execution](#order-types-and-execution)
6. [Stop-Loss Safety Features](#stop-loss-safety-features)
7. [Crash Recovery & Reconciliation](#crash-recovery--reconciliation)
8. [Daily Loss Limits](#daily-loss-limits)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This trading system integrates with Interactive Brokers (IBKR) to execute algorithmic trading strategies with comprehensive risk management. All trades are executed in a paper trading environment for safety.

**Key Features:**
- **Broker-Level Stop-Loss**: Stop-loss orders placed at IBKR survive application crashes
- **2% Risk Rule**: No single trade risks more than 2% of portfolio
- **20% Position Cap**: No position exceeds 20% of total portfolio value
- **50% Strategy Limit**: No strategy can allocate more than 50% of portfolio
- **3-Loss Circuit Breaker**: Auto-pause strategy after 3 consecutive losses
- **Position Reconciliation**: Automatic sync between broker and database on startup

---

## IBKR Integration Setup

### Prerequisites

1. **IBKR Paper Trading Account**
   - Sign up at: https://www.interactivebrokers.com/
   - Select "Paper Trading" account type
   - Complete registration and account setup

2. **IB Gateway or TWS Installation**
   - Download from: https://www.interactivebrokers.com/en/trading/tws.php
   - Install either:
     - **IB Gateway** (lightweight, recommended for automated trading)
     - **Trader Workstation (TWS)** (full-featured desktop application)

### Configuration Steps

#### Step 1: Configure IB Gateway/TWS

1. **Launch IB Gateway** (or TWS)

2. **Log in** with paper trading credentials

3. **Configure API Access:**
   - Go to: `Configure` → `API` → `Settings`
   - Enable: **"ActiveX and Socket Clients"**
   - Set port to: **7497** (paper trading port)
   - **7496** is for live trading - never use in development!

4. **Add Trusted IPs:**
   - In API Settings, add **127.0.0.1** to trusted IPs
   - This allows local connections

5. **Disable Read-Only API** (if prompted)

6. **Click "OK"** to save settings

#### Step 2: Configure Application Environment

Add IBKR credentials to your `.env` file:

```bash
# IBKR Connection Settings
IBKR_HOST=127.0.0.1
IBKR_PORT=7497          # Paper trading port
IBKR_CLIENT_ID=1        # Unique client ID (1-32)
```

**Important:** Never commit `.env` file to version control!

#### Step 3: Verify Connection

Run the connection test script:

```bash
cd backend
python test_ibkr_connection.py
```

**Expected Output:**
```
✓ Successfully connected to IBKR!
Account Summary:
  BuyingPower: $X,XXX,XXX.XX
  NetLiquidation: $X,XXX,XXX.XX
  TotalCashValue: $X,XXX,XXX.XX
Current positions: 0
✓ Successfully disconnected
✓ All tests passed!
```

### Connection Management

The `IBKRClient` class handles connection management automatically:

```python
from app.services.trading.ibkr_client import IBKRClient
from app.core.config import settings

# Create client
client = IBKRClient(
    host=settings.IBKR_HOST,
    port=settings.IBKR_PORT,
    client_id=settings.IBKR_CLIENT_ID
)

# Connect (with automatic retry logic)
client.connect()  # Retries 3 times with exponential backoff

# Use client
if client.is_connected:
    account_summary = client.get_account_summary()
    positions = client.get_positions()

# Disconnect
client.disconnect()
```

**Features:**
- Automatic reconnection on connection loss
- Health monitoring
- 3 retry attempts with exponential backoff (5s, 10s, 15s)
- Connection state tracking

---

## Position Sizing (2% Risk Rule)

### Formula

The system uses the **2% risk rule** to calculate position sizes:

```
Position Size = (Portfolio Value × 0.02) / (Entry Price - Stop Loss)
```

**Example:**
- Portfolio Value: $100,000
- Entry Price: $150
- Stop Loss: $145 (3.33% below entry)
- Risk Per Share: $150 - $145 = $5

**Calculation:**
```
Position Size = ($100,000 × 0.02) / $5
             = $2,000 / $5
             = 400 shares
```

**Position Value:** 400 shares × $150 = $60,000

**BUT** - this exceeds the 20% position cap!

### 20% Position Cap

The system enforces a **maximum 20% position size**:

```
Max Position Value = Portfolio Value × 0.20
Max Shares = Max Position Value / Entry Price
```

**Continuing Example:**
```
Max Position Value = $100,000 × 0.20 = $20,000
Max Shares = $20,000 / $150 = 133 shares
```

**Result:** Position is capped at **133 shares** (instead of 400)

This ensures diversification and limits single-position risk.

### Usage Example

```python
from app.services.risk.position_sizer import PositionSizer

# Initialize
sizer = PositionSizer(ibkr_client)

# Calculate position size
result = sizer.calculate_position_size(
    entry_price=150.0,
    stop_loss=145.0
)

print(f"Quantity: {result['quantity']} shares")
print(f"Position Value: ${result['position_value']:,.2f}")
print(f"Risk Amount: ${result['risk_amount']:,.2f}")
print(f"Risk %: {result['risk_percent']:.2f}%")
print(f"Position %: {result['position_percent']:.2f}%")
print(f"Capped: {result['capped']}")
```

### Real-World Scenarios

#### Scenario 1: Small Risk Per Share
- Portfolio: $50,000
- Entry: $100
- Stop: $95 (5% risk)
- **Result:** 200 shares, $20,000 position (20% capped)

#### Scenario 2: Large Risk Per Share
- Portfolio: $50,000
- Entry: $100
- Stop: $50 (50% risk)
- **Result:** 20 shares, $2,000 position (4% of portfolio)

#### Scenario 3: Penny Stock
- Portfolio: $50,000
- Entry: $5
- Stop: $4.50 (10% risk)
- **Result:** 2,000 shares, $10,000 position (20% capped)

---

## Risk Management Rules

The `RiskManager` enforces 6 critical validation rules before any trade:

### Rule 1: No Duplicate Positions

**Prevents:** Holding the same symbol multiple times in one strategy

**Reason:** Increases concentration risk

**Example:**
```python
# If already holding AAPL:
validation = risk_manager.check_duplicate_position(strategy_id, "AAPL")
# Result: REJECTED - "Duplicate position: already holding AAPL"
```

### Rule 2: Sufficient Capital

**Requires:** Available buying power ≥ required capital

**Formula:**
```
Required Capital ≤ Buying Power
```

**Example:**
```python
# Portfolio: $100k, Buying Power: $400k
# Try to buy $500k position:
validation = risk_manager.check_sufficient_capital(500000.0)
# Result: REJECTED - "Insufficient capital"
```

### Rule 3: Position Size Limit (20%)

**Requires:** Single position ≤ 20% of portfolio value

**Formula:**
```
Position Value / Portfolio Value ≤ 0.20
```

**Example:**
```python
# Portfolio: $100k
# Try 25% position ($25k):
validation = risk_manager.check_position_size_limit(25000.0)
# Result: REJECTED - "Position size exceeds 20% limit: 25.0%"
```

### Rule 4: Strategy Allocation Limit (50%)

**Requires:** Total strategy allocation ≤ 50% of portfolio

**Formula:**
```
(Current Allocation + New Position) / Portfolio Value ≤ 0.50
```

**Example:**
```python
# Portfolio: $100k
# Strategy already has $30k in positions
# Try to add $25k position (total would be $55k = 55%):
validation = risk_manager.check_portfolio_allocation(strategy_id, 25000.0)
# Result: REJECTED - "Strategy allocation exceeds 50% limit: 55.0%"
```

### Rule 5: Daily Loss Limit

**Requires:** Strategy not paused due to consecutive losses

**Trigger:** 3 consecutive losing trades

**Example:**
```python
# Strategy paused after 3 losses:
validation = risk_manager.check_daily_loss_limit(strategy_id)
# Result: REJECTED - "Strategy paused (likely due to daily loss limit)"
```

### Rule 6: Complete Trade Validation

The `validate_trade()` method runs ALL checks in sequence:

```python
validation = risk_manager.validate_trade(
    strategy_id=1,
    symbol="AAPL",
    position_size=position_size_dict
)

if not validation.is_valid:
    print(f"Trade rejected: {validation.reason}")
else:
    print("All risk checks passed - trade approved")
```

**Validation Order:**
1. Daily Loss Limit Check
2. Duplicate Position Check
3. Position Size Limit Check
4. Sufficient Capital Check
5. Portfolio Allocation Check

**If ANY check fails, trade is rejected immediately.**

---

## Order Types and Execution

### Market Orders

**Purpose:** Immediate execution at current market price

**Usage:**
```python
from app.services.trading.order_service import OrderService

order = order_service.submit_market_order(
    symbol="AAPL",
    quantity=100,
    action="BUY",  # or "SELL"
    stock_id=stock.id
)

print(f"Order submitted: {order.broker_order_id}")
print(f"Status: {order.status}")  # PENDING, FILLED, REJECTED
```

**Characteristics:**
- Executes immediately during market hours
- No price guarantee
- Best for liquid stocks with tight spreads
- Used for entry orders

### Stop-Loss Orders

**Purpose:** Automatic exit at specified price to limit losses

**Critical:** Placed at **broker level** - survives application crashes!

**Usage:**
```python
stop_order = order_service.submit_stop_loss_order(
    symbol="AAPL",
    quantity=100,
    stop_price=145.00,  # Sell if price drops to $145
    stock_id=stock.id,
    trade_id=trade.id
)
```

**Characteristics:**
- Becomes market order when stop price hit
- Placed at broker (IBKR servers)
- Persists even if app crashes
- Visible in TWS as "STP" order type
- Always SELL orders for long positions

### Take-Profit Orders

**Purpose:** Automatic exit at target profit price

**Usage:**
```python
tp_order = order_service.submit_take_profit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=165.00,  # Sell if price reaches $165
    stock_id=stock.id,
    trade_id=trade.id
)
```

**Characteristics:**
- Limit order at target price
- Placed at broker level
- Visible in TWS as "LMT" order type
- Always SELL orders for long positions

### Order Flow Diagram

```
1. Signal Generated
         ↓
2. Risk Validation
         ↓
3. Position Sizing
         ↓
4. Submit MARKET Order (Entry)
         ↓
5. Wait for Fill
         ↓
6. Submit STOP-LOSS Order (Broker Level) ← Survives Crashes!
         ↓
7. Submit TAKE-PROFIT Order (Broker Level)
         ↓
8. Log Trade to Database
         ↓
9. Monitor Orders (Background Task)
```

---

## Stop-Loss Safety Features

### Critical Safety: Broker-Level Placement

**Why This Matters:**

All stop-loss orders are placed **at the broker level** (IBKR servers), NOT in the application.

**This means:**
- ✅ Stop-loss survives if application crashes
- ✅ Stop-loss survives if server goes down
- ✅ Stop-loss survives if internet disconnects
- ✅ Stop-loss executes even when app is offline
- ✅ Stop-loss visible in IBKR TWS/Gateway

**Verification:**

After placing a stop-loss order:
1. Open IBKR TWS or Gateway
2. Navigate to: `Trade` → `Orders` → `Active Orders`
3. Verify order type shows as **"STP"** (Stop)
4. **Close your trading application**
5. Verify stop-loss order **still appears** in TWS
6. This confirms broker-level placement ✅

### Stop-Loss Calculation

```python
from app.services.strategies.base_strategy import BaseStrategy

# In your strategy class:
stop_price = strategy.calculate_stop_loss_price(
    entry_price=100.0,
    stop_loss_pct=0.05  # 5% stop loss
)

# Result: $95.00
```

**Formula:** `Stop Price = Entry Price × (1 - Stop Loss %)`

**Examples:**
| Entry | Stop % | Stop Price | Max Loss |
|-------|--------|------------|----------|
| $100 | 5% | $95.00 | $5/share |
| $150 | 3% | $145.50 | $4.50/share |
| $50 | 10% | $45.00 | $5/share |

### Execution Engine Integration

The `ExecutionEngine` automatically places stop-loss orders:

```python
from app.services.trading.execution_engine import ExecutionEngine

# Execute signal
result = execution_engine.execute_signal(
    signal=trading_signal,
    strategy=strategy_instance,
    strategy_id=strategy.id
)

if result.success:
    print(f"Trade ID: {result.trade.id}")
    print(f"Market Order: {result.market_order.broker_order_id}")
    print(f"Stop-Loss Order: {result.stop_loss_order.broker_order_id}")  # At broker!
    print(f"Take-Profit Order: {result.take_profit_order.broker_order_id}")
```

**Automatic Flow:**
1. Market order submitted
2. Wait for market order fill (max 30s)
3. **Immediately** submit stop-loss at broker
4. **Immediately** submit take-profit at broker
5. Log complete trade to database

---

## Crash Recovery & Reconciliation

### Position Reconciliation System

The system reconciles positions between **broker** (IBKR) and **database** to detect discrepancies.

**When it Runs:**
- On application startup (optional)
- On demand via API
- After suspected crashes

### Discrepancy Types

#### 1. EXTRA_AT_BROKER

**Scenario:** Position exists at broker but not in database

**Cause:** Manual trade in TWS, or database lost during crash

**Recovery:**
```python
position_service.recover_extra_position(discrepancy, strategy_id)
```

**Action:** Creates recovery trade record in database with metadata:
```json
{
  "recovered": true,
  "recovery_timestamp": "2025-11-20T15:00:00Z"
}
```

#### 2. MISSING_AT_BROKER

**Scenario:** Position in database but not at broker

**Cause:** Manual close in TWS, or broker closed position

**Recovery:**
```python
position_service.recover_missing_position(discrepancy)
```

**Action:** Marks database trades as CLOSED with unknown exit price

#### 3. QUANTITY_MISMATCH

**Scenario:** Different quantities at broker vs database

**Cause:** Partial fills, manual adjustments

**Recovery:** Manual review required

### Major Discrepancy Detection

**Threshold:** Value difference > $100

**Action:**
- Log critical alert
- **Pause all trading** (recommended)
- Send notification to admin
- Require manual review before resuming

```python
discrepancies, total_diff = position_service.reconcile_positions()

if position_service.check_major_discrepancy(total_diff):
    # MAJOR DISCREPANCY - DO NOT TRADE
    print(f"CRITICAL: ${total_diff:.2f} discrepancy detected!")
    # Pause trading, investigate
```

### Reconciliation Example

```python
from app.services.trading.position_service import PositionService

# Run reconciliation
discrepancies, total_diff = position_service.reconcile_positions()

if not discrepancies:
    print("✓ All positions match - no discrepancies")
else:
    print(f"Found {len(discrepancies)} discrepancies:")
    for disc in discrepancies:
        print(f"  {disc.symbol}: broker={disc.broker_quantity}, db={disc.db_quantity}")
        print(f"  Type: {disc.discrepancy_type}")
        print(f"  Value: ${disc.value_difference:.2f}")
```

### Testing Crash Recovery

**Manual Test Procedure:**

1. Start application
2. Execute a trade (creates position)
3. **Forcefully kill application** (kill -9 or Ctrl+C)
4. Verify stop-loss order **still active in TWS** ✅
5. Restart application
6. Run reconciliation
7. Verify position detected and synced

**Expected Result:** Stop-loss order remains active, proving broker-level safety!

---

## Daily Loss Limits

### 3 Consecutive Loss Rule

**Purpose:** Prevent strategy from losing more after bad streak

**Trigger:** 3 consecutive losing trades in same trading day

**Action:** Strategy automatically paused

### Loss Tracking

```python
from app.services.risk.loss_limit_detector import LossLimitDetector

detector = LossLimitDetector(db)

# After trade closes:
detector.track_trade_outcome(trade_id)

# Check if limit hit:
if detector.check_loss_limit(strategy_id):
    # Limit reached - strategy will be paused
    detector.pause_strategy_on_limit(strategy_id)
```

**Tracking Logic:**

- **Loss:** `profit_loss < 0` → Increment counter
- **Win:** `profit_loss >= 0` → Reset counter to 0
- **Breakeven:** `profit_loss == 0` → Counts as win (resets counter)

### Auto-Pause Behavior

**When Strategy Paused:**
- `status` changed to `"paused"`
- Critical alert logged
- Email/notification sent (if configured)
- **All future trades rejected** until manual review

**Example Alert:**
```
TRADING ALERT: Daily Loss Limit Hit
Strategy: MA Crossover RSI
Consecutive Losses: 3
Status: PAUSED
Action Required: Review strategy performance before re-enabling
```

### Daily Reset

**Reset Time:** 9:30 AM ET (market open)

**What Resets:**
- `consecutive_losses_today` counter → 0
- Strategy remains paused (manual resume required)

```python
# Reset all counters (scheduled task at 9:30 AM ET)
detector.reset_daily_counters()
```

### Manual Resume

To resume a paused strategy:

```sql
UPDATE strategies
SET status = 'active', consecutive_losses_today = 0
WHERE id = <strategy_id>;
```

Or via API (when implemented).

### Strategy Status Monitoring

```python
status = detector.get_strategy_status(strategy_id)

print(f"Strategy: {status['strategy_name']}")
print(f"Status: {status['status']}")
print(f"Consecutive Losses: {status['consecutive_losses_today']}/3")
print(f"Losses Until Pause: {status['losses_until_pause']}")
print(f"Is Paused: {status['is_paused']}")
```

---

## Troubleshooting

### Connection Issues

#### Error: "Connection refused (port 7497)"

**Cause:** IB Gateway/TWS not running or API not enabled

**Solutions:**
1. Start IB Gateway or TWS
2. Log in to paper trading account
3. Verify API settings:
   - `Configure` → `API` → `Settings`
   - Enable "ActiveX and Socket Clients"
   - Port: **7497** (paper) not 7496 (live)

#### Error: "Connection refused after 3 attempts"

**Cause:** Firewall, wrong port, or API disabled

**Solutions:**
1. Check firewall allows localhost connections
2. Verify port 7497 in both app config and TWS
3. Add 127.0.0.1 to TWS trusted IPs
4. Restart IB Gateway/TWS after config changes

#### Error: "API connection requires subscription"

**Cause:** Market data subscription required for real-time data

**Solutions:**
1. Subscribe to market data in IBKR account (paid)
2. Use delayed data (free but 15-minute delay)
3. Trade during market hours when data available
4. Use last known prices for testing

### Order Rejection Issues

#### Error: "Order rejected: insufficient margin"

**Cause:** Not enough buying power

**Solutions:**
1. Check account buying power: `sizer.get_available_cash()`
2. Reduce position size
3. Close existing positions
4. Verify paper account funding

#### Error: "Invalid stop price: NaN"

**Cause:** Market data not available

**Solutions:**
1. Subscribe to market data
2. Ensure market is open
3. Use delayed data if acceptable
4. Verify ticker symbol correct

#### Error: "Symbol not found"

**Cause:** Stock not in database

**Solutions:**
1. Add stock to database first:
   ```sql
   INSERT INTO stocks (symbol, name, exchange)
   VALUES ('AAPL', 'Apple Inc.', 'NASDAQ');
   ```
2. Verify symbol spelling
3. Check symbol exists on exchange

### Reconciliation Issues

#### Positions Don't Match

**Cause:** Manual trading in TWS or database out of sync

**Solutions:**
1. Run reconciliation:
   ```python
   discrepancies, diff = position_service.reconcile_positions()
   ```

2. Review discrepancies:
   ```python
   for disc in discrepancies:
       print(f"{disc.symbol}: {disc.discrepancy_type}")
   ```

3. Recover positions:
   ```python
   if disc.discrepancy_type == "EXTRA_AT_BROKER":
       position_service.recover_extra_position(disc, strategy_id)
   elif disc.discrepancy_type == "MISSING_AT_BROKER":
       position_service.recover_missing_position(disc)
   ```

#### Major Discrepancy Alert

**Threshold:** Value difference > $100

**Action Required:**
1. **Stop all trading immediately**
2. Review all positions manually
3. Compare TWS positions with database
4. Identify source of discrepancy
5. Correct database or broker positions
6. Re-run reconciliation
7. Only resume trading when difference < $100

### Risk Validation Failures

#### "Duplicate position"

**Cause:** Already holding symbol

**Solution:** Close existing position first, or skip trade

#### "Position size exceeds 20% limit"

**Cause:** Calculated position too large

**Solutions:**
1. Widen stop-loss (increases risk per share, reduces quantity)
2. Use smaller entry price
3. Accept rejection (good risk management!)

#### "Strategy allocation exceeds 50% limit"

**Cause:** Strategy has too many open positions

**Solutions:**
1. Close some existing positions
2. Wait for positions to close naturally
3. Skip new trade (good risk management!)
4. Create additional strategy for diversification

### Database Issues

#### "Column does not exist: consecutive_losses_today"

**Cause:** Database schema not updated

**Solution:**
```bash
PGPASSWORD=trading_password psql -h localhost -U trading_user -d trading_db \
  -c "ALTER TABLE strategies ADD COLUMN consecutive_losses_today INTEGER DEFAULT 0;"
```

#### "Trade not found"

**Cause:** Trade ID doesn't exist

**Solutions:**
1. Verify trade ID correct
2. Check trade wasn't deleted
3. Verify database connection

### Performance Issues

#### Orders Taking Too Long

**Cause:** Market data delay or network latency

**Solutions:**
1. Check internet connection
2. Verify IBKR server status
3. Reduce timeout values if acceptable
4. Use limit orders instead of market orders

#### Reconciliation Slow

**Cause:** Large number of positions or slow broker connection

**Solutions:**
1. Run reconciliation during off-hours
2. Reduce frequency if running on schedule
3. Optimize database queries
4. Consider caching broker positions

---

## Best Practices

### Trading Execution

1. **Always validate trades** through RiskManager before execution
2. **Always use position sizer** - never hardcode quantities
3. **Always place stop-loss** at broker level immediately after entry
4. **Monitor protective orders** in background task
5. **Run reconciliation** on startup and periodically

### Risk Management

1. **Never bypass risk checks** - they protect your capital
2. **Review paused strategies** before resuming
3. **Investigate major discrepancies** immediately
4. **Keep stop-loss percentages reasonable** (3-10% typical)
5. **Diversify across strategies** to use 50% limit effectively

### Testing

1. **Always test in paper account** first
2. **Verify stop-loss orders in TWS** after placement
3. **Test crash recovery** before going live
4. **Monitor first trades closely** for issues
5. **Keep trading logs** for debugging

### Monitoring

1. **Check logs daily** for errors
2. **Monitor consecutive loss counts** across strategies
3. **Review reconciliation results** on startup
4. **Track position sizes** vs portfolio growth
5. **Audit trade execution** for unexpected behavior

---

## API Integration Examples

### Complete Trade Execution

```python
from app.services.trading.execution_engine import ExecutionEngine
from app.services.strategies.base_strategy import TradingSignal, SignalType
import pandas as pd

# Create signal
signal = TradingSignal(
    signal_type=SignalType.BUY,
    symbol="AAPL",
    timestamp=pd.Timestamp.now(),
    trigger_reason="MA crossover with RSI confirmation",
    indicator_values={
        'ma_fast': 150.5,
        'ma_slow': 149.2,
        'rsi': 45.3
    }
)

# Execute with full risk management
result = execution_engine.execute_signal(
    signal=signal,
    strategy=strategy_instance,
    strategy_id=strategy.id
)

if result.success:
    print(f"✓ Trade executed successfully!")
    print(f"  Trade ID: {result.trade.id}")
    print(f"  Entry: ${result.trade.entry_price:.2f}")
    print(f"  Quantity: {result.trade.quantity} shares")
    print(f"  Stop Loss: ${result.trade.stop_loss:.2f}")
    print(f"  Take Profit: ${result.trade.take_profit:.2f}")
else:
    print(f"✗ Trade rejected: {result.error_message}")
```

### Monitoring Protective Orders

```python
# Background task to monitor stop-loss and take-profit orders
def monitor_orders_task():
    open_trades = db.query(Trade).filter(Trade.status == 'OPEN').all()

    for trade in open_trades:
        execution_engine.monitor_protective_orders(trade.id)
        # Updates trade when stop or TP fills
```

### Position Sizing Workflow

```python
# Get current market price
current_price = 150.00

# Calculate stop and target
stop_price = strategy.calculate_stop_loss_price(current_price)
tp_price = strategy.calculate_take_profit_price(current_price)

# Calculate position size with 2% risk rule
position_size = position_sizer.calculate_position_size(
    entry_price=current_price,
    stop_loss=stop_price
)

# Validate position
is_valid, error = position_sizer.validate_position(position_size)

if not is_valid:
    print(f"Position validation failed: {error}")
    return

# Validate trade with all risk rules
validation = risk_manager.validate_trade(
    strategy_id=strategy.id,
    symbol="AAPL",
    position_size=position_size
)

if validation.is_valid:
    # Proceed with execution
    execute_trade(...)
else:
    print(f"Risk check failed: {validation.reason}")
```

---

## Configuration Reference

### Environment Variables

```bash
# Required IBKR Settings
IBKR_HOST=127.0.0.1        # Localhost
IBKR_PORT=7497             # Paper trading port
IBKR_CLIENT_ID=1           # Client ID (1-32)

# Database Settings
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_db
```

### Strategy Parameters

Required parameters in strategy configuration:

```json
{
  "stop_loss_pct": 0.05,      // 5% stop loss
  "take_profit_pct": 0.10,    // 10% take profit
  "max_position_pct": 0.20,   // 20% max (enforced by system)
  "risk_pct": 0.02            // 2% risk (enforced by system)
}
```

### Risk Limits (Hard-Coded)

These limits are **hard-coded** in the system for safety:

```python
# In PositionSizer
RISK_PERCENT = 0.02          # 2% risk per trade
MAX_POSITION_PERCENT = 0.20  # 20% max position

# In RiskManager
MAX_POSITION_PERCENT = 0.20  # 20% max position
MAX_STRATEGY_ALLOCATION_PERCENT = 0.50  # 50% max per strategy

# In LossLimitDetector
MAX_CONSECUTIVE_LOSSES = 3   # Auto-pause after 3 losses
```

**Cannot be overridden** - these are safety limits!

---

## Logging and Monitoring

### Log Levels

The system uses structured logging:

- **DEBUG**: Calculation details, price data
- **INFO**: Normal operations, successful actions
- **WARNING**: Risk limit hits, recoverable errors
- **ERROR**: Failed operations, validation rejections
- **CRITICAL**: Major discrepancies, system pauses

### Key Log Messages

**Successful Trade:**
```
✓ TRADE EXECUTION COMPLETE
Trade ID: 123
Entry: $150.00 x 100 shares
Stop Loss: $145.00
Take Profit: $165.00
```

**Risk Rejection:**
```
✗ Daily Loss Limit: FAILED - Strategy paused
```

**Major Discrepancy:**
```
MAJOR DISCREPANCY DETECTED: $271.59 (threshold: $100.00)
```

---

## Testing Guide

### Manual Testing Checklist

- [ ] IBKR connection successful
- [ ] Position sizing calculations correct (2% rule)
- [ ] 20% position cap enforced
- [ ] Risk validation rejecting violations
- [ ] Market orders executing
- [ ] Stop-loss orders at broker level
- [ ] Stop-loss survives app restart
- [ ] Take-profit orders placed
- [ ] Loss limit pauses strategy after 3 losses
- [ ] Win resets loss counter
- [ ] Position reconciliation detects discrepancies
- [ ] Major discrepancy alerts trigger

### Automated Testing

```bash
# Run all Phase 5 tests
cd backend
python -m pytest tests/test_order_service.py \
                tests/test_position_sizer.py \
                tests/test_risk_manager.py \
                tests/test_loss_limit_detector.py \
                tests/test_position_service.py \
                -v --cov=app/services/risk \
                   --cov=app/services/trading

# Expected: 78 tests passing, 70%+ coverage
```

### Manual Test Scripts

```bash
# Connection test
python test_ibkr_connection.py

# Position sizing test
python test_position_sizer.py

# Risk validation test
python test_risk_manager.py

# Loss limit test
python test_loss_limit.py

# Order submission test (places real order!)
python test_order_submission.py

# Full execution flow (places real orders!)
python test_full_execution.py

# Position reconciliation (requires manual setup)
python test_position_reconciliation.py
```

---

## Support and Resources

### Interactive Brokers Resources

- **API Documentation**: https://interactivebrokers.github.io/tws-api/
- **ib_insync Documentation**: https://ib-insync.readthedocs.io/
- **Paper Trading**: https://www.interactivebrokers.com/en/trading/free-trading-trial.php
- **TWS Downloads**: https://www.interactivebrokers.com/en/trading/tws.php

### Internal Documentation

- **Architecture**: `/backend/app/ARCHITECTURE.md`
- **PRD**: `/PRD.md`
- **Phase 5 Tasks**: `/tasks/tasks-phase5-trading.md`
- **Test Coverage Report**: `/backend/htmlcov/index.html`

### Getting Help

1. Check logs in application output
2. Review this troubleshooting guide
3. Run test scripts to isolate issue
4. Check IBKR TWS for order status
5. Verify database state with SQL queries

---

## Safety Checklist

Before going live (if ever moving beyond paper trading):

- [ ] All automated tests passing
- [ ] Manual testing completed successfully
- [ ] Stop-loss orders verified at broker level
- [ ] Crash recovery tested
- [ ] Position reconciliation working
- [ ] Risk limits tested and enforced
- [ ] Loss limit auto-pause tested
- [ ] Real account funded appropriately
- [ ] Real market data subscription active
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures documented
- [ ] Emergency shutdown procedure defined

**Remember:** This system is designed for **paper trading only**. Live trading involves real financial risk.

---

**Last Updated:** 2025-11-20
**Version:** Phase 5 Complete
**Status:** Production-Ready for Paper Trading
