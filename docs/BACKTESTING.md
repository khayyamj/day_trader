# Backtesting System Documentation

## Overview

The backtesting system validates trading strategies on historical data to assess performance before deploying live. It simulates realistic trading conditions with slippage, commissions, and proper signal-to-execution timing to avoid look-ahead bias.

## Architecture

### Design Decision: Simple Custom Backtester

**Why Not Backtrader/Zipline?**
- **Simplicity**: Easier to understand and debug
- **Control**: Full control over execution logic
- **Integration**: Direct integration with our strategy system
- **Transparency**: Clear, traceable logic for validation

**Future**: Can migrate to Backtrader if needed for advanced features

### Core Components

```
┌──────────────────────────────────────────────────────┐
│                Backtesting System                     │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌────────────────┐        ┌──────────────────┐     │
│  │ BacktestEngine │───────►│ SimpleBacktester │     │
│  │  (Coordinator) │        │  (Event Engine)  │     │
│  └────────────────┘        └──────────────────┘     │
│          │                          │                │
│          │                          ▼                │
│          │                  ┌──────────────────┐    │
│          │                  │ PortfolioState   │    │
│          │                  │ BacktestTrade    │    │
│          │                  └──────────────────┘    │
│          ▼                                           │
│  ┌────────────────┐                                 │
│  │ Results Storage│                                 │
│  │ - BacktestRun  │                                 │
│  │ - Trades       │                                 │
│  │ - EquityCurve  │                                 │
│  └────────────────┘                                 │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## No Look-Ahead Bias Prevention

### The Problem

Look-ahead bias occurs when backtest logic uses information not available at decision time, artificially inflating performance.

**Example of Bias**:
```python
# WRONG: Using close price to both generate AND execute signal
if ema_20 > ema_50:  # Check at close
    buy_at_price = close  # Execute at same close (impossible in real trading!)
```

### Our Solution

**Two-Bar Execution Model**:

```
Bar N (Today):
  - Calculate indicators using OHLC data
  - Generate signal at CLOSE price
  - Store signal for next bar

Bar N+1 (Tomorrow):
  - Execute stored signal at OPEN price
  - New information (next day's open) is realistic
```

**Implementation**:
```python
for i in range(1, len(df)):
    current_bar = df.iloc[i]

    # 1. Execute signal from PREVIOUS bar at current OPEN
    if pending_signal == 'buy':
        execute_buy(price=current_bar['open'])

    # 2. Generate NEW signal at current CLOSE
    signal = strategy.generate_signal(df[:i+1])
    pending_signal = signal.type  # Store for next bar
```

**Why This Works**:
- Signal decision uses only data up to close of Bar N
- Execution happens at open of Bar N+1
- Mimics real trading: decide after close, execute next day
- Cannot use tomorrow's information today

### Verification

Check first few trades manually:
```python
# Trade 1 entry should be at Bar 2's open (after Bar 1 signal)
# Trade 1 signal date = Bar 1 date
# Trade 1 execution date = Bar 2 date
```

## Slippage and Commissions

### Slippage Modeling

**Slippage**: Difference between expected and actual execution price due to market impact and latency.

**Our Model**: 0.1% (10 basis points)

```python
# Buying (pay more)
execution_price = open_price * (1 + 0.001)  # +0.1%

# Selling (receive less)
execution_price = open_price * (1 - 0.001)  # -0.1%
```

**Why 0.1%?**:
- Conservative estimate for liquid stocks (AAPL, MSFT)
- Accounts for bid-ask spread and market impact
- Typical for small retail orders (<$10k)

**Impact on $10,000 trade**:
- Slippage cost = $10

### Commission Modeling

**Per-Trade Commission**: $1.00

**Why $1?**:
- IBKR typical cost for US stocks
- Fixed fee (not percentage)
- Minimum realistic commission

**Impact**:
- Buy: $1 commission
- Sell: $1 commission
- Total per round trip: $2

### Total Cost Example

**Trade**: Buy 100 shares @ $100
- Position value: $10,000
- Buy slippage: $10 (0.1%)
- Buy commission: $1
- **Total entry cost**: $10,011

**Exit**: Sell 100 shares @ $110
- Gross profit: $1,000
- Sell slippage: $11 (0.1%)
- Sell commission: $1
- **Net profit**: $988

**Cost impact**: ~1.2% ($22 / $1,000)

## Position Sizing

### Strategy: 95% of Available Cash

```python
available_cash = portfolio.cash * 0.95
shares = int(available_cash / execution_price)
```

**Why 95%?**:
- Leaves 5% cash buffer for fees
- Prevents overtrading
- Ensures sufficient capital for entry

**Example**:
- Cash: $100,000
- Available: $95,000
- Price: $150
- Shares: 633

## Performance Metrics

### Returns

**Total Return**:
```
Total Return % = (Final Equity / Initial Capital - 1) × 100
```

**Annualized Return**:
```
Annualized % = ((Final / Initial) ^ (1/years) - 1) × 100
```

### Sharpe Ratio

**Formula**:
```
Sharpe = (Mean Daily Return / Std Dev of Returns) × √252
```

**Interpretation**:
- **> 1.0**: Good (exceeds risk-adjusted expectations)
- **> 2.0**: Excellent
- **> 3.0**: Exceptional
- **< 0**: Strategy loses money

**Our Target**: > 1.0

### Maximum Drawdown

**Formula**:
```
For each day:
  Peak = Max equity seen so far
  Drawdown = (Current Equity - Peak) / Peak × 100

Max Drawdown = Most negative drawdown
```

**Interpretation**:
- **< 10%**: Low risk
- **10-20%**: Moderate risk
- **20-30%**: High risk
- **> 30%**: Very high risk

**Our Target**: < 25%

### Win Rate

**Formula**:
```
Win Rate % = (Winning Trades / Total Trades) × 100
```

**Interpretation**:
- **> 60%**: Very good
- **50-60%**: Good
- **40-50%**: Acceptable (if wins > losses)
- **< 40%**: Needs large wins to be profitable

**Typical Range**: 40-60% for trend-following strategies

### Profit Factor

**Formula**:
```
Profit Factor = Gross Profit / Gross Loss
```

**Interpretation**:
- **> 2.0**: Excellent
- **1.5-2.0**: Good
- **1.0-1.5**: Marginal
- **< 1.0**: Losing strategy

**Minimum**: > 1.0 (profitable)

### Average Win/Loss Ratio

**Formula**:
```
Win/Loss Ratio = Avg Win $ / |Avg Loss $|
```

**Interpretation**:
- **> 2.0**: Great (wins 2x losses)
- **1.5-2.0**: Good
- **1.0-1.5**: Acceptable if win rate > 50%
- **< 1.0**: Needs high win rate

## API Usage

### Run a Backtest

```bash
POST /api/backtests
Content-Type: application/json

{
  "strategy_id": 1,
  "symbol": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000.0,
  "slippage_pct": 0.001,
  "commission_per_trade": 1.0
}
```

**Response**:
```json
{
  "backtest_id": 1,
  "symbol": "AAPL",
  "strategy_name": "MA Crossover + RSI",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000.0,
  "final_equity": 115000.0,
  "metrics": {
    "total_return_pct": 15.0,
    "sharpe_ratio": 1.5,
    "max_drawdown_pct": 12.5,
    "win_rate_pct": 55.0,
    "profit_factor": 1.8,
    "total_trades": 20
  },
  "execution_time_seconds": 2.5,
  "bars_processed": 252
}
```

### List All Backtests

```bash
GET /api/backtests
GET /api/backtests?strategy_id=1
GET /api/backtests?symbol=AAPL
```

### Get Backtest Details

```bash
GET /api/backtests/1
```

### Get Trade List

```bash
GET /api/backtests/1/trades
```

Returns all trades with entry/exit details, P&L, and holding periods.

### Get Equity Curve

```bash
GET /api/backtests/1/equity-curve
```

Returns daily equity snapshots for charting.

## Interpreting Results

### Decision Criteria (from PRD)

**Strategy PASSES if**:
- ✅ Sharpe Ratio > 1.0
- ✅ Max Drawdown < 25%
- ✅ Positive total return

**Strategy FAILS if**:
- ❌ Sharpe Ratio ≤ 1.0
- ❌ Max Drawdown ≥ 25%
- ❌ Negative total return

### Red Flags

⚠️ **High Win Rate but Low Profit Factor**
- Suggests small wins, large losses
- Risky: one bad trade wipes out many wins

⚠️ **High Sharpe but Low Total Return**
- Consistent but small gains
- May not justify trading costs

⚠️ **High Return but High Drawdown**
- Risky strategy
- May not be sustainable

### Ideal Profile

✅ Sharpe > 1.5
✅ Drawdown < 15%
✅ Win Rate 50-60%
✅ Profit Factor > 1.5
✅ Annualized Return > 10%

## Validation Process

### Step 1: Single Stock Test

Test on one stock first (e.g., AAPL):

```bash
POST /api/backtests
{
  "strategy_id": 1,
  "symbol": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

**Review**:
- Check Sharpe > 1.0
- Check Drawdown < 25%
- Review trade list for patterns
- Inspect equity curve for smoothness

### Step 2: Multi-Stock Validation

Test on 5 diverse stocks:
- **Tech**: AAPL, MSFT, GOOGL
- **Finance**: JPM
- **Energy**: XOM

**Why Diverse?**:
- Validates strategy isn't over-fit to one sector
- Tests across different volatility profiles
- Ensures robustness

### Step 3: Aggregate Analysis

Calculate average metrics across all stocks:
- Average Sharpe ratio
- Average drawdown
- Average win rate
- Consistency (std dev of returns across stocks)

### Step 4: Parameter Sensitivity

Test with ±20% parameter changes:
- EMA(16/40) instead of EMA(20/50)
- EMA(24/60) instead of EMA(20/50)
- RSI threshold 60 and 80 instead of 70

**Why?**:
- Robust strategies perform well across parameter ranges
- Over-fit strategies fail with small changes
- Identifies optimal parameter zones

## Common Issues

### Issue: Very Few Trades

**Cause**: Strategy too conservative or insufficient volatility

**Solutions**:
- Relax entry conditions (lower RSI threshold)
- Use faster EMAs (10/20 instead of 20/50)
- Extend backtest period

### Issue: Many Trades, Poor Performance

**Cause**: Overtrading, false signals

**Solutions**:
- Add filters (volume, trend confirmation)
- Increase indicator periods (slower signals)
- Add cooling-off period between trades

### Issue: High Sharpe but Negative Return

**Cause**: Calculation error or very low volatility

**Fix**: Review metrics calculation logic

### Issue: Huge Drawdown Early, Recovery Later

**Cause**: Strategy caught in adverse trend

**Action**: Review trades during drawdown period, consider adding trend filter

## Database Schema

### backtest_runs Table

Stores backtest metadata and summary metrics:

```sql
CREATE TABLE backtest_runs (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    stock_id INTEGER REFERENCES stocks(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital NUMERIC(15,2),
    final_equity NUMERIC(15,2),
    total_return_pct NUMERIC(10,4),
    sharpe_ratio NUMERIC(10,4),
    max_drawdown_pct NUMERIC(10,4),
    ...
    UNIQUE(strategy_id, stock_id, start_date, end_date)
);
```

### backtest_trades Table

Individual trade records:

```sql
CREATE TABLE backtest_trades (
    id SERIAL PRIMARY KEY,
    backtest_run_id INTEGER REFERENCES backtest_runs(id),
    trade_number INTEGER,
    entry_date DATE,
    entry_price NUMERIC(10,2),
    exit_date DATE,
    exit_price NUMERIC(10,2),
    shares INTEGER,
    net_pnl NUMERIC(15,2),
    is_winner BOOLEAN,
    ...
);
```

### backtest_equity_curve Table

Daily portfolio snapshots:

```sql
CREATE TABLE backtest_equity_curve (
    id SERIAL PRIMARY KEY,
    backtest_run_id INTEGER REFERENCES backtest_runs(id),
    date DATE,
    equity NUMERIC(15,2),
    cash NUMERIC(15,2),
    position_value NUMERIC(15,2),
    daily_return_pct NUMERIC(10,4),
    drawdown_pct NUMERIC(10,4),
    UNIQUE(backtest_run_id, date)
);
```

## Testing the System

### 1. Load Historical Data

First, ensure stocks have historical data:

```bash
POST /api/market-data/fetch-historical
{
  "symbol": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31"
}
```

### 2. Create Strategy

```bash
POST /api/strategies
{
  "name": "MA Crossover + RSI",
  "parameters": {
    "ema_fast": 20,
    "ema_slow": 50,
    "rsi_period": 14,
    "rsi_threshold": 70
  }
}
```

### 3. Run Backtest

```bash
POST /api/backtests
{
  "strategy_id": 1,
  "symbol": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### 4. Analyze Results

```bash
# Get summary
GET /api/backtests/1

# Get trades
GET /api/backtests/1/trades

# Get equity curve
GET /api/backtests/1/equity-curve
```

### 5. Validate

**Check**:
- ✓ First trade entry date is AFTER first signal date
- ✓ Entry prices are at open (not close)
- ✓ Total trades matches expected
- ✓ Final equity = initial + sum(net_pnl)
- ✓ Win rate = winning_trades / total_trades

## Metrics Calculation Details

### Sharpe Ratio

```python
# Daily returns
returns = equity_series.pct_change()

# Annualized Sharpe (assuming 252 trading days)
sharpe = (returns.mean() / returns.std()) * sqrt(252)
```

**Note**: Assumes risk-free rate = 0 (conservative)

### Max Drawdown

```python
# Running maximum
running_max = equity.expanding().max()

# Drawdown at each point
drawdown = (equity - running_max) / running_max

# Maximum drawdown
max_dd = abs(drawdown.min())
```

### Win Rate

```python
winning_trades = sum(1 for trade in trades if trade.net_pnl > 0)
win_rate = winning_trades / len(trades) * 100
```

### Profit Factor

```python
gross_profit = sum(trade.net_pnl for trade in trades if trade.net_pnl > 0)
gross_loss = abs(sum(trade.net_pnl for trade in trades if trade.net_pnl < 0))

profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
```

## Best Practices

### 1. Sufficient Data

- **Minimum**: 6 months (for annual strategies)
- **Recommended**: 1+ years
- **Ideal**: 2-3 years (multiple market cycles)

### 2. Multiple Stocks

- Test on **5+ stocks** from different sectors
- Validates strategy isn't stock-specific
- Reduces over-fitting risk

### 3. Out-of-Sample Testing

- Train on 2023 data
- Test on 2024 data
- Performance should be similar

### 4. Parameter Sensitivity

- Test ±20% parameter variations
- Robust strategies maintain performance
- Fragile strategies collapse

### 5. Market Condition Diversity

- Include bull markets (2023)
- Include corrections (2022)
- Include high volatility periods

## Troubleshooting

### Backtest Returns Error "Insufficient data"

**Cause**: Not enough historical bars for indicators

**Fix**:
```bash
# Fetch more data
POST /api/market-data/fetch-historical
{
  "symbol": "AAPL",
  "start_date": "2023-01-01",  # Earlier start
  "end_date": "2024-12-31"
}
```

### All Trades Have Same Entry/Exit Dates

**Cause**: Insufficient price variation or data issues

**Fix**: Check OHLCV data quality

### Sharpe Ratio is NaN

**Cause**: Zero volatility or single trade

**Fix**: Extend backtest period, ensure price variation

### Negative Sharpe but Positive Return

**Possible**: High volatility despite gains

**Action**: Review equity curve for stability

## Next Steps After Backtesting

### If Strategy Passes (Sharpe > 1.0, Drawdown < 25%)

1. ✅ Document results
2. ✅ Proceed to Phase 5 (Paper Trading)
3. ✅ Set up risk management
4. ✅ Prepare for live deployment

### If Strategy Fails

1. **Analyze Why**:
   - Which trades lost money?
   - What market conditions caused losses?
   - Are parameters suboptimal?

2. **Refine Strategy**:
   - Adjust parameters
   - Add filters (trend, volume)
   - Test modifications

3. **Retest**:
   - Run new backtests
   - Compare metrics
   - Iterate until pass criteria met

### If Strategy Marginally Passes

- Run longer backtests (2+ years)
- Test on more stocks (10+)
- Reduce position size for safety
- Add stricter risk controls

## Integration with Phase 5

Phase 4 validates the strategy. Phase 5 executes it live:

**Flow**:
```
Phase 4: Backtest ──PASS──> Phase 5: Paper Trading
                      │
                     FAIL
                      │
                      ▼
                  Refine Strategy
                  (iterate Phase 3-4)
```

**What Carries Forward**:
- ✅ Validated strategy parameters
- ✅ Expected performance metrics (baseline)
- ✅ Known risks (drawdown scenarios)
- ✅ Trade frequency expectations

## Appendix: Calculation Examples

### Example Backtest

**Setup**:
- Symbol: AAPL
- Period: 100 days
- Initial Capital: $100,000
- Trades: 10

**Sample Trade**:
- Entry: Day 20, Open = $150.00
- Exit: Day 35, Open = $165.00
- Shares: 633

**Calculations**:
```
Entry Price (with slippage) = $150.00 × 1.001 = $150.15
Exit Price (with slippage) = $165.00 × 0.999 = $164.84

Gross P&L = ($164.84 - $150.15) × 633 = $9,298.77
Commissions = $1 (entry) + $1 (exit) = $2.00
Slippage Cost = ($150.00 × 0.001 × 633) + ($165.00 × 0.001 × 633) = $199.40

Net P&L = $9,298.77 - $2.00 - $199.40 = $9,097.37
Return % = ($164.84 / $150.15 - 1) × 100 = 9.78%
Holding Period = 35 - 20 = 15 days
```

## Support

- See `STRATEGY_ENGINE.md` for strategy documentation
- Check API docs at `/docs`
- Review test files for usage examples
- Refer to PRD.md for requirements
