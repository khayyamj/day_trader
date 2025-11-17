# Strategy Engine Documentation

## Overview

The Strategy Engine is a flexible, extensible system for implementing and executing algorithmic trading strategies. Built on top of the technical indicators system, it provides a framework for generating trading signals based on market data and technical analysis.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    Strategy Engine                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐         ┌───────────────────┐    │
│  │  BaseStrategy    │◄────────│ MACrossoverRSI    │    │
│  │  (Abstract)      │         │  Strategy         │    │
│  └──────────────────┘         └───────────────────┘    │
│          ▲                                              │
│          │                                              │
│  ┌──────────────────┐         ┌───────────────────┐    │
│  │ SignalGenerator  │────────►│ StrategyService   │    │
│  │                  │         │                   │    │
│  └──────────────────┘         └───────────────────┘    │
│          │                            │                 │
│          ▼                            ▼                 │
│  ┌──────────────────┐         ┌───────────────────┐    │
│  │ IndicatorService │         │  Strategy State   │    │
│  │                  │         │  Management       │    │
│  └──────────────────┘         └───────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1. BaseStrategy (Abstract Class)

**Location**: `backend/app/services/strategies/base_strategy.py`

The foundation for all trading strategies. Provides:

- **TradingSignal**: Data class for signal representation
- **SignalType**: Enum for signal types (BUY, SELL, HOLD)
- **Abstract Methods**:
  - `generate_signal()` - Core signal generation logic
  - `get_parameters()` - Return strategy parameters
  - `validate_parameters()` - Validate parameter values
- **Helper Methods**:
  - `get_required_indicators()` - Specify needed indicators
  - `check_data_sufficiency()` - Validate DataFrame completeness

### 2. IndicatorCalculator

**Location**: `backend/app/services/indicators/calculator.py`

Handles technical indicator calculations using pandas-ta:

**Methods**:
- `calculate_ema(df, period, column)` - Exponential Moving Average
- `calculate_rsi(df, period, column)` - Relative Strength Index
- `calculate_all(df, indicators)` - Batch calculation

**Features**:
- Automatic NaN handling during warm-up
- Configurable periods and source columns
- Extensible for additional indicators

### 3. IndicatorService

**Location**: `backend/app/services/indicators/indicator_service.py`

Manages indicator calculation lifecycle:

**Methods**:
- `get_indicators_for_stock()` - Fetch OHLCV + calculate indicators
- `has_sufficient_data()` - Check if stock ready for analysis
- `_check_warm_up()` - Validate indicator reliability
- `_save_indicators()` - Store to database (90-day retention)

**Key Features**:
- Automatic OHLCV data retrieval
- Warm-up period detection (100+ bars recommended)
- Optional database persistence

### 4. SignalGenerator

**Location**: `backend/app/services/strategies/signal_generator.py`

Coordinates signal generation across watchlist:

**Methods**:
- `evaluate_watchlist()` - Process all stocks
- `evaluate_single_stock()` - Process one stock
- `_log_signal()` - Persist signals to database

**Signal Logging**:
All signals (BUY, SELL, HOLD) are logged with:
- Timestamp
- Trigger reason
- Indicator values
- Market context (volatility, volume, trend)
- Executed status

### 5. StrategyService

**Location**: `backend/app/services/strategies/strategy_service.py`

Manages strategy state and lifecycle:

**Methods**:
- `get_strategy_status()` - Get current state
- `activate_strategy()` - Activate with warm-up check
- `pause_strategy()` - Pause with reason logging
- `check_warm_up()` - Verify data sufficiency
- `set_error_status()` - Handle errors

**Strategy States**:
- `active` - Generating signals
- `paused` - Inactive, not generating signals
- `warming` - Active but insufficient data
- `error` - Error state, needs attention

## Implemented Strategies

### MA Crossover + RSI Strategy

**Location**: `backend/app/services/strategies/ma_crossover_rsi.py`

A momentum strategy combining moving average crossovers with RSI confirmation.

#### Strategy Logic

**BUY Conditions** (all must be true):
1. **Bullish Crossover**: Fast EMA crosses above Slow EMA
2. **RSI Confirmation**: RSI < threshold (not overbought)
3. **Position Check**: No existing position

**SELL Conditions** (any can trigger if position exists):
1. **Bearish Crossover**: Fast EMA crosses below Slow EMA
2. **Overbought Exit**: RSI > threshold

**HOLD**: No conditions met

#### Default Parameters

```python
{
    'ema_fast': 20,      # Fast EMA period
    'ema_slow': 50,      # Slow EMA period
    'rsi_period': 14,    # RSI calculation period
    'rsi_threshold': 70  # Overbought threshold
}
```

#### Crossover Detection

The strategy detects crossovers by comparing current and previous bar values:

**Bullish Crossover**:
- Previous bar: Fast EMA ≤ Slow EMA
- Current bar: Fast EMA > Slow EMA

**Bearish Crossover**:
- Previous bar: Fast EMA ≥ Slow EMA
- Current bar: Fast EMA < Slow EMA

#### Market Context

Each signal captures market context:

```python
{
    'volatility': 0.02,          # Std dev of 20-day returns
    'volume_vs_avg': 1.3,        # Current volume / 20-day avg
    'trend': 'uptrend'           # uptrend, downtrend, or sideways
}
```

## Indicator Warm-up Period

### Why Warm-up Matters

Technical indicators require historical data to produce reliable values:

- **EMA(20)**: Needs ~20 bars for initial value, 40+ for stability
- **EMA(50)**: Needs ~50 bars for initial value, 100+ for stability
- **RSI(14)**: Needs ~14 bars for initial value, 28+ for stability

### Recommended Minimum

**100 bars (days)** of historical data before trading:

- Ensures all indicators have stabilized
- Provides reliable crossover detection
- Reduces false signals from initialization

### Warm-up Status

Checked automatically during strategy activation:

```python
{
    'warm_up_complete': True,
    'bars_available': 100,
    'bars_needed': 0,
    'stocks_checked': 5,
    'stocks_ready': 5
}
```

Strategies in "warming" state:
- Will not generate trading signals
- Continue to calculate indicators
- Auto-transition to "active" when ready

## Signal Evaluation Timing

### Daily Evaluation

**Trigger Time**: 4:05 PM ET (after market close)

**Why This Time**:
- Market closes at 4:00 PM ET
- 5-minute buffer ensures bar completion
- Data providers have updated prices
- Sufficient time for order preparation

### Evaluation Flow

```
16:00 ET - Market closes
16:05 ET - Signal evaluation triggered
   │
   ├─> For each stock in watchlist:
   │    ├─> Fetch latest OHLCV data
   │    ├─> Calculate indicators (EMA, RSI)
   │    ├─> Generate signal (BUY/SELL/HOLD)
   │    └─> Log signal to database
   │
   └─> Return evaluation summary
```

## API Usage

### Indicator Calculation

**Calculate indicators for a stock**:

```bash
POST /api/indicators/calculate
Content-Type: application/json

{
  "symbol": "AAPL",
  "indicators": {
    "ema_20": {"type": "ema", "period": 20},
    "ema_50": {"type": "ema", "period": 50},
    "rsi_14": {"type": "rsi", "period": 14}
  },
  "lookback_days": 100,
  "save_to_db": false
}
```

**Response**:

```json
{
  "symbol": "AAPL",
  "total_bars": 100,
  "date_range": {
    "start": "2025-08-09",
    "end": "2025-11-17"
  },
  "warm_up_status": {
    "overall": true,
    "indicators": {
      "ema_20": true,
      "ema_50": true,
      "rsi_14": true
    }
  },
  "latest_values": {
    "close": 151.00,
    "ema_20": 150.25,
    "ema_50": 149.80,
    "rsi_14": 58.3
  },
  "status": "ok"
}
```

### Strategy Management

**Create a new strategy**:

```bash
POST /api/strategies
Content-Type: application/json

{
  "name": "MA Crossover + RSI",
  "description": "Moving average crossover with RSI confirmation",
  "parameters": {
    "ema_fast": 20,
    "ema_slow": 50,
    "rsi_period": 14,
    "rsi_threshold": 70
  }
}
```

**List all strategies**:

```bash
GET /api/strategies
```

**Activate a strategy**:

```bash
POST /api/strategies/1/activate
```

Response indicates warm-up status:

```json
{
  "strategy_id": 1,
  "name": "MA Crossover + RSI",
  "status": "active",
  "warm_up_complete": true,
  "warm_up_bars_remaining": 0,
  "message": "Strategy activated successfully"
}
```

**Pause a strategy**:

```bash
POST /api/strategies/1/pause
Content-Type: application/json

{
  "reason": "Market volatility too high"
}
```

**Update strategy parameters**:

```bash
PUT /api/strategies/1/parameters
Content-Type: application/json

{
  "parameters": {
    "ema_fast": 12,
    "ema_slow": 26,
    "rsi_period": 14,
    "rsi_threshold": 75
  }
}
```

### Signal Evaluation

**Evaluate all watchlist stocks**:

```bash
POST /api/signals/evaluate
Content-Type: application/json

{
  "strategy_id": 1,
  "lookback_days": 100
}
```

**Evaluate a specific stock**:

```bash
POST /api/signals/evaluate
Content-Type: application/json

{
  "strategy_id": 1,
  "symbol": "AAPL",
  "lookback_days": 100
}
```

**Response**:

```json
{
  "strategy_id": 1,
  "strategy_name": "MA Crossover + RSI",
  "stocks_evaluated": 5,
  "signals_generated": 2,
  "signals": [
    {
      "signal_id": 123,
      "symbol": "AAPL",
      "signal_type": "buy",
      "signal_time": "2025-11-17T16:05:00",
      "trigger_reason": "BUY: Bullish crossover detected (EMA20 crossed above EMA50) with RSI(45.2) < 70",
      "indicator_values": {
        "ema_20": 150.25,
        "ema_50": 149.80,
        "rsi_14": 45.2,
        "close": 151.00
      },
      "market_context": {
        "volatility": 0.02,
        "volume_vs_avg": 1.3,
        "trend": "uptrend"
      },
      "executed": false
    }
  ],
  "status": "ok"
}
```

**List recent signals**:

```bash
GET /api/signals?strategy_id=1&limit=50
GET /api/signals?symbol=AAPL&signal_type=buy
GET /api/signals?executed=false
```

## Adding New Strategies

### Step 1: Create Strategy Class

Extend `BaseStrategy` and implement required methods:

```python
from app.services.strategies.base_strategy import BaseStrategy, TradingSignal, SignalType
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    """Your custom strategy."""

    def __init__(self, parameters=None):
        params = {'param1': 10, 'param2': 20}  # Defaults
        if parameters:
            params.update(parameters)

        self.validate_parameters(params)
        super().__init__(name="My Custom Strategy", parameters=params)

    def generate_signal(self, df, current_position=None):
        """Generate trading signal."""
        # Your logic here
        return TradingSignal(
            signal_type=SignalType.BUY,
            symbol="AAPL",
            timestamp=df.index[-1],
            trigger_reason="Your reason",
            indicator_values={},
            market_context={}
        )

    def get_parameters(self):
        """Return parameters."""
        return self.parameters.copy()

    def validate_parameters(self, parameters):
        """Validate parameters."""
        # Your validation logic
        return True

    def get_required_indicators(self):
        """Specify required indicators."""
        return {
            'ema_20': {'type': 'ema', 'period': 20}
        }
```

### Step 2: Register Strategy

Update `SignalGenerator._create_strategy_instance()`:

```python
def _create_strategy_instance(self, strategy: Strategy):
    if strategy.name == "MA Crossover + RSI":
        return MACrossoverRSIStrategy(parameters=strategy.parameters)
    elif strategy.name == "My Custom Strategy":
        return MyCustomStrategy(parameters=strategy.parameters)
    else:
        raise ValueError(f"Unsupported strategy: {strategy.name}")
```

### Step 3: Create via API

```bash
POST /api/strategies
{
  "name": "My Custom Strategy",
  "description": "Custom trading strategy",
  "parameters": {"param1": 10, "param2": 20}
}
```

### Step 4: Activate and Test

```bash
# Activate
POST /api/strategies/2/activate

# Evaluate
POST /api/signals/evaluate
{"strategy_id": 2, "symbol": "AAPL"}
```

## Database Schema

### Strategies Table

```sql
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parameters JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    warm_up_bars_remaining INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Trade Signals Table

```sql
CREATE TABLE trade_signals (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    stock_id INTEGER NOT NULL REFERENCES stocks(id),
    signal_type VARCHAR(20) NOT NULL,
    signal_time TIMESTAMP WITH TIME ZONE NOT NULL,
    executed BOOLEAN NOT NULL DEFAULT FALSE,
    reasons JSONB,
    indicator_values JSONB,
    market_context JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Indicators Table

```sql
CREATE TABLE indicators (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id),
    indicator_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    value NUMERIC(20, 8) NOT NULL,
    meta JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## Testing

### Running Tests

```bash
# Run all strategy tests
pytest tests/test_indicator_calculator.py -v
pytest tests/test_ma_crossover_strategy.py -v
pytest tests/test_strategy_service.py -v

# Run with coverage
pytest tests/ -v --cov=app/services/indicators --cov=app/services/strategies
```

### Test Coverage

Tests include:
- Indicator calculations (EMA, RSI)
- Crossover detection (bullish, bearish)
- Signal generation (BUY, SELL, HOLD)
- State management (activate, pause, warm-up)
- Edge cases (NaN values, insufficient data)
- Error conditions

## Common Use Cases

### 1. Set Up a New Strategy

```python
# Create strategy via API
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

# Response: {"strategy_id": 1, "status": "paused", ...}

# Activate strategy
POST /api/strategies/1/activate

# Check status
GET /api/strategies/1/status
```

### 2. Daily Signal Evaluation

```python
# Scheduled job at 4:05 PM ET
POST /api/signals/evaluate
{
  "strategy_id": 1,
  "lookback_days": 100
}

# Review generated signals
GET /api/signals?strategy_id=1&executed=false
```

### 3. Review Historical Signals

```python
# All signals for AAPL
GET /api/signals?symbol=AAPL&limit=100

# Only BUY signals
GET /api/signals?signal_type=buy

# Unexecuted signals
GET /api/signals?executed=false
```

### 4. Update Strategy Parameters

```python
# Adjust parameters
PUT /api/strategies/1/parameters
{
  "parameters": {
    "rsi_threshold": 75
  }
}

# Re-activate if needed
POST /api/strategies/1/activate
```

### 5. Pause Strategy During Volatility

```python
POST /api/strategies/1/pause
{
  "reason": "Market volatility spike - SPX VIX > 30"
}

# Later, resume
POST /api/strategies/1/activate
```

## Performance Considerations

### Data Loading

- Indicators fetch OHLCV data for lookback period (default: 100 days)
- Use `lookback_days` parameter to optimize for strategy needs
- Database queries are indexed on `stock_id` and `timestamp`

### Indicator Storage

- Optional storage via `save_to_db=true`
- Only stores recent 90 days (configurable)
- Reduces redundant calculations
- Trade-off: Storage space vs computation time

### Batch vs Single Evaluation

- **Watchlist evaluation**: Process all stocks (use for scheduled jobs)
- **Single stock**: Faster for manual testing or specific triggers

## Error Handling

### Strategy State Transitions

```
active ──pause──> paused
  ▲                 │
  │                 │
  └────activate─────┘

active ──error──> error
               (manual recovery needed)

warming ──data ready──> active
warming ──pause──────> paused
```

### Common Errors

**ValueError: "Strategy cannot generate signals in 'warming' state"**
- Solution: Wait for warm-up or add more historical data

**ValueError: "Stock not found"**
- Solution: Add stock to watchlist first

**ValueError: "Insufficient data"**
- Solution: Fetch historical data for stock

**ValueError: "Missing required indicators"**
- Solution: Ensure DataFrame has all required indicator columns

## Integration with Scheduler

Add to `app/services/data/scheduler.py`:

```python
from app.services.strategies.signal_generator import SignalGenerator

def evaluate_daily_signals():
    """Daily signal evaluation job."""
    db = SessionLocal()
    try:
        generator = SignalGenerator(db)

        # Get active strategies
        strategies = db.query(Strategy).filter(
            Strategy.active == True,
            Strategy.status == "active"
        ).all()

        for strategy in strategies:
            result = generator.evaluate_watchlist(strategy.id)
            logger.info(f"Evaluated {strategy.name}: {result['signals_generated']} signals")

    finally:
        db.close()

# Schedule for 4:05 PM ET daily
data_scheduler.add_job(
    evaluate_daily_signals,
    trigger='cron',
    hour=16,
    minute=5,
    timezone='America/New_York',
    id='daily_signal_evaluation'
)
```

## Monitoring and Logging

### Log Levels

- **INFO**: Strategy activation, signal generation, evaluation results
- **DEBUG**: Indicator calculations, warm-up checks, data queries
- **WARNING**: Warm-up incomplete, missing data, NaN values
- **ERROR**: Strategy errors, failed calculations, invalid parameters

### Key Metrics to Monitor

1. **Signal Generation Rate**: Signals generated per day
2. **Warm-up Status**: Stocks ready vs total
3. **Indicator Reliability**: NaN value frequency
4. **Strategy Performance**: Win rate, average gain/loss (Phase 4+)

## Next Steps

### Phase 4: Order Execution Integration

- Connect signals to order placement
- Implement position tracking
- Add risk management rules
- Build execution confirmation

### Future Enhancements

- Additional strategies (MACD, Bollinger Bands, etc.)
- Multi-timeframe analysis
- Portfolio-level risk management
- Backtesting framework
- Strategy optimization tools

## Troubleshooting

### Signals Not Generating

1. Check strategy status: `GET /api/strategies/1/status`
2. Verify warm-up complete: `warm_up_bars_remaining` should be 0
3. Ensure stocks have data: `GET /api/indicators/AAPL/status`
4. Check strategy is active: `status` should be "active"

### Indicator Values Are NaN

1. Verify sufficient historical data (100+ bars)
2. Check OHLCV data is present for date range
3. Review warm-up status in indicator response
4. Ensure indicator periods are less than available data

### Strategy Won't Activate

1. Check warm-up status: May be in "warming" state
2. Verify stocks have sufficient data
3. Review error logs for specific issues
4. Check database connectivity

## Support

For issues or questions:
- Review logs in `backend/logs/`
- Check API docs at `/docs` (FastAPI auto-generated)
- Refer to PRD.md for requirements
- See test files for usage examples
