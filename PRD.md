# Product Requirements Document (PRD)
## Autonomous Day Trading Application - MVP

**Version**: 1.0
**Date**: 2025-01-13
**Status**: Approved
**Development Timeline**: 2-3 months
**Team**: Solo Developer

---

## 1. Executive Summary

### 1.1 Product Vision
Build an autonomous trading application that executes rule-based trading strategies on paper trading accounts, with comprehensive monitoring, risk management, and data collection for continuous learning and improvement.

### 1.2 MVP Goals
- Implement a single proven trading strategy (Moving Average Crossover with RSI Confirmation)
- Execute trades automatically on IBKR paper trading account
- Apply robust risk management rules to prevent catastrophic losses
- Collect comprehensive trade data for future strategy optimization
- Provide real-time dashboard for monitoring strategy performance
- Validate strategy viability through 3 months of paper trading before considering live trading

### 1.3 Success Criteria
- **Technical**: System runs reliably during market hours with 99%+ uptime, executes all valid signals within 1 minute of generation
- **Trading**: Strategy completes minimum 30 trades over 3 months paper trading with positive Sharpe ratio (>1.0)
- **Risk**: Zero violations of risk management rules, all stop-losses execute correctly
- **Data**: 100% of trades logged with full context (indicators, market conditions, reasons)

---

## 2. Product Context

### 2.1 Problem Statement
Manual trading requires constant monitoring and emotional discipline. Traders often:
- Miss trading signals due to inattention
- Make emotional decisions under pressure
- Fail to consistently apply risk management rules
- Lack comprehensive data to improve strategies over time

### 2.2 Target User
**Primary User**: You (solo trader/developer)
- Learning algorithmic trading principles
- Wants to automate rule-based strategies
- Needs comprehensive data collection for strategy refinement
- Starting with paper trading to validate approach
- Plans to expand to real money only after proven success

### 2.3 Product Positioning
This is a **learning and validation platform** for algorithmic trading, not a production trading system (yet). MVP focuses on proving strategy viability with comprehensive data collection rather than sophisticated features.

---

## 3. MVP Scope

### 3.1 In Scope (Phase 1 - MVP)

#### Core Trading Features
- ✅ Single trading strategy: Moving Average Crossover with RSI Confirmation
- ✅ Long positions only (no short selling)
- ✅ Daily timeframe (end-of-day signals)
- ✅ Paper trading only via IBKR API
- ✅ 5-10 stocks maximum (user-selected watchlist)
- ✅ Automatic trade execution when signals generated
- ✅ Stop-loss and take-profit order management

#### Risk Management
- ✅ Position sizing: 2% risk rule
- ✅ Maximum position size: 20% of portfolio per stock
- ✅ Maximum allocation per strategy: 50% of portfolio
- ✅ Daily loss limit: 3 consecutive losses triggers strategy pause
- ✅ Stop-loss orders placed at broker level (survives app crashes)

#### Data & Analytics
- ✅ 1 year historical data storage per stock
- ✅ Real-time price data streaming
- ✅ Technical indicator calculation (SMA, EMA, RSI)
- ✅ Comprehensive trade logging (entry/exit, P&L, slippage, context)
- ✅ Signal logging (all signals, executed and rejected)
- ✅ Event logging (errors, warnings, system events)

#### User Interface
- ✅ Single-page dashboard with:
  - Main candlestick chart with indicators
  - Volume chart (synchronized timeline)
  - Current open positions with live P&L
  - Recent trades table
  - Active signals and alerts
  - Strategy status (active/paused/error)
  - Portfolio value and cash available
- ✅ Real-time updates via WebSocket

#### Notifications
- ✅ Email notifications for:
  - Trade execution confirmations
  - Daily summary report
  - Risk limit warnings
  - System errors
- ✅ In-app dashboard alerts

#### Backtesting
- ✅ Historical strategy testing on 1 year of data
- ✅ Performance metrics calculation (returns, Sharpe ratio, drawdown, win rate)
- ✅ Trade-by-trade analysis
- ✅ Equity curve visualization
- ✅ Backtest results storage in database

#### Infrastructure
- ✅ Local machine deployment
- ✅ PostgreSQL database
- ✅ FastAPI backend with REST API
- ✅ React frontend
- ✅ Background job processing (Celery or RQ)
- ✅ Automatic restart on crashes (systemd)
- ✅ Crash recovery with state reconciliation

### 3.2 Explicitly Out of Scope (Future Phases)

#### Phase 2 Features (Post-MVP)
- ❌ Multiple strategies running simultaneously
- ❌ Additional strategy types (mean reversion, breakout, etc.)
- ❌ Intraday timeframes (1min, 5min, 15min, 1hour)
- ❌ Short selling
- ❌ Options trading
- ❌ Slack/SMS notifications
- ❌ Weekly/monthly performance reports
- ❌ Advanced backtesting (walk-forward, Monte Carlo)
- ❌ Strategy parameter optimization
- ❌ Cloud deployment (VPS/AWS)

#### Phase 3+ Features
- ❌ Real money trading (only after successful paper trading validation)
- ❌ Machine learning strategy components
- ❌ Multi-user support
- ❌ Mobile app
- ❌ Strategy marketplace
- ❌ Fundamental data integration
- ❌ News sentiment analysis
- ❌ Advanced portfolio management
- ❌ Margin/leverage trading

---

## 4. User Stories & Use Cases

### 4.1 Strategy Configuration & Management

**US-001**: As a trader, I want to configure my Moving Average Crossover strategy parameters (EMA periods, RSI threshold, stop-loss %, take-profit %) so that I can test different configurations.

**Acceptance Criteria**:
- Can set EMA fast period (default: 20)
- Can set EMA slow period (default: 50)
- Can set RSI period (default: 14)
- Can set RSI overbought threshold (default: 70)
- Can set stop-loss percentage (default: 5%)
- Can set take-profit percentage (default: 15%)
- Configuration persists in database
- Changes take effect on next signal evaluation

**US-002**: As a trader, I want to activate/deactivate my strategy so that I can pause trading when needed.

**Acceptance Criteria**:
- Single toggle button on dashboard
- Active strategy generates signals automatically
- Paused strategy stops generating new signals but maintains existing positions
- Status clearly displayed on dashboard
- Reason for pause logged (manual, risk limit, error)

**US-003**: As a trader, I want to define a watchlist of stocks for my strategy to monitor so that I focus on liquid, suitable stocks.

**Acceptance Criteria**:
- Can add up to 10 stock symbols
- Symbol validation against known exchanges
- Can remove stocks from watchlist
- Strategy only generates signals for watchlist stocks
- Watchlist persists in database

### 4.2 Trade Monitoring

**US-004**: As a trader, I want to see all my open positions with real-time P&L so that I know my current exposure.

**Acceptance Criteria**:
- Table showing: Symbol, Quantity, Entry Price, Current Price, P&L ($), P&L (%), Entry Time
- P&L updates in real-time (every 5 seconds)
- Color coding (green for profit, red for loss)
- Shows stop-loss and take-profit levels
- Click position to see trade details

**US-005**: As a trader, I want to see recently executed trades so that I can review what the strategy is doing.

**Acceptance Criteria**:
- Shows last 20 trades
- For each trade: Symbol, Entry/Exit Time, Entry/Exit Price, Quantity, P&L, Exit Reason
- Click trade to see full details (indicator values, market context)
- Filterable by symbol, date range, win/loss

**US-006**: As a trader, I want to see active buy/sell signals so that I know what trades are being considered.

**Acceptance Criteria**:
- Shows pending signals before execution
- For each signal: Symbol, Signal Type, Trigger Reason, Indicator Values, Signal Time
- Shows why signals were rejected (insufficient capital, risk limit, etc.)
- Signal history for last 24 hours

### 4.3 Performance Analysis

**US-007**: As a trader, I want to see my strategy's performance metrics so that I can evaluate if it's working.

**Acceptance Criteria**:
- Total P&L ($ and %)
- Win Rate (%)
- Total trades count
- Average win/loss amounts
- Maximum drawdown
- Sharpe ratio (if sufficient trades)
- Portfolio value chart over time
- Comparison to buy-and-hold benchmark

**US-008**: As a trader, I want to run backtests on historical data so that I can validate my strategy before live trading.

**Acceptance Criteria**:
- Select date range (up to 1 year historical data)
- Select stock symbol
- Select strategy parameters
- Run backtest (takes <30 seconds)
- See results: metrics, equity curve, trade list
- Save backtest results for comparison

### 4.4 Risk Management

**US-009**: As a trader, I want automatic position sizing based on the 2% risk rule so that I don't over-risk my capital.

**Acceptance Criteria**:
- Position size calculated automatically: `Risk Amount / (Entry Price - Stop Loss Price)`
- Never risks more than 2% of portfolio value
- Position size never exceeds 20% of portfolio value
- Calculation shown in trade details
- Override only with explicit manual confirmation

**US-010**: As a trader, I want my strategy to automatically pause after 3 consecutive losses so that I don't continue losing in bad market conditions.

**Acceptance Criteria**:
- Consecutive loss counter tracked per strategy per day
- After 3rd consecutive loss, strategy status changes to "PAUSED"
- Dashboard shows warning message
- Email notification sent
- Strategy resumes automatically next trading day (or manual resume)
- Counter resets at start of each trading day

**US-011**: As a trader, I want all stop-loss orders placed at the broker level so that positions are protected even if my app crashes.

**Acceptance Criteria**:
- Every position has corresponding stop-loss order at IBKR
- Stop-loss order submitted immediately after entry order fills
- Stop-loss price adjustable (if strategy uses trailing stop)
- Order status monitored continuously
- If stop-loss fills, database updated immediately

### 4.5 System Monitoring & Reliability

**US-012**: As a trader, I want to be notified by email when important trading events occur so that I stay informed without constantly monitoring.

**Acceptance Criteria**:
- Email sent on: Trade execution (entry/exit), Daily loss limit warning, Strategy paused, System error/crash
- Email contains: Event type, timestamp, relevant details, link to dashboard
- Emails sent within 1 minute of event
- Can configure email address
- Can disable email notifications

**US-013**: As a trader, I want the system to automatically recover from crashes so that I don't miss trades or lose positions.

**Acceptance Criteria**:
- System restarts automatically within 30 seconds of crash
- On restart: Reconcile database positions with broker positions
- Identify and log discrepancies
- Send crash report email with: Crash time, active positions, pending orders, recovery status
- If major discrepancies, enter recovery mode (manual approval required)
- If minor discrepancies (<$100), auto-fix and resume

---

## 5. Detailed Functional Requirements

### 5.1 Market Data Integration

**FR-001**: System shall fetch 1 year of historical daily OHLCV data for each watchlist stock on initial setup
- Source: Twelve Data API
- Format: Date, Open, High, Low, Close, Volume
- Storage: PostgreSQL `stock_data` table
- Schedule: One-time per stock on first add to watchlist

**FR-002**: System shall fetch latest daily bar at market close (4:00 PM ET) for all watchlist stocks
- Source: Twelve Data API
- Frequency: Daily at 4:05 PM ET
- Retry logic: 3 attempts with exponential backoff
- Failure handling: Log error, send alert, attempt again in 5 minutes

**FR-003**: System shall stream real-time price updates during market hours for dashboard display
- Source: Twelve Data WebSocket API
- Frequency: Real-time (as prices change)
- Data: Symbol, current price, timestamp
- Fallback: If WebSocket fails, poll REST API every 30 seconds

**FR-004**: System shall respect Twelve Data API rate limits
- Free tier: 8 API calls per minute, 800 per day
- Implementation: Request queue with rate limiter
- If limit exceeded: Cache data, delay non-critical requests
- Monitor: Track API usage daily

### 5.2 Technical Indicator Calculation

**FR-005**: System shall calculate required technical indicators after each new daily bar
- Indicators: EMA(20), EMA(50), RSI(14)
- Library: pandas-ta
- Trigger: When new daily bar added to database
- Storage: Store calculated values in `indicators` table (optional - can recalculate)

**FR-006**: System shall handle indicator warm-up period correctly
- EMA(50) requires 50 bars minimum, RSI(14) requires 28 bars for stability
- Recommended warm-up: 100 bars (2x longest period)
- Strategy status: "Warming up (X/100 bars)" until sufficient data
- No signals generated during warm-up period

**FR-007**: System shall provide indicator values for charting
- API endpoint: GET `/api/indicators/calculate?symbol=AAPL&indicators=ema_20,ema_50,rsi_14`
- Returns: Time series data with calculated indicator values
- Format: `[{timestamp, close, ema_20, ema_50, rsi_14}, ...]`

### 5.3 Strategy Engine

**FR-008**: System shall evaluate strategy rules after each daily bar completion (4:05 PM ET)
- For each watchlist stock: Calculate indicators, generate signal (BUY/SELL/HOLD)
- Signal logic (Moving Average Crossover with RSI):
  - **BUY**: EMA(20) crosses above EMA(50) AND RSI < 70 AND no existing position
  - **SELL**: EMA(20) crosses below EMA(50) OR RSI > 70 OR stop-loss/take-profit triggered
- Log all signals to `trade_signals` table (executed or not)

**FR-009**: System shall execute valid BUY signals by placing market orders
- Check risk management rules before execution
- Calculate position size using 2% risk rule
- Submit market order to IBKR
- Submit stop-loss order immediately after fill
- Submit take-profit order (optional)
- Log trade to `trades` table with entry details

**FR-010**: System shall execute SELL signals by closing positions
- Submit market order to close position
- Cancel any existing stop-loss/take-profit orders
- Log exit details to `trades` table
- Update P&L calculations

**FR-011**: System shall monitor stop-loss and take-profit orders
- Poll IBKR every 30 seconds for order status updates
- If filled: Update trade record with exit details
- Calculate slippage (intended vs actual execution price)

### 5.4 Risk Management Engine

**FR-012**: System shall enforce position sizing using 2% risk rule
- Formula: `Position Size = (Portfolio Value × 0.02) ÷ (Entry Price - Stop Loss Price)`
- Never exceed 20% of portfolio value per position
- If calculated size > max, use max size
- Log position size calculation method

**FR-013**: System shall enforce maximum portfolio allocation per strategy
- Track total value of positions for strategy
- Limit: 50% of portfolio value
- If new trade would exceed limit: Reject trade, log reason

**FR-014**: System shall enforce daily loss limit (3 consecutive losses)
- Track consecutive losses per strategy per day
- After 3rd loss: Pause strategy, send alert, log event
- Reset counter at start of each trading day (9:30 AM ET)
- Allow manual resume or auto-resume next day

**FR-015**: System shall place stop-loss orders at broker level
- Every position MUST have stop-loss order at IBKR
- Stop-loss price: Entry price × (1 - stop_loss_percentage)
- Order type: Stop Market Order
- If stop-loss gaps through: Execute at market, log gap amount

**FR-016**: System shall validate sufficient capital before trades
- Check available cash before placing order
- Account for commission costs (~$1 per trade for IBKR)
- If insufficient: Reject trade, log reason "insufficient_funds"

### 5.5 Trade Execution & Order Management

**FR-017**: System shall integrate with Interactive Brokers API via ib_insync library
- Connection: Paper trading account
- Authentication: API credentials from environment variables
- Connection monitoring: Reconnect if disconnected
- Order types supported: Market, Stop Market, Limit (take-profit)

**FR-018**: System shall submit orders and track execution
- Submit market order for entry
- Wait for fill confirmation (timeout: 5 minutes)
- If fill: Submit stop-loss and take-profit orders
- If timeout: Cancel order, log error, send alert
- Store broker order IDs for tracking

**FR-019**: System shall handle order failures gracefully
- Failure types: Rejected, cancelled, insufficient margin, market closed
- Retry logic: Market orders retry once, others fail immediately
- Logging: Log failure details, reason, order parameters
- Notification: Send error alert for all failures

**FR-020**: System shall reconcile positions with broker on startup
- Query IBKR for current positions
- Compare with database records
- If discrepancies: Log differences, update database to match broker
- If major discrepancy (>$100): Enter recovery mode, require manual approval

### 5.6 Data Persistence & Management

**FR-021**: System shall store all trade data with comprehensive context
- Trades table: Entry/exit prices, timestamps, P&L, commission, slippage
- Market context: Indicator values, volatility, volume vs average
- Trade journey: Max favorable/adverse excursion
- Exit reason: Signal, stop-loss, take-profit, manual, end-of-day

**FR-022**: System shall store all signals (executed and rejected)
- Signal type: BUY, SELL, HOLD
- Trigger reason: "ema_crossover", "rsi_overbought", etc.
- Executed: True/False
- Non-execution reason: "insufficient_funds", "risk_limit", "duplicate_position"
- Indicator values at signal time

**FR-023**: System shall store strategy execution events
- Event types: order_placed, order_filled, order_failed, order_rejected, risk_limit_hit, api_error
- Severity: INFO, WARNING, ERROR, CRITICAL
- Event details and metadata
- Linked entities (trade_id, signal_id, order_id)

**FR-024**: System shall implement data retention policies
- Trade data: Keep forever (core business data)
- Trade signals: Keep forever (learning data)
- OHLCV data: Keep 1 year (rolling)
- Logs: 30 days hot, 90 days cold, 1 year archive
- Portfolio snapshots: Keep forever (daily)

### 5.7 Backtesting System

**FR-025**: System shall support historical strategy backtesting
- Library: Backtrader (recommended) or simple custom implementation
- Data: Historical OHLCV from database
- Parameters: Configurable strategy parameters
- Simulation: Include slippage (0.1%), commissions ($1 per trade)
- Realism: Signal on close, execute on next open (no look-ahead bias)

**FR-026**: System shall calculate comprehensive backtest metrics
- Returns: Total, annualized, CAGR
- Risk: Max drawdown, Sharpe ratio, Sortino ratio, volatility
- Trades: Total, winning/losing, win rate, avg win/loss, profit factor
- Equity curve: Daily portfolio values

**FR-027**: System shall store backtest results for comparison
- Store in `backtest_runs` table
- Store individual trades in `backtest_trades` table
- Store equity curve in `backtest_equity_curve` table
- Allow comparison of multiple backtests

### 5.8 Dashboard & Visualization

**FR-028**: System shall provide real-time dashboard with primary chart
- Library: Lightweight Charts (TradingView)
- Chart type: Candlestick
- Timeframe: Daily bars
- Overlays: EMA(20), EMA(50) lines
- Markers: Buy/sell signals, current positions
- Interaction: Zoom, pan, crosshair

**FR-029**: System shall provide synchronized volume chart below main chart
- Library: Recharts
- Chart type: Bar chart
- Data: Daily volume
- Timeline: Synchronized with main chart
- Highlight: Above average volume

**FR-030**: System shall update dashboard in real-time via WebSocket
- Connection: WebSocket to backend
- Updates: Price changes, P&L updates, new signals, new trades
- Frequency: Every 5 seconds during market hours
- Reconnect: Automatic reconnection if disconnected

**FR-031**: System shall provide positions and trades tables on dashboard
- Open positions: Symbol, quantity, entry price, current P&L
- Recent trades: Last 20 trades with details
- Sortable and filterable
- Click to expand details

**FR-032**: System shall display strategy status and portfolio summary
- Strategy status: Active, Paused, Error, Warming Up
- Portfolio value: Total, cash, invested
- Daily P&L: Today's profit/loss
- Win rate: Overall and recent (last 10 trades)

### 5.9 Notification System

**FR-033**: System shall send email notifications for trading events
- SMTP configuration: From environment variables
- Events: Trade execution, risk limit warning, strategy paused, system crash
- Content: Event details, timestamp, relevant context, dashboard link
- Delivery: Within 1 minute of event

**FR-034**: System shall generate daily summary email at market close
- Send time: 4:30 PM ET
- Content: Trades today, P&L, win rate, portfolio value, active positions
- Format: HTML email with tables and summary statistics

**FR-035**: System shall display in-app alerts/notifications
- Toast notifications for: New trade, signal generated, error occurred
- Alert panel: Recent alerts (last 20)
- Severity colors: Info (blue), Warning (yellow), Error (red)

### 5.10 System Operations

**FR-036**: System shall run automatically during market hours
- Start: 9:00 AM ET (30 minutes before market open)
- Stop: 5:00 PM ET (1 hour after market close)
- Can run 24/7 but only trades during market hours
- Check if market open before generating signals

**FR-037**: System shall restart automatically on crashes
- Process manager: systemd (Linux/Mac) or Windows Service
- Restart delay: 10 seconds
- Restart limit: Max 5 restarts in 10 minutes (prevent crash loops)
- On restart: Run recovery process

**FR-038**: System shall implement crash recovery procedure
- Load last known state from database
- Query broker for current positions and orders
- Reconcile differences
- Send crash report email
- Enter recovery mode if discrepancies found
- Resume normal operation after manual approval

**FR-039**: System shall log all operations for debugging
- Application logs: INFO, WARNING, ERROR, CRITICAL
- Storage: File logs rotated daily
- Format: Timestamp, level, module, message
- Retention: 30 days
- Critical errors: Also log to database

---

## 6. Non-Functional Requirements

### 6.1 Performance

**NFR-001**: Signal evaluation latency shall be < 60 seconds
- From daily bar completion to signal generation
- Includes indicator calculation time

**NFR-002**: Order execution latency shall be < 5 minutes
- From signal generation to order submission to broker

**NFR-003**: Dashboard shall load in < 3 seconds
- Initial page load
- Includes chart rendering

**NFR-004**: Real-time updates shall have < 5 second delay
- From price change to dashboard update

**NFR-005**: Backtesting shall complete in < 60 seconds
- For 1 year of daily data, single stock

### 6.2 Reliability

**NFR-006**: System uptime shall be > 99% during market hours
- Downtime budget: ~2.5 hours per trading month
- Excludes planned maintenance

**NFR-007**: Zero data loss on crashes
- All trades persisted to database before execution
- State recoverable from database

**NFR-008**: Order execution success rate shall be > 98%
- Excludes broker rejections (insufficient funds, market closed)
- Includes retry logic

### 6.3 Security

**NFR-009**: All API credentials shall be stored in environment variables
- Never hardcoded in source code
- .env file added to .gitignore
- File permissions: 600 (owner read/write only)

**NFR-010**: Database credentials shall be secured
- Dedicated database user with minimal permissions
- SSL/TLS connection enabled
- Password complexity enforced

**NFR-011**: All external communication shall use HTTPS/TLS
- API calls to Twelve Data, IBKR
- WebSocket connections (WSS)

**NFR-012**: Sensitive data shall not appear in logs
- Never log API keys, passwords, tokens
- Log only non-sensitive contextual info

### 6.4 Maintainability

**NFR-013**: Code shall follow PEP 8 style guide (Python) and Airbnb style guide (JavaScript/React)

**NFR-014**: All public functions shall have docstrings/comments explaining purpose and parameters

**NFR-015**: Database migrations shall be versioned and reversible
- Using Alembic for Python/SQLAlchemy

**NFR-016**: Configuration shall be externalized
- Environment variables for deployment-specific config
- Database tables for business logic config (strategy parameters)

### 6.5 Scalability

**NFR-017**: System shall support up to 10 concurrent watchlist stocks without performance degradation

**NFR-018**: Database schema shall support adding multiple strategies without schema changes
- JSONB columns for flexible strategy parameters

**NFR-019**: System architecture shall allow adding new strategy types without refactoring core components

### 6.6 Usability

**NFR-020**: Dashboard shall be responsive and work on desktop screen sizes (1920x1080 and 1366x768)

**NFR-021**: All user-facing errors shall have clear, actionable messages
- Example: "Insufficient capital to execute trade. Available: $500, Required: $800"

**NFR-022**: Dashboard shall remain functional if WebSocket disconnects
- Fallback to polling every 30 seconds

---

## 7. Technical Architecture

### 7.1 System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User Browser                      │
│                  (React Frontend)                    │
└───────────────┬─────────────────────────────────────┘
                │ HTTP/REST + WebSocket
                │
┌───────────────▼─────────────────────────────────────┐
│                 FastAPI Backend                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐    │
│  │ REST API │  │WebSocket │  │ Business Logic│    │
│  └──────────┘  └──────────┘  └───────────────┘    │
└──┬────────┬────────────┬────────────┬──────────────┘
   │        │            │            │
   │        │            │            │
   ▼        ▼            ▼            ▼
┌──────┐ ┌──────┐  ┌─────────┐  ┌─────────┐
│ Postgres│ │ Redis │  │ Celery  │  │ External│
│  (DB)  │ │(Cache)│  │ Worker  │  │  APIs   │
└────────┘ └───────┘  └────┬────┘  └────┬────┘
                           │              │
                           ▼              ▼
                     ┌──────────┐  ┌──────────┐
                     │ Strategy │  │  Twelve  │
                     │  Engine  │  │   Data   │
                     └──────────┘  │   IBKR   │
                                   └──────────┘
```

### 7.2 Tech Stack

**Frontend**:
- React 18+ (standalone, Create React App or Vite)
- Lightweight Charts (TradingView) for candlestick charts
- Recharts for volume/MACD charts
- Axios for HTTP client
- WebSocket client for real-time updates

**Backend**:
- Python 3.10+
- FastAPI for REST API and WebSocket
- SQLAlchemy for ORM
- Alembic for database migrations
- pandas + pandas-ta for indicator calculations
- ib_insync for IBKR integration
- Celery or RQ for background jobs
- Redis for Celery broker and caching

**Database**:
- PostgreSQL 14+
- Optional: TimescaleDB extension for time-series optimization

**External APIs**:
- Twelve Data (market data)
- Interactive Brokers API (trade execution)

**Deployment**:
- Local machine (MVP)
- systemd for process management
- Docker Compose for PostgreSQL and Redis (optional)

### 7.3 Database Schema

See [TechnicalArchitecture.md](./TechnicalArchitecture.md) for complete schema.

**Core Tables**:
- `strategies`: Strategy definitions and parameters
- `stocks`: Stock reference data
- `stock_data`: OHLCV time-series data
- `trades`: Trade execution records with comprehensive context
- `trade_signals`: All generated signals (executed and rejected)
- `strategy_events`: Errors, warnings, system events
- `orders`: Order management and tracking
- `portfolio_snapshots`: Daily portfolio values
- `backtest_runs`: Backtest metadata and metrics
- `backtest_trades`: Individual backtest trades

### 7.4 API Integrations

#### Twelve Data API
- **Purpose**: Market data (historical and real-time)
- **Authentication**: API key in header
- **Rate Limits**: 8 calls/minute, 800/day (free tier)
- **Endpoints Used**:
  - `/time_series`: Historical OHLCV data
  - `/price`: Real-time price quotes
  - WebSocket: Real-time price streaming

#### Interactive Brokers API
- **Purpose**: Trade execution (paper trading)
- **Library**: ib_insync (Python wrapper)
- **Authentication**: API credentials
- **Connection**: Gateway or TWS desktop application
- **Order Types**: Market, Stop Market, Limit
- **Features**: Position tracking, order status, account info

---

## 8. Testing & Validation Strategy

### 8.1 Unit Testing
- **Coverage Target**: 70% minimum for backend services
- **Framework**: pytest for Python, Jest for React
- **Focus Areas**: Indicator calculations, signal generation, position sizing logic, risk management rules

### 8.2 Integration Testing
- **Broker Integration**: Test IBKR connection, order submission, position reconciliation (use IBKR paper account)
- **Database**: Test all CRUD operations, complex queries
- **API Endpoints**: Test all REST endpoints with various inputs

### 8.3 Backtesting Validation
- **Phase**: Week 7-8 of development
- **Approach**:
  - Run strategy on 1 year historical data for 5 different stocks
  - Verify: Positive Sharpe ratio (>1.0), win rate 40-50%, max drawdown <25%
  - Test different parameter combinations (EMA periods ±20%)
  - Verify no look-ahead bias (signal on close, execute on next open)
- **Success Criteria**: Strategy shows consistent profitability across multiple stocks and parameters

### 8.4 Paper Trading Validation
- **Duration**: 3 months minimum OR 30 completed trades (whichever is longer)
- **Requirements**:
  - Must experience at least 2 different market conditions (bull/bear/sideways)
  - Strategy must be net profitable
  - Maximum drawdown must be <25%
  - No violations of risk management rules
  - All order executions successful
- **Decision Point**: After 3 months, review metrics and decide: Go live with real money, extend testing, or reject strategy

### 8.5 System Testing
- **Crash Recovery**: Simulate crashes during trading, verify recovery
- **API Failures**: Simulate Twelve Data / IBKR API failures, verify fallback behavior
- **Market Conditions**: Test during pre-market, market hours, after-hours, market closed, holidays
- **Edge Cases**: Insufficient capital, position limit reached, daily loss limit hit, stop-loss gap through

---

## 9. Success Metrics

### 9.1 Technical Metrics (System Performance)

| Metric | Target | Measurement |
|--------|--------|-------------|
| System Uptime | >99% during market hours | Monitor uptime logs |
| Signal Latency | <60 seconds | Time from bar close to signal |
| Order Execution Latency | <5 minutes | Time from signal to broker submission |
| Order Success Rate | >98% | Successful fills / total orders |
| Crash Recovery Time | <30 seconds | Time to restart and reconcile |
| API Call Success Rate | >99% | Successful API calls / total calls |

### 9.2 Trading Metrics (Strategy Performance - Backtesting)

| Metric | Target | Acceptable |
|--------|--------|------------|
| Total Return (1 year backtest) | >15% | >5% |
| Sharpe Ratio | >1.5 | >1.0 |
| Maximum Drawdown | <15% | <25% |
| Win Rate | 45-55% | 40-60% |
| Profit Factor | >2.0 | >1.5 |
| Average Win/Loss Ratio | >1.5 | >1.2 |

### 9.3 Trading Metrics (Strategy Performance - Paper Trading)

| Metric | Target | Minimum Acceptable |
|--------|--------|-------------------|
| Total Return (3 months) | >5% | >0% (break-even) |
| Sharpe Ratio | >1.5 | >1.0 |
| Maximum Drawdown | <15% | <25% |
| Win Rate | 45-55% | 40-65% |
| Total Trades | 30+ | 30 (required) |
| Risk Rule Violations | 0 | 0 (required) |

### 9.4 Data Quality Metrics

| Metric | Target |
|--------|--------|
| Trade Data Completeness | 100% (all fields populated) |
| Signal Data Capture Rate | 100% (all signals logged) |
| Event Logging Coverage | 100% (all critical events logged) |
| Data Integrity Errors | 0 (no orphaned records, broken relationships) |

### 9.5 User Experience Metrics

| Metric | Target |
|--------|--------|
| Dashboard Load Time | <3 seconds |
| Real-time Update Delay | <5 seconds |
| Email Notification Delivery | <1 minute from event |
| Alert Acknowledgment Time | User reviews within 1 hour |

---

## 10. Development Timeline (2-3 Months)

### Phase 1: Foundation (Weeks 1-2)

**Week 1: Project Setup & Infrastructure**
- Set up project structure (frontend, backend, database)
- Initialize Git repository
- Configure development environment
- Set up PostgreSQL database
- Set up Redis (if using Celery)
- Create initial database schema with Alembic
- Configure API credentials (Twelve Data, IBKR)
- Set up environment variables and .env file
- **Deliverable**: Development environment ready, database initialized

**Week 2: Core Backend Structure**
- Set up FastAPI application with basic routing
- Implement database models (SQLAlchemy)
- Create API endpoints structure (placeholder implementations)
- Set up WebSocket connection
- Implement basic logging system
- Create configuration management module
- **Deliverable**: Backend skeleton with database connectivity

### Phase 2: Market Data Integration (Weeks 3-4)

**Week 3: Historical Data Pipeline**
- Implement Twelve Data API client
- Create service to fetch historical OHLCV data
- Implement data storage in `stock_data` table
- Create stock watchlist management (add/remove stocks)
- Build data validation and error handling
- Implement rate limiting for API calls
- **Deliverable**: Historical data fetching and storage working

**Week 4: Real-time Data & Caching**
- Implement real-time price streaming (WebSocket or polling)
- Set up Redis caching for price data
- Create data update scheduler (Celery beat or APScheduler)
- Implement daily bar completion detection (4:05 PM ET trigger)
- Add market hours detection logic
- **Deliverable**: Real-time and daily data updates working

### Phase 3: Indicators & Strategy Engine (Weeks 5-6)

**Week 5: Technical Indicators**
- Integrate pandas-ta library
- Implement indicator calculation service (EMA, RSI)
- Create indicator calculation scheduler (trigger on new daily bar)
- Store indicator values in database (optional)
- Build indicator API endpoints for frontend
- Implement indicator warm-up period handling
- **Deliverable**: Indicators calculating correctly

**Week 6: Strategy Engine**
- Implement Moving Average Crossover strategy logic
- Build signal generation service
- Create signal evaluation scheduler (daily at 4:05 PM ET)
- Implement signal logging to `trade_signals` table
- Build strategy state management (active/paused/warming)
- Add strategy configuration API endpoints
- **Deliverable**: Strategy generating signals correctly

### Phase 4: Backtesting System (Weeks 7-8)

**Week 7: Backtest Implementation**
- Integrate Backtrader library OR implement simple custom backtester
- Build backtest service with slippage and commission modeling
- Implement performance metrics calculation
- Create backtest results storage (database tables)
- Build backtest API endpoints
- **Deliverable**: Backtesting functional

**Week 8: Backtest Validation & Tuning**
- Run backtests on 5 different stocks, 1 year each
- Analyze results and validate strategy performance
- Test parameter sensitivity (EMA periods ±20%)
- Verify no look-ahead bias
- Document backtest results
- **Decision Point**: Proceed if Sharpe ratio >1.0 and drawdown <25%, otherwise refine strategy

### Phase 5: Trading Execution & Risk Management (Weeks 9-10)

**Week 9: IBKR Integration & Order Execution**
- Set up IBKR paper trading account
- Integrate ib_insync library
- Implement broker connection management (connect, reconnect)
- Build order submission service (market orders)
- Implement order tracking and status monitoring
- Create position reconciliation service
- **Deliverable**: Can place orders via IBKR paper account

**Week 10: Risk Management System**
- Implement position sizing calculator (2% risk rule)
- Build portfolio allocation tracker
- Create daily loss limit detector (3 consecutive losses)
- Implement stop-loss order placement at broker
- Build take-profit order management
- Add risk rule validation before trade execution
- Implement strategy pause/resume logic
- **Deliverable**: Risk management rules enforced

### Phase 6: Frontend Dashboard (Weeks 11-12)

**Week 11: Core Dashboard UI**
- Set up React application (Create React App or Vite)
- Implement dashboard layout (main chart, tables, status panels)
- Integrate Lightweight Charts for candlestick chart
- Integrate Recharts for volume chart
- Build positions table component
- Build recent trades table component
- Create strategy status display
- **Deliverable**: Dashboard UI structure complete

**Week 12: Real-time Updates & Polish**
- Implement WebSocket client for real-time updates
- Connect chart to live price data
- Add indicator overlays to chart (EMA lines)
- Implement real-time P&L updates
- Build alert/notification UI components
- Add strategy control buttons (start/stop, configure)
- Polish UI/UX, add loading states, error handling
- **Deliverable**: Full dashboard functional

### Phase 7: System Operations & Monitoring (Week 13+)

**Week 13: Notifications & Logging**
- Implement email notification service (SMTP)
- Create notification templates (trade execution, alerts, daily summary)
- Build event logging system
- Implement crash detection and recovery procedure
- Set up systemd service for auto-restart
- Create daily summary email scheduler
- **Deliverable**: Notifications and monitoring working

**Week 14: Testing & Bug Fixes**
- Comprehensive integration testing
- Test crash recovery scenarios
- Test API failure handling
- Fix identified bugs
- Performance optimization
- Documentation updates
- **Deliverable**: System stable and ready for paper trading

**Week 15+: Paper Trading Validation**
- Deploy to local machine (or VPS if ready)
- Start paper trading with IBKR
- Monitor daily for issues
- Collect comprehensive trade data
- Review performance weekly
- **Duration**: 3 months minimum or 30 trades
- **Outcome**: Decision to proceed to real money or refine further

---

## 11. Risks & Mitigation Strategies

### 11.1 Development Risks

**Risk**: Timeline slippage (solo developer, 2-3 month aggressive timeline)
- **Likelihood**: High
- **Impact**: Medium (delays paper trading start)
- **Mitigation**:
  - Ruthlessly prioritize MVP features only
  - Cut nice-to-have features if behind schedule
  - Use existing libraries (pandas-ta, backtrader, ib_insync) instead of building from scratch
  - Allocate buffer time in weeks 13-14 for catch-up
- **Contingency**: Extend timeline to 3-4 months if needed

**Risk**: Learning curve on unfamiliar technologies (some experience with stack)
- **Likelihood**: Medium
- **Impact**: Medium (slows development)
- **Mitigation**:
  - Allocate time for learning in early weeks
  - Use official documentation and tutorials
  - Start with simpler components, build complexity gradually
  - Leverage AI assistants for code examples and debugging
- **Contingency**: Consider alternatives if too difficult (e.g., simpler charting library if Lightweight Charts too complex)

**Risk**: Underestimated complexity in specific areas
- **Likelihood**: Medium
- **Impact**: Medium to High
- **Mitigation**:
  - Identify high-risk components early (IBKR integration, real-time data streaming)
  - Build proof-of-concepts for risky areas in first 2 weeks
  - Keep architecture flexible to accommodate changes
- **Contingency**: Simplify or defer problematic features to Phase 2

### 11.2 Technical Risks

**Risk**: API integration failures (Twelve Data or IBKR)
- **Likelihood**: Medium
- **Impact**: High (blocks core functionality)
- **Mitigation**:
  - Test API access in Week 1 (verify credentials work)
  - Implement robust error handling and retry logic
  - Set up fallback mechanisms (cache, alternative data sources)
  - Monitor API status and rate limits closely
- **Contingency**: Switch to alternative data provider if Twelve Data unreliable (Yahoo Finance, Alpha Vantage)

**Risk**: Data quality issues (missing data, incorrect prices, splits not adjusted)
- **Likelihood**: Medium
- **Impact**: High (corrupts strategy performance)
- **Mitigation**:
  - Validate data on ingestion (check for gaps, outliers)
  - Compare multiple data sources for critical decisions
  - Implement data quality monitoring and alerts
  - Use adjusted prices from API (account for splits/dividends)
- **Contingency**: Manual data cleaning, maintain backup data source

**Risk**: System crashes during trading cause positions to be untracked
- **Likelihood**: Low to Medium
- **Impact**: Critical (financial loss, uncontrolled exposure)
- **Mitigation**:
  - **Critical**: Place stop-loss orders at broker level (not just in app)
  - Implement automatic restart (systemd)
  - Build crash recovery with broker reconciliation
  - Send immediate alerts on crashes
  - Test recovery thoroughly before paper trading
- **Contingency**: Manual monitoring during first weeks of paper trading, emergency stop-trading procedure

**Risk**: Database corruption or data loss
- **Likelihood**: Low
- **Impact**: High (lose trade history, analysis data)
- **Mitigation**:
  - Use PostgreSQL with ACID guarantees
  - Implement daily automated backups
  - Test backup restoration procedure
  - Use database constraints to prevent invalid data
- **Contingency**: Restore from backups, reconcile with broker trade history

### 11.3 Trading & Strategy Risks

**Risk**: Strategy performs poorly in paper trading (loses money, low Sharpe ratio)
- **Likelihood**: Medium
- **Impact**: Medium (delays going live, requires strategy refinement)
- **Mitigation**:
  - Thorough backtesting on multiple stocks and time periods (Week 7-8)
  - Conservative risk management (2% rule, loss limits)
  - Start paper trading with clear success criteria (Sharpe >1.0)
  - Monitor performance weekly, identify issues early
- **Contingency**: Extend paper trading, refine strategy parameters, test alternative strategies

**Risk**: Risk management rules don't work as intended (bugs allow over-leverage)
- **Likelihood**: Low
- **Impact**: Critical (large losses in paper trading)
- **Mitigation**:
  - Unit test all risk management logic thoroughly
  - Integration test with various scenarios (insufficient capital, max allocation reached)
  - Add multiple safety checks (pre-trade validation, post-trade verification)
  - Monitor actual position sizes vs limits daily
- **Contingency**: Pause strategy immediately if rule violation detected, fix bug, resume after verification

**Risk**: Slippage and commissions make strategy unprofitable (backtest didn't model accurately)
- **Likelihood**: Medium
- **Impact**: Medium (strategy not viable)
- **Mitigation**:
  - Include conservative slippage (0.1%) and commissions in backtests
  - Track actual slippage in paper trading vs expected
  - Adjust strategy parameters if slippage consistently higher
- **Contingency**: Refine execution (limit orders instead of market), target more liquid stocks

**Risk**: Market conditions during paper trading don't match historical backtest periods
- **Likelihood**: Medium
- **Impact**: Medium (can't validate strategy across conditions)
- **Mitigation**:
  - Extend paper trading duration until experience diverse conditions
  - Run additional backtests on recent historical data
  - Compare paper trading performance to backtest expectations
- **Contingency**: Extend paper trading beyond 3 months if needed

### 11.4 Operational Risks

**Risk**: Local machine downtime (power outage, hardware failure, internet outage)
- **Likelihood**: Low to Medium
- **Impact**: Medium (missed trades, system offline)
- **Mitigation**:
  - UPS (uninterruptible power supply) for computer
  - Backup internet connection (mobile hotspot)
  - Cloud backup of critical data
  - Consider migrating to VPS after successful paper trading
- **Contingency**: Monitor uptime, accept some missed signals during MVP

**Risk**: Insufficient monitoring leads to undetected issues
- **Likelihood**: Medium
- **Impact**: Medium (bugs compound, lose trust in system)
- **Mitigation**:
  - Implement comprehensive logging
  - Email alerts for all critical events
  - Daily review of trades and system status
  - Set up simple health check dashboard
- **Contingency**: Dedicate time each evening to review logs and performance

**Risk**: Regulatory or compliance issues with automated trading
- **Likelihood**: Low
- **Impact**: Medium (may need to stop trading)
- **Mitigation**:
  - Start with paper trading only (no real money)
  - Consult IBKR's terms of service for automated trading
  - Understand PDT (Pattern Day Trading) rules if going live
  - Keep detailed trade logs for audit trail
- **Contingency**: Seek legal advice before transitioning to real money

---

## 12. Open Questions & Decisions Needed

### 12.1 Immediate Decisions (Before Week 1)

**Q1**: Which 5-10 stocks will be in the initial watchlist?
- **Recommendation**: Start with highly liquid large-cap stocks to minimize slippage
- **Suggested**: AAPL, MSFT, GOOGL, AMZN, TSLA, JPM, BAC, XOM, NVDA, META
- **Decision Needed**: Finalize watchlist by Week 1

**Q2**: Which email service will be used for notifications?
- **Options**: Gmail (SMTP), SendGrid, Mailgun, AWS SES
- **Recommendation**: Gmail SMTP for MVP (free, easy setup)
- **Decision Needed**: Set up email account and credentials by Week 13

**Q3**: Will development use Docker Compose for local services (PostgreSQL, Redis)?
- **Pros**: Consistent environment, easy setup, isolated services
- **Cons**: Additional complexity, Docker learning curve
- **Recommendation**: Use Docker Compose if comfortable, otherwise native installations
- **Decision Needed**: By Week 1

**Q4**: What initial capital will paper trading account start with?
- **Typical**: IBKR paper account default is $100,000
- **Decision**: Verify actual paper account balance, use as initial capital
- **Decision Needed**: When setting up IBKR paper account (Week 9)

### 12.2 Deferred Decisions (Can decide during development)

**Q5**: Should indicator values be stored in database or calculated on-demand?
- **Stored**: Faster queries, uses more storage
- **Calculated**: Slower, saves storage, always fresh
- **Recommendation**: Store recent 90 days, calculate historical on-demand
- **Decision Needed**: By Week 5

**Q6**: Should system use Celery or RQ for background jobs?
- **Celery**: More features, more complex setup, better for scaling
- **RQ**: Simpler, easier to use, sufficient for MVP
- **Recommendation**: RQ for MVP (simpler), migrate to Celery if scaling needed
- **Decision Needed**: By Week 2

**Q7**: Should backtesting use Backtrader or custom implementation?
- **Backtrader**: Professional-grade, realistic simulation, steeper learning curve
- **Custom**: Simpler, faster to build, less realistic
- **Recommendation**: Start with simple custom backtester, migrate to Backtrader if needed
- **Decision Needed**: By Week 7

**Q8**: When to migrate from local deployment to VPS/cloud?
- **Options**: Keep local for MVP, migrate after paper trading success, migrate before going live
- **Recommendation**: Stay local for MVP, migrate to VPS before real money trading
- **Decision Needed**: After paper trading validation (Month 5+)

### 12.3 Future Phase Decisions (Not needed for MVP)

**Q9**: How to handle multiple simultaneous strategies in Phase 2?
**Q10**: Which additional strategy types to implement in Phase 2?
**Q11**: What intraday timeframes to support in Phase 2?
**Q12**: Which notification channels to add (Slack, SMS)?
**Q13**: How to implement strategy parameter optimization?
**Q14**: What machine learning approaches to explore in Phase 3+?

---

## 13. Dependencies & Prerequisites

### 13.1 External Services Setup Required

**Twelve Data Account**:
- Sign up for free tier account
- Generate API key
- Verify rate limits (8 calls/min, 800/day)
- Test API access with sample calls
- **Deadline**: Week 1

**Interactive Brokers Account**:
- Open IBKR paper trading account
- Download and install TWS (Trader Workstation) or IB Gateway
- Configure API access (enable API connections in settings)
- Generate API credentials
- Verify API connection with ib_insync library
- **Deadline**: Week 9

**Email Service**:
- Set up email account for sending notifications (Gmail or other)
- Generate app password (if using Gmail 2FA)
- Configure SMTP settings
- **Deadline**: Week 13

### 13.2 Development Environment Setup

**Required Software**:
- Python 3.10+ (with pip, virtualenv)
- Node.js 16+ and npm (for React frontend)
- PostgreSQL 14+ (database)
- Redis 6+ (for Celery/RQ)
- Git (version control)
- Code editor (VS Code, PyCharm, etc.)

**Optional Tools**:
- Docker & Docker Compose (for containerized services)
- Postman or Insomnia (for API testing)
- pgAdmin or DBeaver (for database management)
- Redis Commander (for Redis inspection)

**System Requirements**:
- 8 GB RAM minimum (16 GB recommended)
- 50 GB free disk space
- Stable internet connection
- Compatible OS: Linux, macOS, or Windows (WSL recommended for Windows)

### 13.3 Knowledge & Skills Required

**Must Have**:
- Python programming (functions, classes, async/await)
- Basic SQL (SELECT, INSERT, UPDATE queries)
- RESTful API concepts (GET/POST/PUT requests)
- Git basics (commit, push, pull)
- Command line / terminal usage

**Good to Have**:
- React basics (components, hooks, state management)
- FastAPI or Flask experience
- PostgreSQL/SQLAlchemy ORM
- pandas for data manipulation
- Trading concepts (candlesticks, indicators, orders)

**Will Learn During Development**:
- ib_insync library for IBKR API
- pandas-ta for technical indicators
- Lightweight Charts library
- Celery/RQ for background jobs
- WebSocket communication
- Backtrader for backtesting

---

## 14. Acceptance Criteria for MVP Completion

### 14.1 Development Complete (End of Week 14)

**System Functionality**:
- ✅ Can add stocks to watchlist (up to 10)
- ✅ Historical data fetched and stored for all watchlist stocks
- ✅ Technical indicators (EMA, RSI) calculated correctly
- ✅ Strategy generates signals daily at market close
- ✅ Orders placed via IBKR paper trading account
- ✅ Stop-loss orders placed at broker level
- ✅ Risk management rules enforced (position sizing, loss limits)
- ✅ Dashboard displays real-time prices, positions, trades
- ✅ Email notifications sent for critical events
- ✅ System restarts automatically on crashes
- ✅ Crash recovery reconciles positions with broker

**Testing Complete**:
- ✅ Unit tests passing for critical components
- ✅ Integration tests passing for broker and database
- ✅ Backtest on 1 year data shows Sharpe ratio >1.0
- ✅ Backtest on 5 different stocks shows consistent results
- ✅ Crash recovery tested and working
- ✅ API failure scenarios handled gracefully

**Documentation**:
- ✅ README with setup instructions
- ✅ Configuration guide for API credentials
- ✅ User guide for dashboard and controls
- ✅ Troubleshooting guide for common issues

### 14.2 Paper Trading Validation Complete (After 3+ Months)

**Minimum Requirements**:
- ✅ 3 full months of paper trading OR 30 completed trades (whichever longer)
- ✅ At least 2 different market conditions experienced (bull/bear/sideways)
- ✅ Net positive total return (profitable)
- ✅ Sharpe ratio > 1.0
- ✅ Maximum drawdown < 25%
- ✅ Zero violations of risk management rules
- ✅ Zero critical system failures or unrecovered crashes
- ✅ All trades logged with complete data (100% data quality)

**Performance Analysis**:
- ✅ Win rate between 40-60% (strategy-dependent)
- ✅ Profit factor > 1.5
- ✅ Consistent with backtest expectations (±20%)
- ✅ Average slippage measured and acceptable (<0.3%)
- ✅ Order execution success rate > 98%

**Decision Point**:
- If all criteria met: **Proceed to real money with graduated capital allocation (25% → 50% → 100%)**
- If most criteria met but minor issues: **Extend paper trading 1-2 months, refine strategy**
- If criteria not met: **Major strategy revision or rejection, start new strategy cycle**

---

## 15. Appendices

### Appendix A: Glossary

**Terms**:
- **EMA (Exponential Moving Average)**: Trend indicator giving more weight to recent prices
- **RSI (Relative Strength Index)**: Momentum oscillator measuring overbought/oversold conditions (0-100)
- **Stop-Loss**: Order to sell position if price drops to specified level (limits losses)
- **Take-Profit**: Order to sell position if price rises to specified level (locks in gains)
- **Slippage**: Difference between expected execution price and actual fill price
- **Sharpe Ratio**: Risk-adjusted return metric (higher is better, >1.0 is good)
- **Drawdown**: Peak-to-trough decline in portfolio value (measures worst loss period)
- **Position Sizing**: Calculation determining how many shares to buy based on risk tolerance
- **Paper Trading**: Simulated trading with fake money to test strategies without risk
- **Crossover**: When one indicator line crosses above/below another (buy/sell signal)

### Appendix B: Reference Documents

- [IdeaDevelopment.md](./IdeaDevelopment.md) - Comprehensive planning document with all strategy decisions
- [TechnicalArchitecture.md](./TechnicalArchitecture.md) - Detailed technical specifications and database schema
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pandas-ta Documentation](https://github.com/twopirllc/pandas-ta)
- [ib_insync Documentation](https://ib-insync.readthedocs.io/)
- [Lightweight Charts Documentation](https://tradingview.github.io/lightweight-charts/)
- [Twelve Data API Documentation](https://twelvedata.com/docs)

### Appendix C: Risk Management Quick Reference

**2% Risk Rule**:
```
Portfolio Value = $10,000
Max Risk per Trade = $10,000 × 0.02 = $200
Entry Price = $100
Stop-Loss Price = $95
Risk per Share = $100 - $95 = $5
Position Size = $200 / $5 = 40 shares
```

**Daily Loss Limit**:
- After 3 consecutive losing trades in same day → Pause strategy
- Counter resets at start of next trading day
- Manual resume allowed, or auto-resume next day

**Portfolio Allocation Limits**:
- Max 20% of portfolio in any single position
- Max 50% of portfolio allocated to one strategy
- These are hard limits - trades rejected if exceeded

### Appendix D: Key Dates & Milestones

| Milestone                    | Target Date           | Description                              |
|------------------------------|-----------------------|------------------------------------------|
| Project Kickoff              | Week 1, Day 1         | Start development, environment setup     |
| Backend Foundation           | End of Week 2         | FastAPI, database, basic structure       |
| Market Data Integration      | End of Week 4         | Historical & real-time data working      |
| Strategy Engine              | End of Week 6         | Signal generation functional             |
| Backtesting Complete         | End of Week 8         | Validated on historical data             |
| Trading Execution            | End of Week 10        | IBKR integration & risk mgmt             |
| Dashboard Complete           | End of Week 12        | Full UI functional                       |
| System Operations            | End of Week 14        | Monitoring, notifications, stability     |
| Paper Trading Start          | Week 15               | Begin live paper trading                 |
| Paper Trading Checkpoint 1   | Week 19 (1 month)     | Review performance, check issues         |
| Paper Trading Checkpoint 2   | Week 23 (2 months)    | Analyze metrics, adjust if needed        |
| Paper Trading Complete       | Week 27+ (3 months)   | Final validation, go/no-go decision      |

---

## 16. Approval & Sign-Off

**Document Status**: Approved
**Approved By**: Khayyam Jones (Solo Developer)
**Approval Date**: 2025-01-13

**Next Steps**:
1. Review and confirm all open questions (Section 12)
2. Set up external services (Twelve Data, IBKR accounts)
3. Prepare development environment
4. Begin Week 1 development (Project Setup & Infrastructure)

**Contact**:
- For questions or clarifications: Review IdeaDevelopment.md and TechnicalArchitecture.md
- For scope changes: Update this PRD document and track in version control

---

**END OF PRD**
