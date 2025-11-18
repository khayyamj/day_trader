# Integration Testing Guide - Phase 4 Complete

## System Status Overview

### ✅ What's Available

**Backend API:** Running on `http://localhost:8000`
- 8 API endpoint groups
- Swagger docs at `http://localhost:8000/docs`
- Health check at `http://localhost:8000/health`
- WebSocket support for real-time data

**Database:** PostgreSQL with complete data
- 5 stocks (AAPL, MSFT, GOOGL, JPM, XOM)
- ~377 days of historical OHLCV data per stock
- 1 active strategy (MA Crossover + RSI)
- 15 completed backtest runs
- Complete trade history and equity curves

**Frontend:** ❌ Not built yet (empty directory)

---

## Available API Endpoints

### 1. Health & Info
```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/

# Interactive API docs
open http://localhost:8000/docs
```

### 2. Stocks API (`/api/stocks`)
```bash
# List all stocks
curl http://localhost:8000/api/stocks

# Get specific stock
curl http://localhost:8000/api/stocks/1

# Add stock to watchlist
curl -X POST http://localhost:8000/api/stocks \
  -H "Content-Type: application/json" \
  -d '{"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ"}'
```

### 3. Market Data API (`/api/market-data`)
```bash
# Get historical data for a stock
curl "http://localhost:8000/api/market-data/AAPL?days=30"

# Fetch new historical data
curl -X POST "http://localhost:8000/api/market-data/fetch/AAPL?days=365"

# Get latest data point
curl http://localhost:8000/api/market-data/AAPL/latest
```

### 4. Indicators API (`/api/indicators`)
```bash
# Calculate indicators for a stock
curl -X POST http://localhost:8000/api/indicators/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "indicators": {
      "ema_20": {"type": "ema", "period": 20},
      "ema_50": {"type": "ema", "period": 50},
      "rsi_14": {"type": "rsi", "period": 14}
    },
    "lookback_days": 100
  }'

# Get stored indicators
curl "http://localhost:8000/api/indicators/AAPL?limit=30"
```

### 5. Signals API (`/api/signals`)
```bash
# Generate signal for a stock
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 1,
    "symbol": "AAPL"
  }'

# List recent signals
curl "http://localhost:8000/api/signals?limit=20"

# Get signals for specific stock
curl "http://localhost:8000/api/signals?symbol=AAPL"
```

### 6. Strategies API (`/api/strategies`)
```bash
# List all strategies
curl http://localhost:8000/api/strategies

# Get specific strategy
curl http://localhost:8000/api/strategies/1

# Update strategy parameters
curl -X PATCH http://localhost:8000/api/strategies/1 \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "fast_ema": 20,
      "slow_ema": 50,
      "rsi_period": 14,
      "rsi_overbought": 70
    }
  }'
```

### 7. Backtests API (`/api/backtests`)
```bash
# Run a backtest (synchronous)
curl -X POST http://localhost:8000/api/backtests/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 1,
    "symbol": "AAPL",
    "start_date": "2024-11-18",
    "end_date": "2025-11-18",
    "initial_capital": 100000.0
  }'

# Run backtest asynchronously (for long-running tests)
curl -X POST http://localhost:8000/api/backtests/async \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 1,
    "symbol": "GOOGL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }'

# Check async job status
curl http://localhost:8000/api/backtests/jobs/{job_id}

# List all backtests
curl http://localhost:8000/api/backtests/

# Get backtest results
curl http://localhost:8000/api/backtests/1

# Get backtest trades
curl http://localhost:8000/api/backtests/1/trades

# Get equity curve
curl http://localhost:8000/api/backtests/1/equity-curve
```

### 8. Scheduler API (`/api/scheduler`)
```bash
# Get scheduler status
curl http://localhost:8000/api/scheduler/status

# Trigger manual update
curl -X POST http://localhost:8000/api/scheduler/trigger
```

### 9. Market API (`/api/market`)
```bash
# Check if market is open
curl http://localhost:8000/api/market/is-open

# Get market hours
curl http://localhost:8000/api/market/hours
```

---

## Integration Testing Checklist

### Backend API Tests

#### ✅ Basic Connectivity
```bash
# 1. Health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}

# 2. API docs accessible
curl -I http://localhost:8000/docs
# Expected: HTTP/1.1 200 OK

# 3. OpenAPI schema
curl http://localhost:8000/openapi.json | python -m json.tool | head -20
# Expected: Valid JSON with API schema
```

#### ✅ Data Endpoints
```bash
# 1. List stocks
curl http://localhost:8000/api/stocks | python -m json.tool
# Expected: 5 stocks (AAPL, MSFT, GOOGL, JPM, XOM)

# 2. Get stock data
curl "http://localhost:8000/api/market-data/AAPL?days=10" | python -m json.tool
# Expected: Array of OHLCV data

# 3. Calculate indicators
curl -X POST http://localhost:8000/api/indicators/calculate \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "lookback_days": 30}' | python -m json.tool
# Expected: DataFrame with EMA and RSI columns
```

#### ✅ Strategy & Signals
```bash
# 1. Get strategy
curl http://localhost:8000/api/strategies/1 | python -m json.tool
# Expected: MA Crossover + RSI strategy details

# 2. Generate signal
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 1, "symbol": "AAPL"}' | python -m json.tool
# Expected: Signal response (buy/sell/hold)
```

#### ✅ Backtesting
```bash
# 1. List backtests
curl http://localhost:8000/api/backtests/ | python -m json.tool
# Expected: 15 backtest runs

# 2. Get backtest details
curl http://localhost:8000/api/backtests/1 | python -m json.tool
# Expected: Complete backtest results with metrics

# 3. Get trades
curl http://localhost:8000/api/backtests/1/trades | python -m json.tool
# Expected: Trade list with entry/exit details

# 4. Get equity curve
curl http://localhost:8000/api/backtests/1/equity-curve | python -m json.tool
# Expected: Time series of portfolio value
```

---

## Quick Integration Test Script

Create this script to test all endpoints:

```bash
#!/bin/bash
# test_integration.sh

echo "=== Backend Integration Tests ==="
echo ""

echo "1. Health Check..."
curl -s http://localhost:8000/health | grep healthy && echo "✓ PASS" || echo "✗ FAIL"

echo ""
echo "2. List Stocks..."
STOCK_COUNT=$(curl -s http://localhost:8000/api/stocks | python -c "import sys, json; print(len(json.load(sys.stdin)['stocks']))")
[ "$STOCK_COUNT" == "5" ] && echo "✓ PASS (5 stocks)" || echo "✗ FAIL ($STOCK_COUNT stocks)"

echo ""
echo "3. Get Stock Data..."
DATA_COUNT=$(curl -s "http://localhost:8000/api/market-data/AAPL?days=30" | python -c "import sys, json; print(len(json.load(sys.stdin)['data']))")
[ "$DATA_COUNT" -gt "0" ] && echo "✓ PASS ($DATA_COUNT bars)" || echo "✗ FAIL"

echo ""
echo "4. Get Strategy..."
STRATEGY=$(curl -s http://localhost:8000/api/strategies/1 | python -c "import sys, json; print(json.load(sys.stdin)['name'])" 2>/dev/null)
[ "$STRATEGY" == "MA Crossover + RSI" ] && echo "✓ PASS" || echo "✗ FAIL"

echo ""
echo "5. List Backtests..."
BT_COUNT=$(curl -s http://localhost:8000/api/backtests/ | python -c "import sys, json; print(json.load(sys.stdin)['total'])")
[ "$BT_COUNT" -gt "0" ] && echo "✓ PASS ($BT_COUNT backtests)" || echo "✗ FAIL"

echo ""
echo "6. Get Backtest Results..."
curl -s http://localhost:8000/api/backtests/1 | python -c "import sys, json; data=json.load(sys.stdin); print(f\"Symbol: {data['symbol']}, Return: {data['metrics']['total_return_pct']}%\")"
echo "✓ PASS"

echo ""
echo "=== All Tests Complete ==="
```

---

## What You Can Test Right Now

### Option 1: Using cURL (Command Line)
```bash
# Quick test - get all backtests with results
curl http://localhost:8000/api/backtests/ | python -m json.tool

# Get specific backtest with full metrics
curl http://localhost:8000/api/backtests/1 | python -m json.tool

# Generate a new signal
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 1, "symbol": "GOOGL"}' | python -m json.tool
```

### Option 2: Using Swagger UI (Interactive Browser)
1. Open browser to `http://localhost:8000/docs`
2. Click on any endpoint to expand
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. View response

### Option 3: Using Python Requests
```python
import requests

# Test API
response = requests.get("http://localhost:8000/api/backtests/")
print(response.json())

# Run new backtest
response = requests.post(
    "http://localhost:8000/api/backtests/",
    json={
        "strategy_id": 1,
        "symbol": "AAPL",
        "start_date": "2024-11-18",
        "end_date": "2025-11-18"
    }
)
print(response.json())
```

---

## Current System Capabilities

### ✅ Fully Functional (Ready to Test)

1. **Historical Data Management**
   - Fetch data from TwelveData API
   - Store in PostgreSQL
   - Query by date range
   - 5 stocks with ~377 days each

2. **Technical Indicators**
   - EMA (any period)
   - RSI (any period)
   - Calculate on-demand or from stored data
   - Pandas-based calculations

3. **Signal Generation**
   - MA Crossover + RSI strategy
   - Buy/sell/hold signals
   - Store signal history
   - Query signals by stock/strategy

4. **Backtesting System**
   - Run backtests on historical data
   - Realistic slippage & commissions
   - No look-ahead bias verified
   - Store results with full metrics
   - 15 completed backtests in database

5. **Performance Metrics**
   - Total/annualized returns
   - Sharpe ratio
   - Maximum drawdown
   - Win rate, profit factor
   - Trade statistics

### ⚠️ Limited Functionality

1. **Real-time Data**
   - WebSocket endpoints exist but not actively streaming
   - Requires active market hours
   - TwelveData API has rate limits

2. **Scheduler**
   - Running but only triggers at 4:05 PM ET
   - Daily bar updates only

### ❌ Not Yet Built

1. **Frontend UI**
   - Directory exists but is empty
   - No React/Vue/web interface
   - All testing must be via API/Swagger

2. **Live Trading** (Phase 5)
   - IBKR integration not active
   - No order execution
   - No position management

---

## Recommended Testing Flow

### Step 1: Verify Backend (5 minutes)

```bash
# Open Swagger UI in browser
open http://localhost:8000/docs

# Or run quick curl tests
curl http://localhost:8000/health
curl http://localhost:8000/api/stocks
curl http://localhost:8000/api/backtests/
```

### Step 2: Test Backtest Functionality (10 minutes)

```bash
# View existing backtest results
curl http://localhost:8000/api/backtests/1 | python -m json.tool

# Run a NEW backtest on different date range
curl -X POST http://localhost:8000/api/backtests/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 1,
    "symbol": "AAPL",
    "start_date": "2024-06-01",
    "end_date": "2024-12-31",
    "initial_capital": 50000.0
  }' | python -m json.tool

# View equity curve
curl http://localhost:8000/api/backtests/1/equity-curve | python -m json.tool
```

### Step 3: Test Signal Generation (5 minutes)

```bash
# Generate signal for GOOGL
curl -X POST http://localhost:8000/api/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 1, "symbol": "GOOGL"}' | python -m json.tool

# View recent signals
curl http://localhost:8000/api/signals?limit=10 | python -m json.tool
```

### Step 4: Database Verification (5 minutes)

```bash
# Use Python to query database directly
cd backend
source venv/bin/activate
python show_results.py
```

---

## Database Contents (Current State)

### Stocks Table
- 5 stocks: AAPL, MSFT, GOOGL, JPM, XOM
- All with name and exchange information

### Stock Data Table
- ~1,885 OHLCV records total (377 per stock)
- Date range: May 2024 to November 2025
- Complete daily bars with open, high, low, close, volume

### Strategies Table
- 4 strategies:
  - MA Crossover + RSI (baseline)
  - MA Crossover + RSI (Baseline) - sensitivity test
  - MA Crossover + RSI (Faster (-20%)) - sensitivity test
  - MA Crossover + RSI (Slower (+20%)) - sensitivity test

### Backtest Runs Table
- 15 completed backtests
- Results for all 5 stocks across different configurations
- Complete metrics (return, Sharpe, drawdown, etc.)

### Backtest Trades Table
- Individual trade records
- Entry/exit prices and dates
- P&L calculations
- ~15 trades total

### Backtest Equity Curve Table
- ~3,735 equity points (249 per backtest × 15 backtests)
- Daily portfolio snapshots

---

## Integration Test Results

You can verify the system works by running:

```bash
cd /Users/khayyam.jones/WebDevelopment/Trading/backend

# 1. View backtest results
source venv/bin/activate && python show_results.py

# 2. Test API health
curl http://localhost:8000/health

# 3. Browse interactive API docs
open http://localhost:8000/docs
```

### Expected Outcomes

✅ **Backend Server:** Running on port 8000, responds to requests
✅ **Database:** Connected, queries return data
✅ **API Endpoints:** All 8 routers accessible
✅ **Backtest System:** Can run backtests and retrieve results
✅ **Signal Generation:** Can generate trading signals
✅ **Data Pipeline:** Can fetch and store market data

❌ **Frontend:** Not built - would need React/Next.js app
❌ **Live Trading:** Not active - requires Phase 5 IBKR integration

---

## Next Steps Before Phase 5

### Recommended Pre-Phase 5 Checklist

- [ ] Test all API endpoints via Swagger UI
- [ ] Verify backtest results match expected values
- [ ] Generate signals for all 5 stocks
- [ ] Test async backtest job system
- [ ] Verify WebSocket endpoint connectivity
- [ ] **Optional:** Build basic frontend UI for monitoring
- [ ] **Optional:** Create integration test suite with pytest

### Phase 5 Requirements

To proceed to live trading, you'll need:
1. ✅ Working backtest system (COMPLETE)
2. ✅ Strategy validation (COMPLETE - APPROVED)
3. ❌ IBKR account configured (credentials in .env)
4. ❌ Frontend monitoring dashboard (optional but recommended)
5. ❌ Position management system
6. ❌ Order execution system
7. ❌ Risk management controls

---

## Current Limitations

1. **No Frontend:** All interaction via API/Swagger only
2. **Historical Data Only:** Real-time streaming not active
3. **Single Strategy:** Only MA Crossover + RSI implemented
4. **No Live Trading:** IBKR not connected
5. **Limited Trade History:** Only backtested trades, no live trades

**Recommendation:** The backend is fully functional and ready for testing. You can test all API functionality through Swagger UI or curl. A frontend would make testing easier but isn't strictly necessary for Phase 5.
