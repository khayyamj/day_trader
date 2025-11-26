# Trading Bot User Manual

Complete guide for using the Trading Bot application.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Dashboard](#dashboard)
- [Strategy Management](#strategy-management)
- [Risk Management](#risk-management)
- [Trade Monitoring](#trade-monitoring)
- [Backtesting](#backtesting)
- [Alerts and Notifications](#alerts-and-notifications)
- [Best Practices](#best-practices)

## Overview

The Trading Bot is an automated trading system that executes trades based on technical indicators (MACD and RSI). It monitors stocks in your watchlist, generates trading signals, manages risk, and executes trades through Interactive Brokers.

### Key Features

- **Automated Trading**: Execute trades based on MACD/RSI signals
- **Real-time Monitoring**: Track positions and market data live
- **Risk Management**: Automatic position sizing and loss limits
- **Backtesting**: Test strategies on historical data
- **Email Notifications**: Get alerts for trades and system events
- **Daily Summaries**: Receive end-of-day trading reports
- **Crash Recovery**: Automatic position reconciliation on restart

## Getting Started

### Initial Setup

1. **Configure Environment**
   - Set up your `.env` file with IBKR credentials
   - Configure email settings for notifications
   - Add your Twelve Data API key

2. **Add Stocks to Watchlist**
   ```bash
   curl -X POST http://localhost:8000/api/stocks \
     -H "Content-Type: application/json" \
     -d '{"symbol": "AAPL", "name": "Apple Inc."}'
   ```

3. **Start IBKR TWS/Gateway**
   - Launch TWS or IB Gateway
   - Enable API connections (Configure > API > Settings)
   - Note the port (7497 for paper, 7496 for live)

4. **Start the Application**
   ```bash
   sudo systemctl start trading-bot
   ```

### First Trade

The system automatically:
1. Fetches market data every 30 seconds
2. Calculates MACD and RSI indicators
3. Generates BUY/SELL signals
4. Evaluates risk rules
5. Executes approved trades
6. Sends notification emails

## Dashboard

### Overview Page

Access the dashboard at `http://localhost:3000`

The main dashboard shows:
- **Portfolio Summary**: Total value, cash, positions
- **Open Positions**: Current trades with P&L
- **Recent Signals**: Latest buy/sell opportunities
- **Performance Metrics**: Win rate, total P&L, trade count

### Real-time Updates

The dashboard updates automatically via WebSocket connection:
- Price updates every 30 seconds
- Trade executions appear immediately
- Signal notifications in real-time

### Key Metrics

- **Total P&L**: Realized + Unrealized profit/loss
- **Win Rate**: Percentage of profitable trades
- **Open Positions**: Number of active trades
- **Daily P&L**: Today's trading performance

## Strategy Management

### View Active Strategies

```bash
curl http://localhost:8000/api/strategies
```

### Strategy Parameters

Each strategy has configurable parameters:

#### MACD Settings
- **Fast Period**: 12 (default)
- **Slow Period**: 26 (default)
- **Signal Period**: 9 (default)

#### RSI Settings
- **Period**: 14 (default)
- **Overbought**: 70 (default)
- **Oversold**: 30 (default)

### Enable/Disable Strategy

```bash
# Activate strategy
curl -X PUT http://localhost:8000/api/strategies/1/activate

# Pause strategy
curl -X PUT http://localhost:8000/api/strategies/1/pause
```

### Signal Generation Logic

**BUY Signal** generated when:
- MACD line crosses above signal line
- RSI is below 70 (not overbought)
- No open position for this stock

**SELL Signal** generated when:
- MACD line crosses below signal line
- OR RSI exceeds 70 (overbought)
- Open position exists for this stock

## Risk Management

### Position Sizing

The system automatically calculates position size based on:
- **Account Balance**: Available cash
- **Risk Per Trade**: Default 2% of account
- **Stock Price**: Current market price

```
Position Size = (Account Balance × Risk %) / Stock Price
```

### Risk Rules

Trades are rejected if they violate:

1. **Daily Loss Limit**: Stop trading if daily loss exceeds threshold
2. **Position Limit**: Maximum number of simultaneous positions
3. **Concentration Limit**: Maximum % of portfolio in one stock
4. **Order Size Limit**: Maximum shares per order

### Viewing Risk Settings

```bash
curl http://localhost:8000/api/strategies/1
```

Look for `risk_params` section with:
- `max_position_size`: Maximum shares per trade
- `stop_loss_pct`: Stop-loss percentage
- `take_profit_pct`: Take-profit percentage
- `max_daily_loss`: Daily loss limit in dollars

### Adjusting Risk Parameters

Contact system administrator or update strategy configuration directly.

## Trade Monitoring

### View Open Positions

```bash
curl http://localhost:8000/api/trades?status=OPEN
```

### View Trade History

```bash
# All trades
curl http://localhost:8000/api/trades

# Today's trades
curl "http://localhost:8000/api/trades?date=$(date +%Y-%m-%d)"
```

### Trade Details

Each trade includes:
- **Entry Price**: Price at which position was opened
- **Current Price**: Live market price
- **Quantity**: Number of shares
- **Unrealized P&L**: Current profit/loss
- **Duration**: Time position has been open
- **Strategy**: Which strategy generated the trade

### Manual Trade Exit

Trades are automatically exited when:
- SELL signal generated
- Stop-loss hit
- Take-profit target reached

To manually close a position, use the API or contact administrator.

## Backtesting

### Run a Backtest

```bash
curl -X POST http://localhost:8000/api/backtests \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 1,
    "symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000
  }'
```

### View Backtest Results

```bash
curl http://localhost:8000/api/backtests/1
```

Results include:
- **Total Return**: Overall percentage gain/loss
- **Sharpe Ratio**: Risk-adjusted return
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of winning trades
- **Trade Count**: Total number of trades
- **Equity Curve**: Historical portfolio value

### Interpreting Results

- **Sharpe Ratio > 1**: Good risk-adjusted returns
- **Max Drawdown < 20%**: Acceptable risk level
- **Win Rate > 50%**: More winners than losers
- **Positive Total Return**: Strategy is profitable

## Alerts and Notifications

### Email Notifications

You'll receive emails for:

1. **Trade Executions**
   - Sent immediately when trade is executed
   - Includes symbol, action, price, quantity

2. **Risk Warnings**
   - Daily loss limit approaching
   - Position limit reached
   - Concentration risk alert

3. **System Errors**
   - Database connection failures
   - Broker API disconnects
   - Critical application errors

4. **Daily Summary** (4:30 PM ET)
   - Today's trades and P&L
   - Win rate and performance
   - Open positions
   - Tomorrow's watchlist

5. **Recovery Reports**
   - Sent on app restart after crash
   - Position reconciliation status
   - Discrepancies found

### Configuring Email Settings

Email settings are configured in `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
```

## Best Practices

### Pre-Market Checklist

Before market open:
1. ✅ Verify IBKR TWS/Gateway is running
2. ✅ Check system health: `curl http://localhost:8000/api/health`
3. ✅ Review watchlist stocks
4. ✅ Confirm risk settings are appropriate
5. ✅ Check available cash balance

### During Market Hours

1. **Monitor Dashboard**: Keep an eye on real-time updates
2. **Review Signals**: Check new signals before they execute
3. **Watch Email**: Stay alert for notification emails
4. **Check Positions**: Monitor open positions regularly

### Post-Market Review

1. **Review Daily Summary Email**: Sent at 4:30 PM ET
2. **Analyze Performance**: Check win rate and P&L
3. **Adjust Strategy**: Modify parameters if needed
4. **Plan Tomorrow**: Review tomorrow's watchlist

### Risk Management Tips

1. **Start Small**: Begin with small position sizes
2. **Use Paper Trading**: Test strategies before going live
3. **Diversify**: Trade multiple uncorrelated stocks
4. **Set Limits**: Configure daily loss limits
5. **Monitor Closely**: Don't rely solely on automation
6. **Keep Cash Reserve**: Maintain adequate cash balance
7. **Review Regularly**: Check performance weekly

### System Maintenance

1. **Daily**: Check health endpoint and review logs
2. **Weekly**: Review trade performance and adjust strategies
3. **Monthly**: Analyze backtest results, update watchlist
4. **Quarterly**: Review and optimize risk parameters

### Troubleshooting Checklist

If trades aren't executing:
1. ✅ Is IBKR TWS/Gateway running?
2. ✅ Is strategy active?
3. ✅ Are there valid signals?
4. ✅ Do signals pass risk checks?
5. ✅ Is there sufficient cash?
6. ✅ Check application logs for errors

## Data and Privacy

### Data Storage

The system stores:
- Trade history
- Market data (prices, indicators)
- Strategy configurations
- System events and logs

### Data Retention

- **Trade Data**: Kept indefinitely
- **Market Data**: 90 days
- **System Logs**: 30 days
- **Events**: 90 days

### Backup

Regular database backups are automated daily at 2 AM. Backups are retained for 30 days.

## Support and Resources

### Documentation

- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **API Documentation**: `http://localhost:8000/docs`

### Health Monitoring

- **Overall Health**: `GET /api/health`
- **Detailed Metrics**: `GET /api/health/detailed`
- **Component Status**: Individual endpoints for DB, broker, scheduler

### Logs

```bash
# Application logs
tail -f /var/log/trading-bot/app.log

# Error logs
tail -f /var/log/trading-bot/error.log

# systemd logs
sudo journalctl -u trading-bot -f
```

### Getting Help

For support:
- Check `docs/TROUBLESHOOTING.md` first
- Review application logs
- Contact system administrator
- GitHub Issues: https://github.com/yourusername/trading-bot/issues

## Legal Disclaimer

This trading bot is provided for educational and informational purposes only. Trading stocks involves substantial risk of loss. Past performance is not indicative of future results. Use at your own risk. The developers are not responsible for any financial losses incurred while using this software.
