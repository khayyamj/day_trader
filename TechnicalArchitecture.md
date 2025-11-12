# Trading App - Technical Architecture

## Tech Stack

### Frontend
**React** (standalone)
- Excellent charting libraries available
- Strong ecosystem for real-time updates
- Easy to create modular, reusable components

### Backend
**Python with FastAPI**
- Superior libraries for technical analysis (pandas, numpy, TA-Lib, pandas_ta)
- Better for numerical computations and data analysis
- Excellent WebSocket support for real-time data
- Robust async capabilities for handling multiple strategies
- Better suited for algorithmic trading logic
- Most trading algorithm examples/resources are in Python

### Database
**PostgreSQL**
- Robust for time-series data
- ACID compliance for trade records
- Support for JSON columns for flexible strategy parameters
- Consider TimescaleDB extension for time-series optimization

### Background Job Processing
**Celery** or **RQ**
- Handle autonomous trading execution
- Schedule periodic tasks (market data updates, strategy evaluation)
- Manage multiple concurrent strategies

### Real-time Communication
**WebSockets** (via FastAPI)
- Push updates to frontend (price changes, trade executions)
- Bidirectional communication for commands

## System Architecture

```
┌─────────────────┐
│  React Frontend │
│  - Charts       │
│  - Controls     │
│  - Dashboards   │
└────────┬────────┘
         │ HTTP/WS
         ↓
┌─────────────────────────┐
│  FastAPI Backend        │
│  - REST API             │
│  - WebSocket Server     │
│  - Business Logic       │
└──────────┬──────────────┘
           │
    ┌──────┴──────┬────────────┐
    ↓             ↓            ↓
┌─────────┐  ┌─────────┐  ┌──────────┐
│PostgreSQL│  │ Celery  │  │  Redis   │
│         │  │ Workers │  │  Cache   │
└─────────┘  └────┬────┘  └──────────┘
                  │
         ┌────────┴────────┐
         ↓                 ↓
    ┌─────────┐      ┌─────────┐
    │IBKR API │      │Twelve   │
    │(Trading)│      │Data API │
    └─────────┘      └─────────┘
```

## API Integrations

### Market Data: Twelve Data
- Free tier available
- Comprehensive technical indicators
- WebSocket support for real-time data
- REST API for historical data
- Rate limits to consider

### Trading Platform: Interactive Brokers (IBKR)
- Python library: `ib_insync`
- Paper trading account for testing
- Real-time order management
- Position tracking
- Commission-free paper trading

**Note**: TradingView doesn't have direct trading API for automation. Use IBKR for programmatic trading.

## Database Schema

### Core Tables

```sql
-- Strategy definitions
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parameters JSONB, -- flexible strategy config
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Stock reference data
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255),
    exchange VARCHAR(50)
);

-- Trade execution records (ENHANCED FOR LEARNING)
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    stock_id INTEGER REFERENCES stocks(id),

    -- Entry details
    entry_timestamp TIMESTAMP NOT NULL,
    entry_price DECIMAL(10,2) NOT NULL,
    entry_reason VARCHAR(100), -- Which signal triggered entry
    intended_entry_price DECIMAL(10,2), -- For slippage analysis

    -- Exit details
    exit_timestamp TIMESTAMP,
    exit_price DECIMAL(10,2),
    exit_reason VARCHAR(100), -- 'signal', 'stop_loss', 'take_profit', 'manual', 'eod'
    intended_exit_price DECIMAL(10,2), -- For slippage analysis

    -- Position details
    quantity INTEGER NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'long' or 'short'

    -- P&L details
    gross_pnl DECIMAL(10,2),
    commission DECIMAL(10,2),
    net_pnl DECIMAL(10,2),
    pnl_pct DECIMAL(10,4), -- Percentage return

    -- Risk management
    initial_stop_loss DECIMAL(10,2),
    initial_take_profit DECIMAL(10,2),
    final_stop_loss DECIMAL(10,2), -- If adjusted during trade
    final_take_profit DECIMAL(10,2),

    -- Trade quality metrics
    max_adverse_excursion DECIMAL(10,2), -- Worst loss during trade
    max_favorable_excursion DECIMAL(10,2), -- Best profit during trade
    hold_duration_seconds INTEGER,

    -- Order execution
    entry_order_id VARCHAR(100),
    exit_order_id VARCHAR(100),

    -- Market context at entry (snapshot for analysis)
    market_context JSONB, -- {volatility, volume_vs_avg, trend, gap_pct, etc.}
    indicator_values JSONB, -- All indicator values at entry time

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Order management
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    stock_id INTEGER REFERENCES stocks(id),
    type VARCHAR(10) NOT NULL, -- 'buy', 'sell', 'stop_loss', 'take_profit'
    quantity INTEGER NOT NULL,
    order_price DECIMAL(10,2),
    stop_loss DECIMAL(10,2),
    take_profit DECIMAL(10,2),
    status VARCHAR(20), -- 'pending', 'filled', 'cancelled', 'expired'
    placed_at TIMESTAMP NOT NULL,
    filled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    broker_order_id VARCHAR(100)
);

-- Time-series stock data
CREATE TABLE stock_data (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(10,2) NOT NULL,
    high DECIMAL(10,2) NOT NULL,
    low DECIMAL(10,2) NOT NULL,
    close DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    UNIQUE(stock_id, timestamp)
);

-- Technical indicators (time-series)
CREATE TABLE indicators (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    indicator_type VARCHAR(50) NOT NULL, -- 'SMA_20', 'EMA_50', 'MACD', etc.
    timestamp TIMESTAMP NOT NULL,
    value DECIMAL(10,4) NOT NULL,
    metadata JSONB, -- for indicators with multiple values (MACD line, signal, histogram)
    UNIQUE(stock_id, indicator_type, timestamp)
);

-- Strategy performance tracking
CREATE TABLE strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    date DATE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_return DECIMAL(10,2),
    total_pnl DECIMAL(10,2),
    max_drawdown DECIMAL(10,2),
    sharpe_ratio DECIMAL(10,4),
    win_rate DECIMAL(5,2),
    UNIQUE(strategy_id, date)
);

-- Portfolio snapshots
CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    timestamp TIMESTAMP NOT NULL,
    total_value DECIMAL(12,2) NOT NULL,
    cash DECIMAL(12,2) NOT NULL,
    positions JSONB, -- array of {symbol, quantity, avg_cost, current_price, pnl}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trade signals (CRITICAL FOR LEARNING - tracks ALL signals, not just executed trades)
CREATE TABLE trade_signals (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    stock_id INTEGER REFERENCES stocks(id),
    timestamp TIMESTAMP NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- 'buy', 'sell', 'hold'
    signal_strength DECIMAL(5,2), -- Optional: how strong was the signal (0-100)
    executed BOOLEAN DEFAULT false,
    trade_id INTEGER REFERENCES trades(id), -- NULL if not executed

    -- Why was signal generated?
    trigger_reason VARCHAR(100), -- 'ma_crossover', 'rsi_oversold', etc.

    -- Why was signal NOT executed (if applicable)?
    non_execution_reason VARCHAR(100), -- 'insufficient_funds', 'risk_limit', 'order_failed', etc.

    -- Market state when signal generated
    indicator_values JSONB, -- All indicator values at signal time
    market_context JSONB, -- Volatility, volume, trend, etc.

    created_at TIMESTAMP DEFAULT NOW()
);

-- Strategy execution events (errors, rejections, missed opportunities)
CREATE TABLE strategy_events (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    stock_id INTEGER REFERENCES stocks(id),
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'order_placed', 'order_filled', 'order_failed', 'order_rejected', 'signal_missed', 'api_error', 'risk_limit_hit', etc.
    severity VARCHAR(20), -- 'info', 'warning', 'error', 'critical'

    -- Event details
    description TEXT,
    metadata JSONB, -- Flexible field for any additional context

    -- Related entities
    trade_id INTEGER REFERENCES trades(id),
    signal_id INTEGER REFERENCES trade_signals(id),
    order_id VARCHAR(100), -- Broker order ID if applicable

    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance and common queries
CREATE INDEX idx_trades_strategy ON trades(strategy_id);
CREATE INDEX idx_trades_stock ON trades(stock_id);
CREATE INDEX idx_trades_entry_timestamp ON trades(entry_timestamp);
CREATE INDEX idx_trades_exit_timestamp ON trades(exit_timestamp);
CREATE INDEX idx_signals_strategy ON trade_signals(strategy_id);
CREATE INDEX idx_signals_timestamp ON trade_signals(timestamp);
CREATE INDEX idx_signals_executed ON trade_signals(executed);
CREATE INDEX idx_events_strategy ON strategy_events(strategy_id);
CREATE INDEX idx_events_timestamp ON strategy_events(timestamp);
CREATE INDEX idx_events_type ON strategy_events(event_type);
```

### Data Collection Strategy (MVP Implementation)

**Critical Design Principle**: Store ALL data with maximum granularity from day 1. Analysis dashboards can be built later, but you cannot recreate missing data.

**What to capture on EVERY trade**:
1. **Intent vs Reality**: Store both intended prices and actual execution prices to measure slippage
2. **Full Context**: Capture all indicator values and market conditions at signal/entry time using JSONB fields
3. **Trade Journey**: Track max favorable/adverse excursion to understand optimal exit points
4. **The Why**: Always store the reason (entry_reason, exit_reason, trigger_reason)

**What to capture on EVERY signal** (even if not executed):
1. Signal type and strength
2. Why it was generated (trigger_reason)
3. Why it wasn't executed (if applicable)
4. Market context and indicator values

**What to capture on EVERY event** (errors, failures, rejections):
1. Event type and severity
2. Description of what happened
3. Any relevant metadata
4. Links to related trades/signals/orders

**Implementation pattern**:
```python
# Example: When generating a signal
signal_data = {
    'strategy_id': strategy.id,
    'stock_id': stock.id,
    'timestamp': now(),
    'signal_type': 'buy',
    'trigger_reason': 'sma_crossover',
    'indicator_values': {
        'sma_20': 105.50,
        'sma_50': 104.25,
        'rsi': 45,
        'macd': 0.75
    },
    'market_context': {
        'volatility': 0.015,
        'volume_vs_avg': 1.2,
        'trend': 'uptrend',
        'gap_pct': 0.5
    }
}
db.insert('trade_signals', signal_data)
```

**Why this matters**:
- Can't perform meaningful analysis without data
- Patterns only emerge from comprehensive records
- Professional traders track everything - you should too
- Storage is cheap, missing insights are expensive

```

## Charting Libraries

### Primary: Lightweight Charts (TradingView)
- Best-in-class candlestick charts
- Highly performant
- Free and open source
- Built by TradingView

### Secondary: Recharts
- Volume charts
- MACD histogram
- Good for simpler visualizations
- React-friendly

### Alternative: TradingView Widgets
- Embedded charting solution
- Free tier available
- Less customization but faster implementation

## Project Structure

```
trading-app/
├── frontend/                  # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/       # Chart components
│   │   │   ├── controls/     # UI controls
│   │   │   ├── dashboard/    # Dashboard layout
│   │   │   └── common/       # Reusable components
│   │   ├── services/         # API client
│   │   ├── hooks/            # Custom React hooks
│   │   ├── utils/            # Helper functions
│   │   └── App.js
│   └── package.json
│
├── backend/                   # Python FastAPI
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Config, security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/
│   │   │   ├── data/         # Market data fetching
│   │   │   ├── trading/      # Trade execution
│   │   │   ├── indicators/   # Technical analysis
│   │   │   └── strategies/   # Trading strategies
│   │   ├── workers/          # Celery tasks
│   │   └── main.py
│   ├── requirements.txt
│   └── alembic/              # Database migrations
│
└── docs/                      # Documentation
    ├── IdeaDevelopment.md
    └── TechnicalArchitecture.md
```

## Key Python Libraries

```
# Core framework
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
alembic

# Trading & Data
ib_insync              # Interactive Brokers
pandas                 # Data manipulation
numpy                  # Numerical computing
ta-lib                 # Technical analysis
pandas_ta              # Additional indicators

# Background jobs
celery
redis

# Utilities
python-dotenv          # Environment variables
httpx                  # Async HTTP client
websockets             # WebSocket support
pydantic               # Data validation
```

## Backtesting System

### Overview

Backtesting validates trading strategies using historical data before risking real capital. The complexity ranges from simple (basic validation) to advanced (production-grade simulation).

### Backtesting Complexity Levels

#### Level 1: Simple Backtesting
Basic validation to test strategy logic:
- Load historical OHLCV data
- Calculate technical indicators
- Iterate through data chronologically
- Generate buy/sell signals
- Assume instant execution at next bar's open
- Track hypothetical profit/loss

**Good for**: Initial strategy validation, rapid prototyping

#### Level 2: Realistic Backtesting
Add real-world friction and costs:
- Slippage (0.1-0.3% price deviation)
- Transaction costs (commissions + bid-ask spread)
- Proper signal timing (signal on close, execute on next open)
- Stop-loss execution realism
- Position sizing constraints

**Good for**: Serious strategy evaluation before paper trading

#### Level 3: Production-Grade Backtesting
Full simulation with edge cases:
- Multiple asset backtesting
- Portfolio-level constraints
- Market impact modeling
- Survivorship bias elimination
- Different market regime testing
- Monte Carlo simulation
- Walk-forward optimization

**Good for**: Professional strategy development

### Critical Issues to Address

#### 1. Look-Ahead Bias (Most Important)
**Problem**: Using future information to make past decisions

**Bad Example**:
```python
if close[i] > sma[i]:  # Calculate signal
    buy_at_price = close[i]  # Execute at same price - WRONG!
```

**Correct Example**:
```python
if close[i] > sma[i]:  # Calculate signal at bar i
    buy_at_price = open[i+1]  # Execute at next bar's open
```

**Key rule**: Signal generation and execution must be in different bars.

#### 2. Slippage
**Reality**: Orders don't execute at exact calculation price

**Implementation**:
```python
# Market buy order
execution_price = calculated_price * 1.001  # +0.1% slippage

# Market sell order
execution_price = calculated_price * 0.999  # -0.1% slippage

# Slippage varies by:
# - Volatility (higher = more slippage)
# - Liquidity (lower = more slippage)
# - Order size (larger = more slippage)
```

#### 3. Transaction Costs
**Components**:
- Commission: $0-5 per trade (IBKR ~$0.005/share, min $1)
- Bid-ask spread: 0.05-0.2% depending on liquidity
- SEC fees: ~$0.0000278 per dollar sold (US stocks)

**Impact**: High-frequency strategies can be profitable in backtest but lose money due to costs.

#### 4. Order Execution Realism

**Market Orders**:
- Execute immediately but at worse price
- Use slippage model

**Limit Orders**:
- Execute only if price reaches limit
- May not fill if price gaps over limit
- Need to check if high/low crossed limit price

**Stop-Loss Orders**:
- Trigger when price crosses stop level
- Execute at next available price (can be worse)
- Check intraday low to see if triggered

#### 5. Indicator Warm-Up Period

**Problem**: Indicators need historical data to calculate

```python
# 200-day SMA needs 200 days before valid
sma_200 = data['close'].rolling(window=200).mean()

# First 199 values are NaN
# Can't generate signals until day 200
# Must start backtest after warm-up period
```

#### 6. Data Quality

**Issues to handle**:
- Stock splits: Adjust historical prices
- Dividends: Account for dividend payments
- Corporate actions: Mergers, spinoffs
- Missing data: Gaps, halts
- Survivorship bias: Don't only test surviving companies

#### 7. Realistic Position Sizing

**Constraints**:
```python
# Can't buy more than account balance
max_position = account_balance / current_price

# Can't short without margin
if trade_type == 'short':
    required_margin = position_value * margin_requirement

# Can't exceed portfolio allocation
position_size = min(
    calculated_size,
    max_position_pct * account_value / current_price
)
```

### Recommended Backtesting Libraries

#### Backtrader (Recommended for this project)
**Pros**:
- Comprehensive features
- Built-in broker simulation with slippage/commissions
- Support for multiple data feeds
- Extensive documentation
- Active community

**Cons**:
- Steeper learning curve
- Somewhat verbose API

**Example**:
```python
import backtrader as bt

class MovingAverageCross(bt.Strategy):
    params = (
        ('fast_period', 20),
        ('slow_period', 50),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position:  # No position
            if self.crossover > 0:  # Fast MA crosses above slow MA
                self.buy()
        elif self.crossover < 0:  # Fast MA crosses below slow MA
            self.close()  # Close position

# Run backtest
cerebro = bt.Cerebro()
cerebro.addstrategy(MovingAverageCross)
cerebro.broker.setcommission(commission=0.001)  # 0.1%
cerebro.broker.set_slippage_perc(0.001)  # 0.1%
cerebro.adddata(data)
cerebro.run()
cerebro.plot()
```

#### vectorbt
**Pros**:
- Extremely fast (vectorized operations)
- Great for parameter optimization
- Beautiful visualizations

**Cons**:
- Less realistic order simulation
- Better for indicator-based strategies

#### Other Options
- **bt**: Simple, Pythonic, good for portfolio strategies
- **zipline**: Professional-grade, used by Quantopian (archived but still usable)
- **PyAlgoTrade**: Event-driven, good for learning

### Database Schema for Backtesting

Add these tables to track backtest results:

```sql
-- Backtest run metadata
CREATE TABLE backtest_runs (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    stock_symbol VARCHAR(10),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(12,2) NOT NULL,
    final_value DECIMAL(12,2) NOT NULL,
    total_return DECIMAL(10,2),
    total_return_pct DECIMAL(10,4),

    -- Performance metrics
    sharpe_ratio DECIMAL(10,4),
    sortino_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,2),
    max_drawdown_pct DECIMAL(10,4),

    -- Trade statistics
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2),
    avg_win DECIMAL(10,2),
    avg_loss DECIMAL(10,2),
    profit_factor DECIMAL(10,4),

    -- Execution parameters
    commission DECIMAL(10,4),
    slippage_pct DECIMAL(10,4),

    -- Strategy parameters
    parameters JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(strategy_id, stock_symbol, start_date, end_date, parameters)
);

-- Individual backtest trades
CREATE TABLE backtest_trades (
    id SERIAL PRIMARY KEY,
    backtest_run_id INTEGER REFERENCES backtest_runs(id) ON DELETE CASCADE,
    entry_date TIMESTAMP NOT NULL,
    entry_price DECIMAL(10,2) NOT NULL,
    exit_date TIMESTAMP,
    exit_price DECIMAL(10,2),
    quantity INTEGER NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'long' or 'short'
    pnl DECIMAL(10,2),
    pnl_pct DECIMAL(10,4),
    commission_paid DECIMAL(10,2),
    exit_reason VARCHAR(50), -- 'signal', 'stop_loss', 'take_profit', 'end_of_data'
    max_adverse_excursion DECIMAL(10,2), -- Worst loss during trade
    max_favorable_excursion DECIMAL(10,2) -- Best profit during trade
);

-- Portfolio value over time (for equity curve)
CREATE TABLE backtest_equity_curve (
    id SERIAL PRIMARY KEY,
    backtest_run_id INTEGER REFERENCES backtest_runs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    portfolio_value DECIMAL(12,2) NOT NULL,
    cash DECIMAL(12,2),
    positions_value DECIMAL(12,2),
    drawdown DECIMAL(10,2),
    drawdown_pct DECIMAL(10,4)
);

-- Create indexes for performance
CREATE INDEX idx_backtest_runs_strategy ON backtest_runs(strategy_id);
CREATE INDEX idx_backtest_trades_run ON backtest_trades(backtest_run_id);
CREATE INDEX idx_backtest_equity_run ON backtest_equity_curve(backtest_run_id);
```

### Implementation Approach

#### Phase 1: Basic Backtesting Service
```python
# backend/app/services/backtesting/simple_backtest.py

import pandas as pd
from typing import Dict, List
from app.services.indicators.calculator import IndicatorCalculator

class SimpleBacktester:
    def __init__(self,
                 initial_capital: float = 10000,
                 commission: float = 0.001,
                 slippage: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run(self,
            strategy,
            data: pd.DataFrame,
            parameters: Dict) -> Dict:
        """
        Run backtest on historical data

        Args:
            strategy: Strategy class with generate_signal method
            data: DataFrame with OHLCV data
            parameters: Strategy parameters

        Returns:
            Dictionary with performance metrics and trade log
        """
        # Initialize
        cash = self.initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = []

        # Calculate indicators
        indicator_calc = IndicatorCalculator()
        data_with_indicators = indicator_calc.calculate_all(data, parameters)

        # Iterate through bars
        for i in range(1, len(data_with_indicators)):
            current_bar = data_with_indicators.iloc[i]
            previous_bar = data_with_indicators.iloc[i-1]

            # Generate signal on previous bar close
            signal = strategy.generate_signal(previous_bar)

            # Execute on current bar open
            execution_price = current_bar['open']

            if signal == 'BUY' and position == 0:
                # Apply slippage to buy
                buy_price = execution_price * (1 + self.slippage)
                shares = int((cash * 0.95) / buy_price)  # Use 95% of cash

                if shares > 0:
                    cost = shares * buy_price
                    commission_cost = cost * self.commission
                    total_cost = cost + commission_cost

                    if total_cost <= cash:
                        cash -= total_cost
                        position = shares
                        entry_price = buy_price

                        trades.append({
                            'entry_date': current_bar['timestamp'],
                            'entry_price': buy_price,
                            'quantity': shares,
                            'commission': commission_cost
                        })

            elif signal == 'SELL' and position > 0:
                # Apply slippage to sell
                sell_price = execution_price * (1 - self.slippage)
                proceeds = position * sell_price
                commission_cost = proceeds * self.commission
                net_proceeds = proceeds - commission_cost

                cash += net_proceeds
                pnl = net_proceeds - (position * entry_price)

                # Update last trade
                trades[-1].update({
                    'exit_date': current_bar['timestamp'],
                    'exit_price': sell_price,
                    'pnl': pnl,
                    'pnl_pct': (pnl / (position * entry_price)) * 100
                })

                position = 0
                entry_price = 0

            # Track equity curve
            portfolio_value = cash + (position * current_bar['close'])
            equity_curve.append({
                'timestamp': current_bar['timestamp'],
                'portfolio_value': portfolio_value
            })

        # Calculate performance metrics
        metrics = self._calculate_metrics(equity_curve, trades)

        return {
            'metrics': metrics,
            'trades': trades,
            'equity_curve': equity_curve
        }

    def _calculate_metrics(self, equity_curve: List, trades: List) -> Dict:
        """Calculate performance metrics"""
        equity_df = pd.DataFrame(equity_curve)

        final_value = equity_df.iloc[-1]['portfolio_value']
        total_return = final_value - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # Calculate drawdown
        equity_df['cummax'] = equity_df['portfolio_value'].cummax()
        equity_df['drawdown'] = equity_df['portfolio_value'] - equity_df['cummax']
        max_drawdown = equity_df['drawdown'].min()
        max_drawdown_pct = (max_drawdown / equity_df['cummax'].max()) * 100

        # Trade statistics
        completed_trades = [t for t in trades if 'pnl' in t]
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        losing_trades = [t for t in completed_trades if t['pnl'] <= 0]

        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(completed_trades) * 100)
                       if completed_trades else 0
        }
```

#### Phase 2: Integration with Backtrader
After validating basic approach, integrate Backtrader for more realistic simulation.

### Key Performance Metrics

#### Returns
- **Total Return**: Absolute dollar gain/loss
- **Total Return %**: Percentage gain/loss
- **Annualized Return**: Return adjusted for time period
- **Compound Annual Growth Rate (CAGR)**: Smoothed annual return

#### Risk Metrics
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return (return per unit of volatility)
- **Sortino Ratio**: Like Sharpe but only considers downside volatility
- **Volatility**: Standard deviation of returns

#### Trade Statistics
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Average Win/Loss**: Mean profit/loss per trade
- **Max Consecutive Wins/Losses**: Streak analysis

#### Benchmark Comparison
- **Alpha**: Excess return vs benchmark (buy-and-hold)
- **Beta**: Correlation to market movements

### Best Practices

1. **Test on unseen data**: Don't optimize on the same data you test on
2. **Use walk-forward analysis**: Train on past, test on future, repeat
3. **Test multiple stocks**: Strategy should work across multiple assets
4. **Test different market conditions**: Bull, bear, and sideways markets
5. **Be conservative**: Add extra slippage/commissions as safety margin
6. **Paper trade first**: After successful backtest, paper trade for 1-3 months
7. **Track why strategy works**: Understanding > curve fitting
8. **Avoid over-optimization**: 60% win rate with simple rules > 80% with 20 parameters

### Common Pitfalls

**The "too good to be true" backtest**:
- 90%+ win rate → Usually look-ahead bias
- Consistent profits every month → Usually overfit to specific period
- Works on one stock only → Not a robust strategy
- Huge returns with minimal drawdown → Usually data quality issues

**Reality check**:
- Professional hedge funds target 15-30% annual returns
- 55-60% win rate is excellent for most strategies
- 20-30% maximum drawdown is common
- If your backtest significantly exceeds these, investigate for errors

### Project Integration

Add backtesting API endpoint:
```python
# backend/app/api/endpoints/backtesting.py

@router.post("/backtest")
async def run_backtest(
    strategy_id: int,
    symbol: str,
    start_date: date,
    end_date: date,
    parameters: Dict
):
    # Fetch historical data
    data = await data_service.get_historical_data(symbol, start_date, end_date)

    # Load strategy
    strategy = await strategy_service.get_strategy(strategy_id)

    # Run backtest
    backtester = SimpleBacktester()
    results = backtester.run(strategy, data, parameters)

    # Store results in database
    backtest_run = await backtest_service.save_results(results)

    return backtest_run
```

## Deployment Considerations

### Development
- Local machine
- Docker Compose for services (PostgreSQL, Redis)
- Hot reload enabled

### Production Options
1. **VPS (DigitalOcean, Linode)**
   - Full control
   - Runs 24/7
   - $10-20/month

2. **Cloud (AWS, GCP)**
   - Scalable
   - More expensive
   - Better monitoring tools

### Operational Requirements
- Must run during market hours (at minimum)
- Consider 24/7 for pre-market/after-hours trading
- Automatic restart on crashes
- Trade state recovery mechanisms

## Open Technical Questions

1. **Data Granularity**: What timeframe resolution? (1min, 5min, 1hour?)
2. **Historical Data**: How much history to store? (1 year, 5 years?)
3. **Backtesting**: Need separate backtesting engine?
4. **Monitoring**: Error tracking (Sentry?), logging strategy?
5. **Notifications**: Email, SMS, Slack for trade alerts?
6. **Authentication**: User login needed or single-user app?
7. **Data Retention**: Archive old data? For how long?
8. **High Availability**: Failover strategy for autonomous trading?

## Security Considerations

- API keys stored in environment variables
- Database credentials secured
- No API keys in frontend code
- HTTPS for all external communication
- Rate limiting on API endpoints
- Input validation on all user inputs
