# Trading App - Idea Development

## Project Overview

Autonomous trading application with real-time market data, multiple trading strategies, and comprehensive UI for monitoring and analysis.

## Core Requirements

### Trading Functionality

- [ ] Autonomous trading execution
- [ ] Multiple simultaneous trading strategies
- [ ] API integration for market data (Twelve Data, IBKR)
- [ ] API integration for trade execution (IBKR, TradingView)
- [ ] Stop-loss and profit-taking order management
- [ ] Dynamic order updates based on market conditions
- [ ] Paper trading support for strategy testing

### Data & Analysis

- [ ] Real-time stock price data
- [ ] Technical indicators (Moving Averages, MACD, etc.)
- [ ] Trend line calculations
- [ ] Volume analysis
- [ ] Historical data storage
- [ ] Strategy performance tracking

### User Interface

- [ ] Main candlestick chart with indicator overlays
- [ ] Volume chart (synchronized timeline)
- [ ] MACD histogram chart (synchronized timeline)
- [ ] Strategy buy/sell markers on main chart
- [ ] Stock symbol navigation/selection
- [ ] Investment status and summaries
- [ ] Strategy selection and configuration
- [ ] Real-time updates

### Database/Tracking

- [ ] Trade execution history
- [ ] Strategy performance metrics
- [ ] Stock price history
- [ ] Order history (placed, filled, cancelled)
- [ ] Profit/Loss calculations by strategy
- [ ] Time-series data for analysis

## Project Organization Principles

- Group related functionality (indicators, data fetching, strategies, display)
- Keep components simple and focused
- Maximize code reuse
- Separate concerns (data logic, UI logic, trading logic)

## Decisions Made

### Timeframe Strategy

**Decision**: Build support for all three timeframes (intraday, swing, long-term) but implement incrementally

- **Phase 1**: Start with ONE timeframe and ONE strategy
- **Phase 2**: Add additional strategies for same timeframe
- **Phase 3**: Expand to other timeframes

**Recommended starting timeframe**: Daily/Swing Trading

- Less data storage requirements (daily bars vs 1-min bars)
- Lower API rate limit pressure
- Easier to monitor/debug (fewer signals per day)
- More forgiving execution timing
- Still meaningful for learning and testing
- Can run during non-market hours

**Architecture consideration**: Design data models and services to support multiple timeframes from the start, even if only implementing one initially.

### Machine Learning Approach

**Decision**: NO machine learning in MVP. Focus on rule-based strategies with comprehensive analytics.

**MVP Approach (Rule-Based Strategies)**:

- Implement clear, logical trading rules
- Store ALL trade data and performance metrics
- Build analysis tools to identify patterns in wins/losses
- Manually refine strategies based on insights
- Use simple adaptive logic (e.g., adjust position size based on volatility)

**Why no ML in MVP**:

- ML in trading is extremely prone to overfitting
- Requires massive amounts of quality data
- Very difficult to validate if it actually works
- Black box models are hard to trust with real money
- Simple strategies often outperform complex ML models
- Need baseline performance from simple strategies first

**Future ML Possibilities (Phase 4+)**:

- Market regime detection (clustering to identify bull/bear/sideways markets)
- Feature importance analysis (identify which indicators matter most)
- Anomaly detection (pause trading during unusual market conditions)
- Parameter optimization (find optimal indicator settings)

**Key Principle**: Understand why simple strategies work/fail before attempting ML. Most successful traders use rule-based systems, not ML.

### Risk Management Rules

**Decision**: Establish clear risk management rules to protect capital and prevent catastrophic losses.

**Daily Loss Limits**:
- **Rule**: Each strategy stops trading after 3 consecutive losses in a single day
- **Rationale**: Prevents strategy from continuing when market conditions don't match its logic
- **Implementation**: Track consecutive losses per strategy per day, pause strategy until next trading day
- **Reset**: Counter resets at start of each trading day

**Position Sizing**:
- **Recommendation**: Use **2% rule** as starting point
- **Definition**: Risk no more than 2% of total portfolio value on any single trade
- **Calculation**:
  ```
  Risk per trade = Portfolio Value × 0.02
  Position Size = Risk Amount ÷ (Entry Price - Stop Loss Price)
  ```
- **Example**:
  - Portfolio: $10,000
  - Max risk per trade: $200 (2%)
  - Entry price: $100
  - Stop loss: $95
  - Risk per share: $5
  - Position size: $200 ÷ $5 = 40 shares
- **Alternative (Phase 2)**: ATR-based position sizing
  - Adjusts position size based on stock volatility
  - More volatile stocks = smaller positions
  - Less volatile stocks = larger positions
  - Formula: `Position Size = (Portfolio × Risk%) ÷ (ATR × ATR Multiplier)`

**Maximum Position Size**:
- **Recommendation**: Cap at **20% of portfolio value per position**
- **Rationale**: Prevents over-concentration in single position
- **Example**: $10,000 portfolio → max $2,000 in any single position
- **Note**: This is a position value cap, separate from the 2% risk rule

**Maximum Portfolio Allocation per Strategy**:
- **Recommendation**: **50% of portfolio per strategy for MVP**
- **Rationale**:
  - Starting with 1-2 strategies in MVP
  - Allows testing multiple strategies without overlap issues
  - Prevents single strategy from controlling entire portfolio
- **Future**: As more strategies are added, reduce to 30-40% per strategy

**Maximum Concurrent Positions**:
- **Decision**: No hard limit (unlimited)
- **Rationale**: Let portfolio allocation and position sizing rules naturally limit exposure
- **Safeguard**: Portfolio allocation caps and position sizing rules provide sufficient protection
- **Monitor**: Track total portfolio utilization (avoid over-leveraging cash)

**Stop-Loss Gap Handling**:
- **Decision**: Execute sell immediately at market price when stop-loss gaps through
- **Rationale**: Get out of position quickly to limit further losses
- **Implementation**:
  - If stop-loss triggers but price gaps beyond stop level
  - Execute market order immediately
  - Accept slippage beyond intended stop price
  - Log actual loss vs intended loss for analysis
- **Tracking**: Record gap events to identify if strategy needs adjustment

**Risk Management Database Tracking**:
Store in `trades` table:
- Intended stop-loss price
- Actual stop-loss execution price
- Gap amount (if any)
- Position size calculation method
- Risk percentage used
- Portfolio utilization at trade entry

**Risk Alerts**:
- Alert when approaching daily loss limit (after 2nd loss)
- Alert when portfolio utilization exceeds 80%
- Alert when single position exceeds size cap
- Alert on stop-loss gap execution

**Key Principle**: Risk management is more important than profit optimization. Preserving capital allows you to keep trading and learning.

### Strategy Design Approach

**Decision**: Focus on technical indicators with capability to incorporate fundamental data, news, and sentiment.

**Data Sources**:
- **Primary**: Technical indicators (price and volume patterns)
- **Secondary**: Fundamental data (P/E ratios, earnings, revenue growth)
- **Secondary**: Market sentiment (fear/greed index, social media sentiment)
- **Secondary**: News events (earnings announcements, FDA approvals, etc.)
- **Rationale**: Technical indicators provide immediate, quantifiable signals. Fundamental and sentiment data can enhance strategy but add complexity.

**First Strategy (MVP)**:
- **Recommendation**: **Moving Average Crossover with RSI Confirmation**
- **Why this strategy**:
  - Simple and well-understood
  - Easy to debug and validate
  - Clear entry/exit rules
  - Good baseline for learning
  - Proven pattern (though not always profitable)
- **Logic**:
  - Buy signal: Fast MA crosses above slow MA AND RSI is not overbought (< 70)
  - Sell signal: Fast MA crosses below slow MA OR RSI becomes overbought (> 70)
  - Example: 20-day EMA crosses 50-day EMA with RSI(14) confirmation
- **Alternative considerations**:
  - RSI + MACD Mean Reversion (buy oversold, sell overbought)
  - Bollinger Band Breakout (buy when price breaks upper band on volume)
  - Momentum Breakout (buy on new highs with volume confirmation)

**Indicator Count per Strategy**:
- **Recommendation**: **2-4 indicators per strategy**
- **Rationale**:
  - 2-3 indicators: Sweet spot for MVP - enough to create robust signals, simple enough to understand
  - 4-5 indicators: Maximum before strategy becomes too complex to debug
  - 1 indicator: Usually not enough confirmation (too many false signals)
  - 6+ indicators: Over-optimization risk, hard to maintain, unclear which indicators matter
- **Starting point**: Use 2-3 indicators (e.g., 2 moving averages + RSI)
- **Phase 2**: Experiment with 4 indicators after validating simpler strategies

**Long vs Short Positions**:
- **Phase 1 (MVP)**: **Long positions only**
- **Rationale**:
  - Simpler risk management (limited downside = 100%, upside unlimited)
  - Most stocks trend upward over time (market bias)
  - Easier to understand and debug
  - No margin requirements for paper trading
  - Lower psychological stress
- **Phase 2**: Add short capability after mastering long positions
- **Short strategy considerations**:
  - Requires margin account
  - Unlimited downside risk (stock can rise infinitely)
  - Different indicators may be needed (downtrends behave differently)
  - Higher borrowing costs
  - More complex position sizing

**Strategy Architecture**:
- Design system to support multiple data types from day 1
- Implement strategies as configurable rules (stored in database)
- Allow strategies to combine multiple signal types (technical + fundamental + sentiment)
- Each strategy specifies which indicators and data sources it uses
- Easy to A/B test different combinations

**Key Principle**: Start simple with technical indicators and proven patterns. Add complexity only after validating the basics work.

### Capital Management

**Decision**: Use a single shared capital pool with dynamic allocation across strategies.

**Capital Pool Structure**:
- **Single Pool**: All strategies draw from one shared capital pool
- **Rationale**:
  - Simpler to manage and understand
  - Maximizes capital efficiency (no idle capital locked per strategy)
  - Easier to rebalance based on strategy performance
  - Reduces complexity for MVP
- **Future**: Could split into separate pools if strategies have vastly different risk profiles

**Dynamic Capital Allocation**:
- **Decision**: Yes, strategies share capital dynamically
- **Implementation**:
  - Strategies request capital for trades based on position sizing rules
  - Available capital = Total pool - Currently allocated positions
  - If insufficient capital, trade request is queued or rejected
- **Benefits**:
  - Better-performing strategies naturally get more opportunities
  - Underperforming strategies are naturally constrained
  - Capital efficiency maximized

**Capital Allocation Limits**:
- Each strategy still subject to 50% portfolio allocation cap
- Position sizing rules (2% risk, 20% position cap) apply per trade
- If Strategy A uses 40% and Strategy B wants 30%, both can execute
- If Strategy A uses 60% (over limit), additional trades blocked until positions close

**Margin and Leverage**:
- **Phase 1 (MVP)**: No margin or leverage
- **Rationale**:
  - Keep risk simple and contained
  - Easier to understand true performance
  - No interest costs or margin calls
  - Paper trading usually doesn't require margin
- **Phase 2+**: Enable margin/leverage as an option
  - Requirement: Proven profitable strategies without leverage first
  - Conservative leverage (2x maximum)
  - Clear margin requirements and liquidation rules
  - Enhanced risk management (lower position sizes with leverage)

**Initial Capital Allocation**:
- **Amount**: Paper trading account default allocation
- **Typical**: $100,000 for IBKR paper trading accounts
- **Verification**: Check actual paper account balance at setup
- **Tracking**: Record initial capital in database for performance calculations

**Capital Tracking**:
- Track total portfolio value daily
- Track capital allocated per strategy
- Track cash vs invested capital
- Monitor capital utilization percentage
- Alert if approaching full utilization (>90%)

**Example Scenario** (Starting with $100,000):
```
Strategy A wants to buy: $8,000 position
Strategy B wants to buy: $6,000 position
Available capital: $100,000
Result: Both trades execute, $86,000 cash remaining

Later, Strategy A wants another $15,000 position
Strategy A current allocation: $8,000
Strategy A limit: $50,000 (50% of $100k)
Result: Trade executes, Strategy A now at $23,000 (46%)

If Strategy B wants $30,000 more:
Strategy B limit: $50,000
Strategy B current: $6,000
Request: $30,000
Result: Trade executes, Strategy B now at $36,000 (72% - over limit!)
Solution: System rejects or scales down to $44,000 max position
```

**Key Principle**: Start with simple capital management. Add complexity (separate pools, leverage) only after proving strategies work with basic setup.

### Monitoring & Notifications

**Decision**: Implement multi-channel tiered notification system with both real-time dashboard and periodic reports.

**Notification Channels**:

**Email (Primary - Phase 1)**:
- Trade confirmations (entry/exit)
- Daily summary at market close
- Strategy performance reports
- System health alerts
- Easy to implement, provides audit trail

**Slack (Secondary - Phase 1 or 2)**:
- Real-time trade notifications
- System health checks
- Warning messages
- Good for monitoring during market hours

**SMS (Critical Only - Phase 2)**:
- System crashes
- API connection failures
- Daily loss limit hit
- Reserve for urgent issues only to avoid alert fatigue

**In-App Notifications (Phase 1)**:
- Dashboard alerts/toasts
- Real-time updates in UI
- Trade execution status

**Alert Severity Levels**:

**INFO Level** (Email/Slack):
- Trade executed (entry/exit)
- Signal generated but not executed (with reason)
- Daily performance summary
- Strategy statistics updates

**WARNING Level** (Email/Slack/Dashboard):
- Approaching daily loss limit (after 2nd loss)
- Portfolio utilization > 80%
- Stop-loss gap execution (slippage detected)
- Single position exceeds size cap
- Order partially filled
- Indicator calculation delays

**ERROR Level** (Email/Slack/SMS):
- Order execution failed
- API rate limit exceeded
- Daily loss limit hit (strategy paused)
- Data feed interruption > 5 minutes
- Invalid strategy configuration

**CRITICAL Level** (SMS/Email/Slack):
- System crash/restart
- API connection lost > 10 minutes
- Database connection failure
- Unhandled exceptions
- Broker account issues

**Crash Recovery & Trade Safety**:

**State Persistence**:
- Save all active positions to database in real-time
- Store all pending orders with timestamps
- Track strategy state (consecutive losses, paused status)
- Record last processed bar/timestamp

**Recovery Process** (On restart after crash):
1. Load last known state from database
2. Reconcile with broker (query actual positions via API)
3. Identify discrepancies (database vs broker reality)
4. Log recovery event with full details
5. Send alert to user about recovery status
6. Resume monitoring mode (don't auto-trade immediately)
7. Require manual approval to resume automated trading

**Broker-Level Safety** (Critical):
- **Always place stop-loss orders at broker level**, not just in-app tracking
- If app crashes, broker still executes stop-loss automatically
- This is the primary safety net against catastrophic losses
- Update broker stop-loss if strategy adjusts it

**Immediate Crash Alerts**:
- SMS + Email on crash detection
- Include: crash time, active positions, pending orders, portfolio value
- Provide instructions for manual intervention if needed

**Manual Intervention Options**:
- Web UI to view current state and manually close positions
- Direct broker platform access for emergency management
- Recovery mode: view-only until user reviews and approves resume

**Monitoring Dashboards**:

**Real-Time Dashboard** (Web UI with WebSocket updates):
- **Purpose**: Active monitoring during market hours
- **Update Frequency**: Every 1-5 seconds for prices, instant for trade events
- **Content**:
  - Current open positions with live P&L
  - Active buy/sell signals
  - Recent trades (last 10)
  - Portfolio value chart (intraday)
  - Strategy status (active/paused/error)
  - System health indicators (API status, database, workers)
  - Current indicator values for tracked stocks
  - Cash available vs allocated
- **Primary User**: You, during market hours or periodic check-ins

**Periodic Reports**:

**Daily Report** (End of trading day - Email/PDF):
- Trades executed today (entries and exits)
- Daily P&L by strategy
- Portfolio value change ($  and %)
- Win rate for the day
- Any alerts or issues encountered
- Tomorrow's watchlist (stocks near signals)

**Weekly Report** (Sunday evening - Email/PDF):
- Weekly performance summary
- Strategy comparison (which performed best)
- Best and worst trades of the week
- Performance metrics (Sharpe ratio, max drawdown)
- Equity curve chart
- Upcoming week outlook

**Monthly Report** (First of month - Email/PDF):
- Comprehensive performance analysis
- Month-over-month comparison
- Strategy effectiveness review
- Trade quality analysis (wins vs losses patterns)
- Suggestions for optimization
- Year-to-date performance

**Dashboard vs Reports Usage**:
| Need | Real-Time Dashboard | Periodic Report |
|------|---------------------|-----------------|
| Quick check during day | ✓ | |
| Historical analysis | | ✓ |
| Identify issues immediately | ✓ | |
| Deep performance review | | ✓ |
| Share with others | | ✓ |
| Monitor multiple strategies | ✓ | |

**Implementation Priority**:
- **Phase 1 MVP**: Email notifications + Real-time dashboard + Daily reports
- **Phase 2**: Add Slack integration + Weekly reports
- **Phase 3**: Add SMS for critical alerts + Monthly reports + Mobile app

**Key Principle**: Dashboard for "what's happening now", reports for "how are we doing overall". Prevent alert fatigue by tiering severity appropriately.

### Data & Indicators Management

**Decision**: Maintain 1 year of historical data with timeframe-based indicator updates and intelligent warm-up handling.

**Historical Data Range**:
- **Storage**: 1 year of historical OHLCV data
- **Rationale**:
  - Sufficient for backtesting most strategies
  - Captures multiple market cycles (bull, bear, sideways)
  - Includes seasonal patterns
  - Reasonable storage size
  - Can extend later if needed
- **Initial Load**: Download 1 year of data for each tracked stock on first setup
- **Ongoing**: Append new bars as they complete

**Indicator Update Frequency**:
- **Rule**: Indicators update with each completed time period bar
- **Examples**:
  - Daily chart: Update indicators once per day at market close
  - 5-minute chart: Update indicators every 5 minutes when bar completes
  - 1-hour chart: Update indicators every hour when bar completes
- **Rationale**:
  - Prevents look-ahead bias (only use completed bars)
  - Matches how indicators behave in real trading
  - Consistent with strategy evaluation timing
- **Implementation**:
  - Primary timeframe (MVP): Daily bars, update at end of day
  - Real-time data: Stream prices but only update indicators at bar close
  - No intra-bar indicator updates (prevents false signals)

**Indicator Warm-Up Period Handling**:

**Problem**: Indicators need historical data before generating valid signals
- Example: 50-day EMA requires 50 days of data to be accurate
- 200-day SMA requires 200 days before it's meaningful

**Recommendation**: Automatic warm-up with clear status indication

**Warm-Up Process**:
1. On strategy start, identify longest indicator period needed
   - Example: Strategy uses EMA(20), EMA(50), RSI(14)
   - Longest period: 50 days
   - Recommended warm-up: 50 days minimum
2. Load historical data to cover warm-up period
3. Calculate indicators on historical data
4. Mark strategy as "warming up" until sufficient data available
5. Generate signals only after warm-up completes

**Warm-Up Requirements by Indicator**:
- Moving averages (SMA/EMA): Period length (e.g., 50-day = 50 bars)
- RSI: 2x period length for stability (e.g., RSI(14) = 28 bars)
- MACD: Slow period + signal period (e.g., 26 + 9 = 35 bars)
- Bollinger Bands: Period length (e.g., 20-day = 20 bars)
- General rule: **Use 2x the longest period** to ensure stability

**Strategy Warm-Up Example** (EMA Crossover with RSI):
- EMA(20), EMA(50), RSI(14)
- Longest period: 50
- Recommended warm-up: 100 bars (2x longest)
- On day 101, strategy begins generating signals

**UI Indication**:
- Strategy status: "Warming up (45/100 bars)"
- Progress bar showing warm-up completion
- Disable trading during warm-up
- Show indicator values but mark as "preliminary"

**Data Retention Policy**:

**Trade Data** (Keep Forever):
- All executed trades with full details
- Entry/exit prices, timestamps, reasons
- P&L, commissions, slippage
- Position sizes, risk calculations
- Trade-level performance metrics
- **Rationale**: Core business data, essential for analysis and tax reporting

**Trade Signals** (Keep Forever):
- All generated signals (executed and not executed)
- Signal reasons and market context
- Why signals weren't executed
- **Rationale**: Critical for strategy improvement and learning

**Strategy Events** (Keep Forever):
- Errors, warnings, state changes
- Daily loss limits hit, pauses
- Configuration changes
- **Rationale**: Audit trail for understanding strategy behavior

**Market Data - OHLCV** (Rolling retention):
- **Active Period**: Keep 1 year of daily bars
- **Archive**: Move data older than 1 year to cold storage
- **Purge**: Delete data older than 3 years (optional)
- **Rationale**: Balance between backtest capability and storage costs
- **Exception**: Can keep more if storage is cheap

**Calculated Indicators** (Short retention):
- **Active**: Keep 90 days of calculated indicator values
- **Rationale**: Can be recalculated from OHLCV data anytime
- **Benefit**: Reduces database size
- **Exception**: Keep indicator values at trade entry/exit times forever (stored in trade record)

**System Logs** (Tiered retention):
- **Hot Storage**: Last 30 days (full logs, fast access)
- **Cold Storage**: 31-90 days (compressed, slower access)
- **Archive**: 91-365 days (compressed, archival storage)
- **Purge**: Delete after 1 year
- **Exception**: Keep ERROR and CRITICAL logs for 2 years

**Application Logs**:
- DEBUG: 7 days
- INFO: 30 days
- WARNING: 90 days
- ERROR: 1 year
- CRITICAL: 2 years

**Portfolio Snapshots** (Daily):
- Keep daily portfolio value snapshots indefinitely
- Required for equity curve and performance tracking
- Minimal storage (one row per day)

**Backtest Results**:
- Keep all backtest runs indefinitely
- Includes parameters tested and results
- Essential for tracking strategy evolution

**Database Maintenance**:
- Weekly: Archive old logs
- Monthly: Compress old market data
- Quarterly: Review retention policies
- Annually: Purge data per retention rules

**Storage Estimates** (for planning):
- 1 stock, 1 year, daily data: ~1 KB (260 rows)
- 100 stocks, 1 year: ~100 KB
- Trade records: ~1 KB per trade
- 1000 trades: ~1 MB
- Logs: ~10-100 MB per month (varies by activity)

**Key Principle**: Keep all trading/business data forever (it's your history). Market data and logs can be pruned based on utility vs storage cost.

### Testing & Validation

**Decision**: Rigorous multi-phase testing with clear success criteria before risking real capital.

**Paper Trading Duration**:

**Dual Criteria** (Both must be met):
- **Minimum Time**: 3 months of paper trading
- **Minimum Trades**: 30 completed trades (entries and exits)

**Rationale**:
- 3 months captures different market conditions (trending, ranging, volatile)
- 30 trades provides statistical significance (enough sample size)
- Both criteria prevent premature launch (time diversity + sample size)

**Application**:
- If 30 trades in 2 months → still wait full 3 months
- If only 15 trades after 3 months → wait until 30 trades
- Ensures both time diversity and adequate sampling

**Additional Requirements Before Going Live**:
- Strategy must be net profitable (positive P&L)
- Maximum drawdown must be acceptable (< 25%)
- No critical bugs or order execution failures
- All risk management rules functioning correctly
- Broker integration working reliably

**Warning Signs to Extend Testing**:
- Inconsistent performance (wild swings month to month)
- Strategy hasn't experienced a losing streak yet
- Only tested in one market condition (all bull or all bear)
- Suspicious win rate (> 80% might indicate curve fitting)
- Recent performance degrading

**Graduated Capital Allocation** (Going Live):
- **Month 4**: Start with 25% of intended capital
- **Month 5**: Increase to 50% if performing well
- **Month 6+**: Full capital allocation if consistently profitable

**Strategy Success Metrics**:

**Required Metrics** (All must pass):

**Profitability**:
- **Total Return**: Must be positive (making money)
- **Risk-Adjusted Return (Sharpe Ratio)**: > 1.0 minimum
  - Sharpe < 1.0: Risk not worth the return (reject)
  - Sharpe 1.0-1.5: Acceptable risk/reward
  - Sharpe 1.5-2.0: Good strategy
  - Sharpe > 2.0: Excellent strategy
- **Return vs Benchmark**: Ideally beat SPY, acceptable if close

**Win Rate** (Strategy-dependent):
- **Trend-Following**: 40-50% acceptable (larger wins compensate)
- **Mean Reversion**: 55-65% expected (smaller wins, more frequent)
- **Below 35%**: Usually unsustainable (reject)
- **Above 70%**: Investigate for over-optimization

**Risk Management**:
- **Maximum Drawdown**: < 25% acceptable, < 15% good, < 10% excellent
  - Above 25%: Too risky for most traders
- **Consecutive Losses**: Should recover after max 5 losing trades
- **Average Win/Loss Ratio**: > 1.5 for trend-following, > 1.0 for mean reversion

**Trade Quality**:
- **Profit Factor**: (Gross Profit ÷ Gross Loss) > 1.5 minimum
  - 1.0-1.5: Marginal
  - 1.5-2.0: Good
  - 2.0+: Very good
- **Average Trade P&L**: Positive after commissions and slippage
- **Expectancy**: (Win Rate × Avg Win) - (Loss Rate × Avg Loss) > 0

**Consistency**:
- **Positive Months**: At least 60% of months should be profitable
- **Signal Generation**: Should generate signals regularly (not too conservative)
- **No Extended Flat Periods**: Strategy actively trading

**Auto-Reject Criteria** (Any one fails strategy):
- Any single trade loses > 10% of portfolio (risk management failure)
- More than 3 consecutive days hitting daily loss limit
- Frequent order execution errors (> 5% failure rate)
- Strategy performance degrading over time (negative trend)
- Sharpe ratio < 1.0 or Profit factor < 1.5

**Success Criteria Checklist**:
```
Required (Must Pass All):
✓ Positive total return
✓ Sharpe ratio > 1.0
✓ Max drawdown < 25%
✓ Profit factor > 1.5
✓ Win rate within expected range (40-65% depending on type)
✓ No catastrophic single losses (> 10% portfolio)
✓ Consistent signal generation

Bonus (Nice to Have):
• Beats SPY benchmark
• Sharpe ratio > 1.5
• Max drawdown < 15%
• 60%+ months profitable
• Profit factor > 2.0
```

**Testing Across Market Conditions**:

**Market Regime Definitions**:
- **Bull Market**: Trending up, higher highs and higher lows, positive sentiment
- **Bear Market**: Trending down, lower highs and lower lows, negative sentiment
- **Sideways Market**: Range-bound, choppy, no clear direction, low volatility

**Multi-Phase Testing Approach**:

**Phase 1: Historical Backtesting** (Before paper trading):

**Full Period Test**:
- Run backtest on entire 1-year historical dataset
- Get overall performance baseline
- Identify if strategy is fundamentally viable

**Segmented Testing**:
- Break 1-year into quarters (Q1, Q2, Q3, Q4)
- Test each quarter separately
- Compare performance across segments
- Identify which periods perform best/worst

**Market Regime Analysis**:
- Identify bull/bear/sideways periods in historical data
- Measure performance in each regime
- Ensure strategy profitable (or break-even) in at least 2 of 3 regimes
- Document which conditions favor the strategy

**Out-of-Sample Testing**:
- Train/optimize on first 6 months
- Test on last 6 months (never seen before)
- If performs similarly, good sign of robustness
- If performance diverges significantly, over-optimization risk

**Phase 2: Paper Trading Validation** (Real-time testing):
- Must experience at least 2 different market conditions during 3-month period
- If market only bullish during paper trading, extend until bear/sideways occurs
- Track which conditions strategy performs best/worst in
- Compare paper trading results to backtest expectations

**Phase 3: Robustness Checks**:

**Parameter Sensitivity Testing**:
- Change indicator periods by ±20%
  - Example: EMA(20) → test EMA(16) and EMA(24)
  - Example: RSI(14) → test RSI(11) and RSI(17)
- If strategy fails with small changes, it's over-optimized
- Robust strategies work across a range of parameters
- Performance should degrade gracefully, not collapse

**Multiple Stock Testing**:
- Don't optimize on one stock only
- Test on at least 5-10 different stocks across sectors
- Mix market caps: large-cap, mid-cap
- Mix sectors: tech, finance, consumer, healthcare, energy
- Strategy should work across multiple assets with similar results
- Acceptable if some stocks underperform, but most should be profitable

**Volatility Testing**:
- Test during high volatility periods (VIX > 20)
- Test during low volatility periods (VIX < 15)
- Strategy should handle both without breaking
- May have reduced performance in one regime but shouldn't blow up

**Market Event Testing**:
- Include periods with: Earnings announcements, Fed meetings, market crashes
- Strategy should survive unusual events
- Stop-losses should protect capital during extreme moves
- Acceptable to sit out (no trades) during extreme conditions

**Robustness Scoring Checklist**:
```
Strategy is robust if:
✓ Profitable in both bull AND bear markets (maybe reduced profit, but still positive)
✓ Works on 5+ different stocks with similar characteristics
✓ Small parameter changes (±20%) don't drastically change results
✓ Survives high volatility (VIX > 20) without catastrophic loss
✓ Consistent profit factor across different time periods
✓ Out-of-sample performance similar to in-sample
✓ No single stock, time period, or condition responsible for all profits
```

**Warning Signs of Fragile Strategy**:
- Only profitable in one specific market condition
- Only works on one or two stocks
- Highly sensitive to exact parameter values
- Can't handle volatility spikes (VIX > 25)
- Performance degrades quickly over time
- Backtest great but paper trading poor

**Practical Testing Timeline**:

**Week 1-2: Initial Backtest**:
- Full 1-year historical backtest
- Evaluate against success metrics
- If fails, adjust strategy and repeat
- If passes, proceed to deeper testing

**Week 3-4: Robustness Testing**:
- Segment analysis (quarters)
- Market regime analysis
- Multiple stock testing (5-10 stocks)
- Parameter sensitivity analysis
- Out-of-sample validation

**Weeks 5-6: Review & Refinement**:
- Analyze all backtest results
- Identify weaknesses
- Make adjustments if needed
- Finalize strategy parameters

**Months 2-4: Paper Trading**:
- Live paper trading with full position sizes
- Real-time monitoring and logging
- Compare live results to backtest expectations
- Track which market conditions occur
- Document any discrepancies

**Month 5: Comprehensive Evaluation**:
- Review all 3 months of paper trading
- Check if enough market diversity experienced
- Evaluate all success metrics
- Decision: Go live, extend testing, or reject strategy

**If extending testing**:
- Wait for missing market conditions
- Or conduct additional historical backtests for those conditions
- Don't go live without confidence in multiple regimes

**Key Principles**:
- A robust strategy makes money consistently across different conditions
- Better to have moderate returns in all conditions than great returns in one and losses in others
- Over-optimization is a bigger danger than under-optimization
- If it seems too good to be true in backtest, it probably is
- Real trading will always be slightly worse than paper trading

### Operations & Deployment

**Decision**: Phased deployment starting local, with robust restart mechanisms and comprehensive security.

**Deployment Environment**:

**Phase 1 (MVP - Paper Trading): Local Machine**
- **Decision**: Run on local development machine during MVP
- **Pros**:
  - Free (no hosting costs)
  - Easy to develop and debug
  - Direct access to logs and database
  - No latency concerns
  - Can easily restart and modify code
- **Cons**:
  - Must keep computer running during market hours
  - No redundancy if computer crashes
  - Home internet reliability dependency
  - Manual monitoring required
- **Requirements**:
  - Stable internet connection
  - Keep machine running 9:30 AM - 4:00 PM ET (market hours)
  - Or schedule to run end-of-day for daily bar strategies
  - Backup power (UPS) recommended

**Phase 2 (After MVP Success): Cloud/VPS**
- **Decision**: Migrate to VPS after successful paper trading
- **Recommended Provider**: DigitalOcean, Linode, or Vultr
- **Specs**: 2 GB RAM, 1 vCPU, 50 GB SSD ($10-20/month)
- **Benefits**:
  - 24/7 uptime guarantee
  - Professional data center reliability
  - Easy backups and snapshots
  - SSH access for debugging
  - Full environment control
- **Alternative**: AWS/GCP if expecting significant scaling

**When to Migrate to Cloud**:
- After 3 months successful paper trading
- Before switching to real money trading
- When you want 24/7 automated operation
- If local machine becomes unreliable

**Automatic Restart on Crashes**:

**Multi-Layer Restart Strategy**:

**Layer 1: Process Manager (Primary)**

**For Local Machine & VPS: systemd**
```ini
# /etc/systemd/system/trading-bot.service
[Unit]
Description=Trading Bot Application
After=network.target postgresql.service

[Service]
Type=simple
User=tradingbot
WorkingDirectory=/home/tradingbot/trading-app
ExecStart=/usr/bin/python3 backend/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/trading-bot/output.log
StandardError=append:/var/log/trading-bot/error.log

# Restart limits (prevents infinite crash loops)
StartLimitInterval=600
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
```

**Benefits**:
- Automatic restart on crash (after 10 second delay)
- Restart limits: Max 5 restarts in 10 minutes
- Prevents infinite crash loops
- Starts automatically on system boot
- Captures stdout/stderr to log files

**Docker Alternative** (Phase 2):
```yaml
# docker-compose.yml
services:
  trading-app:
    image: trading-bot:latest
    restart: unless-stopped
    deploy:
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 5
        window: 600s
```

**Layer 2: Health Checks & Monitoring**

**Health Check Endpoint**:
```python
# backend/app/api/endpoints/health.py
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": await check_database(),
        "broker_api": await check_broker_connection(),
        "workers": await check_celery_workers()
    }
```

**External Monitoring** (Phase 2):
- **UptimeRobot** (free): Pings health endpoint every 5 minutes
- If no response → sends alert
- Can trigger external restart via webhook

**Layer 3: Application-Level Crash Handling**

**Graceful Error Handling**:
```python
# backend/main.py
def main():
    try:
        app.run()
    except Exception as e:
        error_msg = traceback.format_exc()
        logger.critical(f"Application crashed: {error_msg}")

        # Send alert with trading context
        send_critical_alert(
            title="Trading Bot Crashed",
            message=error_msg,
            context={
                "active_positions": get_active_positions(),
                "pending_orders": get_pending_orders(),
                "timestamp": datetime.now()
            }
        )

        # Exit with error code (systemd will restart)
        sys.exit(1)
```

**Crash Prevention Strategies**:
- Wrap all critical sections in try/except
- Log errors but don't crash on non-critical failures
- Use circuit breakers for external API calls
- Implement rate limiting to prevent API bans
- Validate all data before processing

**Restart Notifications**:
- Always send SMS/Email on restart
- Include: crash reason, time, active positions, last action taken

**Trade State Recovery After System Failure**:

**State Persistence Strategy**:

**What to Persist** (Real-time to database):
- All active positions (symbol, entry price, quantity, timestamps)
- All pending orders (order IDs, prices, quantities, types)
- Strategy state (consecutive losses, paused/active status)
- Last processed timestamp/bar
- Capital allocation per strategy
- Portfolio value snapshots

**Database Schema for Recovery**:
```sql
-- System state tracking
CREATE TABLE system_state (
    id SERIAL PRIMARY KEY,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    last_bar_processed TIMESTAMP,
    system_status VARCHAR(20), -- 'running', 'crashed', 'recovering'
    active_positions_count INTEGER,
    total_portfolio_value DECIMAL(12,2),
    metadata JSONB
);

-- Recovery event log
CREATE TABLE recovery_events (
    id SERIAL PRIMARY KEY,
    recovery_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    crash_timestamp TIMESTAMP,
    recovery_status VARCHAR(20), -- 'started', 'success', 'failed'
    discrepancies JSONB,
    actions_taken JSONB,
    manual_intervention_required BOOLEAN DEFAULT false
);
```

**7-Step Recovery Process**:

**Step 1: Detect Recovery Scenario**
- Check if system_status = 'running' but last_updated > 5 minutes ago
- Indicates unclean shutdown (crash)

**Step 2: Load Last Known State**
- Query database for active positions
- Query database for pending orders
- Query database for strategy states
- Query database for last processed bar

**Step 3: Reconcile with Broker**
- Call broker API to get current positions
- Call broker API to get open orders
- Compare database state vs broker reality
- Identify discrepancies:
  - Missing positions (in DB but not at broker)
  - Extra positions (at broker but not in DB)
  - Missing orders
  - Price/quantity differences

**Step 4: Resolve Discrepancies**
- **Trust broker as source of truth** for positions
- If broker has extra positions → add to database, log warning
- If database has positions broker doesn't → mark as closed during crash
- If orders missing → query broker for status (filled/cancelled)
- Update database to match broker reality

**Step 5: Sync Database State**
- Update all positions to match broker
- Update all orders to match broker
- Update portfolio value from broker account info
- Record reconciliation in recovery_events table

**Step 6: Alert User**
```
Trading Bot Recovery Report

Crash detected at: [timestamp]
Recovery completed at: [timestamp]

Discrepancies Found:
- Missing positions: 0
- Extra positions: 1 (AAPL - 10 shares)
- Order status updates: 2

Current State:
- Active positions: 2
- Portfolio value: $102,450
- All strategies: PAUSED (awaiting approval)

Action Required: Review and approve resuming automated trading
Dashboard: http://localhost:3000/recovery
```

**Step 7: Enter Recovery Mode**
- Pause all strategies (no new trades)
- Set system_status = 'recovery_mode'
- Enable monitoring only (prices update, no trading)
- Wait for manual approval to resume

**Automated Recovery Decision Tree**:
```
No discrepancies found?
  → Auto-resume after 30 seconds
  → Send INFO notification

Minor discrepancies (< $100 difference)?
  → Auto-fix and resume
  → Send WARNING notification

Major discrepancies (> $100 or missing positions)?
  → Pause and require manual approval
  → Send CRITICAL notification with details
```

**Recovery Mode UI**:
- Display recovery dashboard with all discrepancies
- Show current positions and orders from broker
- Show what changed during crash
- Require user to click "Resume Trading" button
- Log manual approval in audit trail

**Critical Safety Feature**:
- **Always place stop-loss orders at broker level**, not just in-app tracking
- If app crashes, broker still executes stop-losses automatically
- This is the primary safety net against catastrophic losses

**Security for API Keys & Credentials**:

**Multi-Layer Security Approach**:

**Layer 1: Environment Variables (Development)**

**Setup**:
```bash
# .env (NEVER commit to git - add to .gitignore)
TWELVE_DATA_API_KEY=your_key_here
IBKR_USERNAME=your_username
IBKR_PASSWORD=your_password
DATABASE_URL=postgresql://user:password@localhost/trading_db
SECRET_KEY=your_secret_key_for_jwt

# Email settings
SMTP_PASSWORD=your_email_password

# Broker settings
IBKR_ACCOUNT_ID=your_account_id
```

**Load in Application**:
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    twelve_data_api_key: str
    ibkr_username: str
    ibkr_password: str
    database_url: str
    secret_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**Critical Requirements**:
- **MUST** add `.env` to `.gitignore` before first commit
- Never log sensitive values
- Use separate .env files per environment (.env.dev, .env.prod)
- File permissions: `chmod 600 .env` (owner read/write only)

**Layer 2: Secrets Manager (Production - VPS/Cloud)**

**Recommended Options**:

**Option A: Docker Secrets** (If using Docker):
```yaml
# docker-compose.yml
services:
  trading-app:
    image: trading-bot:latest
    secrets:
      - ibkr_password
      - twelve_data_api_key
    environment:
      IBKR_USERNAME: ${IBKR_USERNAME}
      DATABASE_URL: ${DATABASE_URL}

secrets:
  ibkr_password:
    file: ./secrets/ibkr_password.txt
  twelve_data_api_key:
    file: ./secrets/twelve_data_api_key.txt
```

**Option B: HashiCorp Vault** (Self-hosted):
- Industry standard secrets management
- Encryption at rest and in transit
- Access control and audit logs
- API-based secret retrieval
- Free and open source

**Option C: Cloud Provider Secrets** (If using AWS/GCP):
- AWS Secrets Manager
- GCP Secret Manager
- Azure Key Vault
- Encrypted, rotatable, auditable

**Layer 3: Additional Security Measures**

**Database Security**:
- Create dedicated database user with minimal permissions
- Only grant needed permissions (SELECT, INSERT, UPDATE on specific tables)
- Don't use root/admin/postgres accounts
- Enable SSL/TLS for database connections

**API Key Management**:
- Rotate API keys every 90 days
- Support multiple keys during rotation (old + new)
- Log when keys are accessed (not the key values)
- Alert on unusual API usage patterns

**Access Control**:
- Don't run application as root user
- Create dedicated system user for trading bot
- Restrict file permissions (`.env` = 600, code = 644)
- Use SSH keys for VPS access (disable password auth)

**Encryption**:
- HTTPS for all external API calls
- SSL/TLS for database connections
- Consider encrypting sensitive DB fields (passwords, API keys)
- Use secure WebSocket connections (wss://)

**Audit Logging**:
- Log all API key usage (timestamp, endpoint, success/failure)
- Log authentication attempts
- Log when secrets are accessed
- Alert on suspicious patterns (multiple failures, unusual times)

**Secure Configuration Loading**:
```python
# backend/app/core/security.py
class SecureConfig:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._secrets_cache = {}

    def get_secret(self, key: str) -> str:
        """Safely retrieve secret"""
        if key in self._secrets_cache:
            return self._secrets_cache[key]

        value = os.getenv(key)
        if not value:
            self.logger.error(f"Secret {key} not found")
            raise ValueError(f"Missing required secret: {key}")

        self._secrets_cache[key] = value

        # Log access without revealing value
        self.logger.info(f"Loaded secret: {key} (length: {len(value)})")

        return value

    def validate_secrets(self):
        """Ensure all required secrets are present on startup"""
        required = [
            'TWELVE_DATA_API_KEY',
            'IBKR_USERNAME',
            'IBKR_PASSWORD',
            'DATABASE_URL',
            'SECRET_KEY'
        ]

        missing = [s for s in required if not os.getenv(s)]

        if missing:
            raise ValueError(f"Missing secrets: {', '.join(missing)}")
```

**Security Anti-Patterns** (Never do these):
```python
# NEVER hardcode secrets
api_key = "abc123def456"  # NEVER!

# NEVER log secrets
logger.info(f"API Key: {api_key}")  # NEVER!

# NEVER commit .env files to git
# Always add to .gitignore before first commit

# NEVER include secrets in error messages
raise Exception(f"API failed with key {api_key}")  # NEVER!

# NEVER store secrets in code or config files
config = {"api_key": "secret123"}  # NEVER!
```

**Security Checklist**:
```
✓ .env file added to .gitignore
✓ Separate .env for dev/staging/prod environments
✓ API keys stored in env variables (never in code)
✓ Database credentials stored securely
✓ File permissions restricted (chmod 600 .env)
✓ Secrets never appear in logs or error messages
✓ HTTPS/SSL for all external communication
✓ Dedicated non-root user for application
✓ API key rotation policy established (90 days)
✓ Audit logging enabled for secret access
✓ Database connections use SSL/TLS
✓ SSH key authentication for VPS (password auth disabled)
```

**User Management**:

**Single-User Application** (MVP):
- **Decision**: Single-user for MVP (no authentication needed)
- Simple: No login, no user management
- Application assumes single trader
- Access control via network (localhost or VPN)
- Sufficient for personal trading

**Multi-User Considerations** (Future - Phase 3+):
- If sharing with others or managing multiple accounts
- Implement authentication (JWT tokens)
- Role-based access control (admin, trader, viewer)
- Per-user strategy configurations
- Audit trail per user

**Key Principles**:
- Security is not optional - it's foundational
- Defense in depth: multiple security layers
- Never trust, always verify (especially after crashes)
- Broker is source of truth for positions
- Recovery safety > speed (pause for manual approval)

### Strategy Learning & Improvement System

**Goal**: Enable continuous strategy improvement through comprehensive data collection and analysis

**Phase 1 - Data Collection (MVP - Implement Immediately)**:

**Trade-Level Data**:

- Entry/exit timestamps, prices, quantities
- Entry/exit reasons (which signal triggered)
- Commission costs and slippage
- Intended vs actual execution prices
- Position hold duration
- P&L (absolute and percentage)
- Max adverse excursion (worst drawdown during trade)
- Max favorable excursion (best profit during trade)
- Stop-loss and take-profit levels (initial and any adjustments)

**Market Context Data** (at time of trade):

- Current indicator values (all indicators used by strategy)
- Market conditions (volatility, volume vs average, trend direction)
- Time of day/week
- Gap up/down from previous close
- Recent price action (was it trending, ranging, breaking out?)

**Strategy Performance Metrics** (daily aggregation):

- Total P&L for the day
- Win rate
- Number of trades
- Average win/loss
- Maximum drawdown
- Sharpe ratio (risk-adjusted returns)
- Portfolio value over time (equity curve)

**Strategy Execution Data**:

- Signal generation events (even if no trade taken - why not?)
- Missed opportunities (signal generated but order failed)
- Rejected trades (why was trade rejected by risk management?)
- Order failures (API errors, insufficient funds, etc.)

**Database Design Principle**:
Store raw data with high granularity. Aggregations and analysis can be computed later. Never lose detail.

**Phase 2 - Analysis Dashboards (End of MVP or Post-MVP)**:

**Dashboard 1: Strategy Overview**

- Equity curve (portfolio value over time)
- Total return, win rate, Sharpe ratio
- Current positions and their P&L
- Recent trades table
- Active orders

**Dashboard 2: Performance Analysis**

- Performance by day of week
- Performance by time of day (for intraday strategies)
- Performance by volatility regime (low/medium/high)
- Performance by market trend (bull/bear/sideways)
- Win rate by hold duration
- P&L distribution histogram

**Dashboard 3: Trade Analysis**

- Winning trades: What did they have in common?
- Losing trades: What patterns emerge?
- Average P&L by indicator conditions
- Trade timing analysis (how long from signal to execution?)
- Slippage analysis (intended vs actual prices)

**Dashboard 4: Risk Analysis**

- Drawdown periods (when and why?)
- Consecutive losses (longest losing streaks)
- Max adverse excursion analysis (where should stop-loss be?)
- Position sizing effectiveness
- Risk/reward ratio by trade type

**Dashboard 5: Strategy Comparison**

- Side-by-side comparison of multiple strategies
- Which strategy performs best in which conditions?
- Portfolio correlation (do strategies complement each other?)
- Combined portfolio metrics

**Manual Improvement Process**:

1. Review dashboards monthly (or after 20+ trades)
2. Identify patterns in losing trades
3. Hypothesize improvements (new filters, adjusted parameters)
4. Backtest proposed changes
5. If backtest shows improvement, paper trade updated strategy
6. If paper trading validates improvement, deploy to production
7. Document what was changed and why

**Key Insight**: The goal is not to "automate" learning but to make pattern identification easy so YOU can make informed decisions about strategy improvements.

## Strategy Ideas

### Phase 1: MVP Strategy

**Strategy 1: Moving Average Crossover with RSI Confirmation**

**Type**: Trend-following with momentum confirmation

**Indicators**:
- EMA(20) - Fast moving average
- EMA(50) - Slow moving average
- RSI(14) - Relative Strength Index

**Entry Rules**:
- EMA(20) crosses above EMA(50) (bullish crossover)
- AND RSI < 70 (not overbought)
- AND position sizing follows 2% risk rule

**Exit Rules**:
- EMA(20) crosses below EMA(50) (bearish crossover)
- OR RSI > 70 (overbought condition)
- OR stop-loss triggered (5% below entry)
- OR take-profit triggered (15% above entry)

**Position Type**: Long only

**Timeframe**: Daily bars (end-of-day signals)

**Target Assets**: Large-cap stocks (S&P 500 constituents)

**Expected Characteristics**:
- Win rate: 40-50% (typical for trend-following)
- Risk/reward: 1:3 (risking 5%, targeting 15%)
- Holding period: Days to weeks

### Phase 2: Additional Strategies (Future)

**Strategy 2: RSI Mean Reversion**
- Buy when RSI < 30 (oversold)
- Sell when RSI > 50 (return to neutral)
- Best for range-bound markets

**Strategy 3: Bollinger Band Breakout**
- Buy on breakout above upper band with high volume
- Momentum strategy for trending markets
- Requires volume confirmation

**Strategy 4: MACD + Volume Divergence**
- MACD histogram crossover signals
- Volume confirms momentum
- Catches trend reversals early

**Strategy 5: Multi-Timeframe Confirmation**
- Align daily and weekly trends
- Higher success rate but fewer signals
- More sophisticated risk management

## Performance Metrics to Track

(To be defined based on trading goals)

## Future Enhancements

(Ideas for future iterations)
